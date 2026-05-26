"""Diagnostic: scan a multi-ball video and print the bat-confidence + pose-motion
signal across time so we can see where each ball lives.

Output goes to scripts/diag_multi_stroke.csv plus a text summary on stdout.

Usage:
    python scripts/diag_multi_stroke.py "C:\\Users\\KARTHIKK\\Downloads\\vid\\6shots.mp4"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HF_DIR = PROJECT_ROOT.parent / "hf-space-cricket"
POSE_WEIGHTS = HF_DIR / "shot_classifier" / "weights" / "yolov8n-pose.pt"
BAT_WEIGHTS = HF_DIR / "shot_classifier" / "weights" / "bat.pt"

# Sampling density: ~6 samples / sec → 17s video = ~100 samples.
# Enough resolution to resolve peaks ~2s apart.
SAMPLE_HZ = 6.0
YOLO_IMGSZ = 320


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, default=PROJECT_ROOT / "scripts" / "diag_multi_stroke.csv")
    args = ap.parse_args()

    if not args.video.exists():
        sys.exit(f"Video not found: {args.video}")
    if not POSE_WEIGHTS.exists() or not BAT_WEIGHTS.exists():
        sys.exit(f"Weights missing in {POSE_WEIGHTS.parent}")

    print(f"Loading YOLO models...", flush=True)
    from ultralytics import YOLO
    pose_model = YOLO(str(POSE_WEIGHTS))
    bat_model = YOLO(str(BAT_WEIGHTS))

    cap = cv2.VideoCapture(str(args.video))
    fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video: {duration:.2f}s, {total} frames, {fps:.1f} fps, {w}x{h}", flush=True)

    n_samples = max(20, int(duration * SAMPLE_HZ))
    sample_idxs = np.linspace(0, total - 1, n_samples).astype(int)
    print(f"Sampling {n_samples} frames at ~{SAMPLE_HZ:.1f} Hz", flush=True)

    rows = []
    prev_kp = None
    for i, fidx in enumerate(sample_idxs):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fidx))
        ok, frame = cap.read()
        if not ok:
            continue
        t_sec = fidx / fps

        # Bat detector
        bat_results = bat_model.predict(frame, imgsz=YOLO_IMGSZ, conf=0.10, verbose=False)
        bat_conf = 0.0
        bat_cx = bat_cy = None
        if len(bat_results) and bat_results[0].boxes is not None and len(bat_results[0].boxes) > 0:
            confs = bat_results[0].boxes.conf.cpu().numpy()
            boxes = bat_results[0].boxes.xyxy.cpu().numpy()
            best = int(np.argmax(confs))
            bat_conf = float(confs[best])
            x1, y1, x2, y2 = boxes[best]
            bat_cx, bat_cy = float((x1 + x2) / 2), float((y1 + y2) / 2)

        # Pose detector
        pose_results = pose_model.predict(frame, imgsz=YOLO_IMGSZ, conf=0.20, verbose=False)
        motion = 0.0
        person_count = 0
        biggest_kp = None
        if (
            len(pose_results)
            and pose_results[0].keypoints is not None
            and pose_results[0].keypoints.xy is not None
            and len(pose_results[0].keypoints.xy) > 0
        ):
            kp_all = pose_results[0].keypoints.xy.cpu().numpy()
            person_count = len(kp_all)
            # Pick the person with the largest bounding box (probably the batter
            # in a phone video at this distance).
            if pose_results[0].boxes is not None and len(pose_results[0].boxes) > 0:
                bx = pose_results[0].boxes.xyxy.cpu().numpy()
                areas = (bx[:, 2] - bx[:, 0]) * (bx[:, 3] - bx[:, 1])
                biggest = int(np.argmax(areas))
                biggest_kp = kp_all[biggest]
            else:
                biggest_kp = kp_all[0]
            if prev_kp is not None and biggest_kp.shape == prev_kp.shape:
                motion = float(np.linalg.norm(biggest_kp - prev_kp, axis=1).mean())
        prev_kp = biggest_kp

        row = {
            "i": i,
            "frame": int(fidx),
            "t_sec": round(t_sec, 3),
            "bat_conf": round(bat_conf, 3),
            "bat_cx": round(bat_cx, 1) if bat_cx else "",
            "bat_cy": round(bat_cy, 1) if bat_cy else "",
            "person_count": person_count,
            "motion_pix": round(motion, 2),
        }
        rows.append(row)
        if i % 10 == 0:
            print(
                f"  [{i:3d}/{n_samples}] t={t_sec:5.2f}s "
                f"bat={bat_conf:.2f}  motion={motion:6.1f}  persons={person_count}",
                flush=True,
            )

    cap.release()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        header = list(rows[0].keys())
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(str(r[k]) for k in header) + "\n")
    print(f"\nWrote {args.out}  ({len(rows)} rows)")

    # Find peaks: combined signal = bat_conf normalised + motion normalised
    bat_arr = np.array([r["bat_conf"] for r in rows], dtype=float)
    mot_arr = np.array([r["motion_pix"] for r in rows], dtype=float)
    bat_n = bat_arr / max(bat_arr.max(), 1e-6)
    mot_n = mot_arr / max(mot_arr.max(), 1e-6)
    combined = 0.6 * bat_n + 0.4 * mot_n

    # Simple peak picking: must be local max in a 1.0s window AND above threshold
    win = max(1, int(SAMPLE_HZ * 1.0))
    threshold = max(0.2, combined.mean() + 0.5 * combined.std())
    peaks = []
    for i in range(len(combined)):
        lo = max(0, i - win)
        hi = min(len(combined), i + win + 1)
        if combined[i] == max(combined[lo:hi]) and combined[i] >= threshold:
            peaks.append(i)
    print(f"\nDetected {len(peaks)} peak(s) at:")
    for p in peaks:
        print(
            f"  peak {p:3d}  t={rows[p]['t_sec']:5.2f}s  bat={rows[p]['bat_conf']:.2f}  "
            f"motion={rows[p]['motion_pix']:6.1f}  combined={combined[p]:.3f}"
        )

    # Print the raw curve so we can eyeball
    print("\n  i  t_sec  bat_conf  motion   |signal|")
    for i, r in enumerate(rows):
        bar_len = int(combined[i] * 40)
        bar = "#" * bar_len
        marker = "  <-- PEAK" if i in peaks else ""
        print(f"  {i:3d}  {r['t_sec']:5.2f}  {r['bat_conf']:.2f}     {r['motion_pix']:6.1f}  |{bar:<40}|{marker}")


if __name__ == "__main__":
    main()
