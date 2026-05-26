"""
Extract batsman pose sequences from clips using YOLO-Pose.

For each clip in data/clips/<class>/:
  - Run YOLO-Pose per frame.
  - Select the batsman from detected persons (largest bbox in lower-center).
  - Stack 17 COCO keypoints + per-keypoint confidence over time.
  - Normalize (center on hip midpoint, scale by torso length).
  - Resample to a fixed T=50 frames (2 sec at 25 fps).
  - Save as data/poses/<class>/<clip_stem>.npy with shape (T, 17, 3).

Handedness is NOT detected here. We rely on random horizontal-flip augmentation
during training to make the model handedness-invariant.

Usage:
    python scripts/extract_poses.py                    # all classes
    python scripts/extract_poses.py --class drive      # one class
    python scripts/extract_poses.py --device cuda      # if you have a GPU
"""

import argparse
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from tqdm import tqdm
    from ultralytics import YOLO
except ImportError as e:
    sys.exit(f"Missing dependency: {e}. Run: pip install -r requirements.txt")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIPS_DIR = PROJECT_ROOT / "data" / "clips"
POSES_DIR = PROJECT_ROOT / "data" / "poses"

CLASS_NAMES = [
    "Cover Drive",
    "Defensive", 
    "Down The Wicket",
    "Flick",
    "Hook",
    "Late Cut",
    "Lofted Legside",
    "Lofted Offside",
    "Pull",
    "Reverse Sweep",
    "Scoop",
    "Square Cut",
    "Straight Drive",
    "Sweep",
    "Upper Cut",
]
T_FRAMES = 50
N_KEYPOINTS = 17
# Lowered from 0.6 → 0.4 to recover cut/sweep clips where the batsman is
# partially obscured (close camera, side angles). The Transformer can still
# learn from sequences with zero-keypoint gaps as long as the stroke itself
# is captured. Boosted training set: cut 16→~80, sweep 16→~100 expected.
MIN_VISIBLE_FRACTION = 0.4

# COCO-17 keypoint indices used in normalization
L_SHOULDER, R_SHOULDER = 5, 6
L_HIP, R_HIP = 11, 12


def select_batsman(boxes: np.ndarray, kpt_conf: np.ndarray, img_w: int, img_h: int) -> int | None:
    """Pick the person most likely to be the batsman.

    Score = bbox_area * center_weight * lower_weight * mean_keypoint_conf.
    The batsman is usually the largest, lowest, most-central person in frame
    (camera is behind the bowler / square of the wicket).
    """
    if len(boxes) == 0:
        return None
    best_i, best_s = None, -1.0
    for i, (box, kc) in enumerate(zip(boxes, kpt_conf)):
        x1, y1, x2, y2 = box
        area = max(1.0, (x2 - x1) * (y2 - y1))
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        center_w = max(0.1, 1.0 - abs(cx / img_w - 0.5) * 1.5)
        lower_w = max(0.1, cy / img_h)
        conf_w = float(kc.mean()) if kc.size else 0.0
        s = area * center_w * lower_w * conf_w
        if s > best_s:
            best_s, best_i = s, i
    return best_i


def normalize(seq: np.ndarray) -> np.ndarray:
    """Center on hip midpoint, scale by torso length. Confidence kept untouched."""
    hip_mid = (seq[:, L_HIP, :2] + seq[:, R_HIP, :2]) / 2.0       # (T, 2)
    sh_mid = (seq[:, L_SHOULDER, :2] + seq[:, R_SHOULDER, :2]) / 2.0
    torso = np.linalg.norm(sh_mid - hip_mid, axis=1, keepdims=True)  # (T, 1)
    torso = np.clip(torso, 1e-3, None)
    out = seq.copy()
    out[:, :, :2] = (seq[:, :, :2] - hip_mid[:, None, :]) / torso[:, None, :]
    return out


def resample_t(seq: np.ndarray, T: int) -> np.ndarray:
    if len(seq) == T:
        return seq
    idx = np.linspace(0, len(seq) - 1, T).astype(int)
    return seq[idx]


def extract_clip(clip_path: Path, model) -> np.ndarray | None:
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        return None
    img_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    img_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    seq: list[np.ndarray] = []
    misses = 0
    total = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        total += 1
        res = model(frame, verbose=False)[0]
        if res.keypoints is None or res.keypoints.xy is None or len(res.boxes) == 0:
            misses += 1
            seq.append(np.zeros((N_KEYPOINTS, 3), dtype=np.float32))
            continue
        boxes = res.boxes.xyxy.cpu().numpy()
        kxy = res.keypoints.xy.cpu().numpy()
        kconf = (res.keypoints.conf.cpu().numpy()
                 if res.keypoints.conf is not None
                 else np.ones((len(boxes), N_KEYPOINTS), dtype=np.float32))
        bi = select_batsman(boxes, kconf, img_w, img_h)
        if bi is None:
            misses += 1
            seq.append(np.zeros((N_KEYPOINTS, 3), dtype=np.float32))
            continue
        frame_kp = np.concatenate([kxy[bi], kconf[bi][:, None]], axis=1)  # (17, 3)
        seq.append(frame_kp.astype(np.float32))
    cap.release()

    if total == 0:
        return None
    visible_frac = 1.0 - misses / total
    if visible_frac < MIN_VISIBLE_FRACTION:
        return None  # too many failed detections

    arr = np.stack(seq, axis=0)
    arr = resample_t(arr, T_FRAMES)
    arr = normalize(arr)
    return arr.astype(np.float32)


def process_class(cls: str, model, overwrite: bool) -> tuple[int, int]:
    src = CLIPS_DIR / cls
    dst = POSES_DIR / cls
    clips = []
    if src.exists():
        # search recursively for common video file extensions (handles nested folders)
        exts = ("*.mp4", "*.avi", "*.mov", "*.mkv")
        files = []
        for e in exts:
            files.extend(list(src.rglob(e)))
        clips = sorted(files)
    if not clips:
        return 0, 0
    dst.mkdir(parents=True, exist_ok=True)
    kept = skipped = 0
    for clip in tqdm(clips, desc=cls, ncols=80):
        out = dst / (clip.stem + ".npy")
        if out.exists() and not overwrite:
            kept += 1
            continue
        seq = extract_clip(clip, model)
        if seq is None:
            skipped += 1
            continue
        np.save(out, seq)
        kept += 1
    return kept, skipped


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--class", dest="cls", help="Only this class")
    ap.add_argument("--model", default="yolov8n-pose.pt",
                    help="YOLO-Pose weights (auto-downloaded on first run)")
    ap.add_argument("--device", default=None, help="cuda, cpu, or omit for auto")
    ap.add_argument("--overwrite", action="store_true", help="Re-extract existing .npy files")
    args = ap.parse_args()

    classes = [args.cls] if args.cls else CLASS_NAMES
    print(f"Loading {args.model} (auto-downloads on first run)...")
    model = YOLO(args.model)
    if args.device:
        model.to(args.device)

    totals = {"kept": 0, "skipped": 0}
    for cls in classes:
        kept, skipped = process_class(cls, model, args.overwrite)
        totals["kept"] += kept
        totals["skipped"] += skipped
        if kept or skipped:
            print(f"  {cls}: kept={kept} skipped={skipped}")

    print(f"\nDone. Total kept={totals['kept']} skipped={totals['skipped']}")
    print(f"Output: {POSES_DIR}")


if __name__ == "__main__":
    main()
