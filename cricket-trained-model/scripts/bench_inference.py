"""Benchmark the cricket-shot inference pipeline end-to-end.

Decomposes total prediction time into:
  - model loading (YOLO-Pose + PoseTransformer)
  - video I/O (frame decode)
  - YOLO-Pose forward per frame
  - batsman selection + pose normalization + temporal resample
  - PoseTransformer forward
  - coaching feedback computation

Reports per-run timings, averages over N runs, and identifies the bottleneck.

Usage:
    python scripts/bench_inference.py "cover-drive .mp4" --runs 3
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
import tracemalloc
from contextlib import contextmanager
from pathlib import Path
from statistics import mean, stdev

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from model import PoseTransformer  # noqa: E402
from coach import generate_coaching_feedback  # noqa: E402
from extract_poses import (  # noqa: E402
    N_KEYPOINTS,
    T_FRAMES,
    MIN_VISIBLE_FRACTION,
    normalize,
    resample_t,
    select_batsman,
)

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402


@contextmanager
def timed(store: dict, key: str):
    t0 = time.perf_counter()
    yield
    store[key] = time.perf_counter() - t0


def load_classifier(ckpt_path: Path, device: torch.device):
    t0 = time.perf_counter()
    try:
        ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(str(ckpt_path), map_location=device)
    state_dict = ckpt["state_dict"]
    class_index = ckpt["class_index"]
    in_proj_key = next((k for k in state_dict if k.endswith("in_proj.weight")), None)
    in_dim = state_dict[in_proj_key].shape[1] if in_proj_key else 51
    model = PoseTransformer(num_classes=len(class_index), in_dim=int(in_dim)).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    elapsed = time.perf_counter() - t0
    id_to_name = {v: k for k, v in class_index.items()}
    return model, id_to_name, elapsed


def extract_clip_timed(video_path: Path, pose_model, stats: dict):
    """Same as extract_poses.extract_clip but records per-stage timing."""
    cap_t0 = time.perf_counter()
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    img_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    img_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    n_frames_meta = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stats["video_meta"] = {"w": img_w, "h": img_h, "fps": fps, "frames": n_frames_meta}

    seq: list[np.ndarray] = []
    misses = 0
    total = 0
    pose_total = 0.0
    decode_total = 0.0
    select_total = 0.0

    while True:
        d0 = time.perf_counter()
        ok, frame = cap.read()
        decode_total += time.perf_counter() - d0
        if not ok:
            break
        total += 1
        p0 = time.perf_counter()
        res = pose_model(frame, verbose=False)[0]
        pose_total += time.perf_counter() - p0

        if res.keypoints is None or res.keypoints.xy is None or len(res.boxes) == 0:
            misses += 1
            seq.append(np.zeros((N_KEYPOINTS, 3), dtype=np.float32))
            continue
        s0 = time.perf_counter()
        boxes = res.boxes.xyxy.cpu().numpy()
        kxy = res.keypoints.xy.cpu().numpy()
        kconf = (
            res.keypoints.conf.cpu().numpy()
            if res.keypoints.conf is not None
            else np.ones((len(boxes), N_KEYPOINTS), dtype=np.float32)
        )
        bi = select_batsman(boxes, kconf, img_w, img_h)
        select_total += time.perf_counter() - s0
        if bi is None:
            misses += 1
            seq.append(np.zeros((N_KEYPOINTS, 3), dtype=np.float32))
            continue
        frame_kp = np.concatenate([kxy[bi], kconf[bi][:, None]], axis=1)
        seq.append(frame_kp.astype(np.float32))
    cap.release()

    stats["pose_yolo_total_s"] = pose_total
    stats["frame_decode_total_s"] = decode_total
    stats["batsman_select_total_s"] = select_total
    stats["frames_processed"] = total
    stats["frames_missed"] = misses
    stats["per_frame_pose_ms"] = (pose_total / max(total, 1)) * 1000.0
    stats["per_frame_decode_ms"] = (decode_total / max(total, 1)) * 1000.0
    stats["extract_open_to_close_s"] = time.perf_counter() - cap_t0

    if total == 0:
        return None
    visible_frac = 1.0 - misses / total
    stats["visible_fraction"] = visible_frac
    if visible_frac < MIN_VISIBLE_FRACTION:
        return None

    norm_t0 = time.perf_counter()
    arr = np.stack(seq, axis=0)
    arr = resample_t(arr, T_FRAMES)
    arr = normalize(arr)
    stats["normalize_resample_s"] = time.perf_counter() - norm_t0
    return arr.astype(np.float32)


def run_once(video: Path, pose_model, classifier, id_to_name, device) -> dict:
    stats: dict = {}
    with timed(stats, "extract_total_s"):
        seq = extract_clip_timed(video, pose_model, stats)
    if seq is None:
        stats["error"] = "pose_extraction_failed"
        return stats

    with timed(stats, "classifier_forward_s"):
        x = torch.from_numpy(seq.reshape(seq.shape[0], -1)).unsqueeze(0).to(device)
        expected_in = classifier.in_proj.in_features
        if x.size(-1) < expected_in:
            pad = torch.zeros(x.size(0), x.size(1), expected_in - x.size(-1), device=x.device)
            x = torch.cat([x, pad], dim=-1)
        elif x.size(-1) > expected_in:
            x = x[:, :, :expected_in]
        with torch.no_grad():
            logits = classifier(x)
            probs = logits.softmax(-1).squeeze(0).cpu().numpy()

    top = int(np.argmax(probs))
    with timed(stats, "coach_feedback_s"):
        _ = generate_coaching_feedback(seq, id_to_name[top], probs, id_to_name)

    stats["top_class"] = id_to_name[top]
    stats["top_prob"] = float(probs[top])
    return stats


def fmt_ms(s: float) -> str:
    return f"{s * 1000.0:.1f} ms"


def summarize(runs: list[dict]) -> dict:
    keys = [
        "extract_total_s",
        "pose_yolo_total_s",
        "frame_decode_total_s",
        "batsman_select_total_s",
        "normalize_resample_s",
        "classifier_forward_s",
        "coach_feedback_s",
        "per_frame_pose_ms",
        "per_frame_decode_ms",
    ]
    out: dict = {}
    for k in keys:
        vals = [r[k] for r in runs if k in r]
        if vals:
            out[k] = {
                "mean": mean(vals),
                "std": stdev(vals) if len(vals) > 1 else 0.0,
                "min": min(vals),
                "max": max(vals),
            }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", help="Video file to benchmark")
    ap.add_argument("--ckpt", default=str(PROJECT_ROOT / "runs" / "exp1" / "best.pt"))
    ap.add_argument("--pose-model", default=str(PROJECT_ROOT / "yolov8n-pose.pt"))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=None, help="Write JSON results to this path")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        sys.exit(f"Video not found: {video}")

    device = torch.device(args.device)

    print("=" * 70)
    print("CRICKET SHOT INFERENCE BENCHMARK")
    print("=" * 70)
    print(f"Video       : {video.name}")
    print(f"Device      : {device}")
    print(f"Runs        : {args.runs}")
    print(f"Torch       : {torch.__version__}  threads={torch.get_num_threads()}")
    print()

    # ------- model load -------
    tracemalloc.start()
    yolo_t0 = time.perf_counter()
    pose_model = YOLO(args.pose_model)
    pose_model.to(str(device))
    yolo_load_s = time.perf_counter() - yolo_t0

    classifier, id_to_name, cls_load_s = load_classifier(Path(args.ckpt), device)
    snapshot, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    n_params = sum(p.numel() for p in classifier.parameters())
    ckpt_bytes = Path(args.ckpt).stat().st_size
    pose_bytes = Path(args.pose_model).stat().st_size

    print("MODEL LOAD")
    print(f"  YOLO-Pose load         : {yolo_load_s:.2f} s   ({pose_bytes / 1e6:.1f} MB on disk)")
    print(f"  PoseTransformer load   : {cls_load_s:.3f} s  ({ckpt_bytes / 1e3:.1f} KB on disk, {n_params:,} params)")
    print(f"  Peak tracemalloc       : {peak / 1e6:.1f} MB during model load (Python objects only)")
    print()

    # ------- runs -------
    runs: list[dict] = []
    for i in range(args.runs):
        gc.collect()
        r = run_once(video, pose_model, classifier, id_to_name, device)
        runs.append(r)
        if "error" in r:
            print(f"RUN {i + 1}: FAILED ({r['error']})")
            continue
        print(
            f"RUN {i + 1}: top={r['top_class']:<14s} prob={r['top_prob']:.3f}  "
            f"end_to_end={r['extract_total_s'] + r['classifier_forward_s'] + r['coach_feedback_s']:.2f}s"
        )

    # ------- summary -------
    succ = [r for r in runs if "error" not in r]
    if not succ:
        sys.exit("All runs failed")

    s = summarize(succ)

    print()
    print("PER-STAGE TIMING (averaged across runs)")
    print("-" * 70)
    print(f"  {'stage':<32s} {'mean':>10s} {'std':>10s} {'min':>10s} {'max':>10s}")
    stage_labels = [
        ("pose_yolo_total_s", "YOLO-Pose total"),
        ("frame_decode_total_s", "Frame decode (cv2)"),
        ("batsman_select_total_s", "Batsman selection"),
        ("normalize_resample_s", "Normalize + resample"),
        ("extract_total_s", "  -> Extract total (sum of above)"),
        ("classifier_forward_s", "PoseTransformer forward"),
        ("coach_feedback_s", "Coaching feedback"),
    ]
    for key, label in stage_labels:
        if key in s:
            v = s[key]
            print(
                f"  {label:<32s} {fmt_ms(v['mean']):>10s} {fmt_ms(v['std']):>10s} "
                f"{fmt_ms(v['min']):>10s} {fmt_ms(v['max']):>10s}"
            )

    print()
    print("PER-FRAME TIMING")
    print(f"  YOLO-Pose / frame      : {s['per_frame_pose_ms']['mean']:.1f} ms")
    print(f"  Decode / frame         : {s['per_frame_decode_ms']['mean']:.2f} ms")

    fp = succ[0].get("frames_processed", 0)
    visible = succ[0].get("visible_fraction", 0.0)
    meta = succ[0].get("video_meta", {})
    if meta:
        print()
        print("INPUT")
        print(f"  Resolution             : {meta['w']}x{meta['h']}")
        print(f"  Frame rate (decoded)   : {meta['fps']:.1f} fps")
        print(f"  Frames processed       : {fp}")
        print(f"  Visible fraction       : {visible:.2f}")

    total_mean = (
        s.get("extract_total_s", {}).get("mean", 0.0)
        + s.get("classifier_forward_s", {}).get("mean", 0.0)
        + s.get("coach_feedback_s", {}).get("mean", 0.0)
    )
    if total_mean > 0:
        pose_pct = s.get("pose_yolo_total_s", {}).get("mean", 0.0) / total_mean * 100
        cls_pct = s.get("classifier_forward_s", {}).get("mean", 0.0) / total_mean * 100
        print()
        print("BOTTLENECK")
        print(f"  End-to-end mean         : {total_mean:.2f} s")
        print(f"  YOLO-Pose share         : {pose_pct:.1f}%")
        print(f"  PoseTransformer share   : {cls_pct:.1f}%  ({fmt_ms(s['classifier_forward_s']['mean'])})")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "video": str(video),
            "device": str(device),
            "runs": runs,
            "summary": s,
            "model": {
                "yolo_load_s": yolo_load_s,
                "classifier_load_s": cls_load_s,
                "classifier_params": n_params,
                "classifier_ckpt_bytes": ckpt_bytes,
                "pose_model_bytes": pose_bytes,
            },
        }, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
