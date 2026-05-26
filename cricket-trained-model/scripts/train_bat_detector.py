"""Train a YOLOv8 cricket-bat detector on the Roboflow dataset.

Dataset: C:\\Users\\KARTHIKK\\Downloads\\Cricket Bat detection.v1i.yolov8
- 2475 train / 236 val / 118 test images
- Classes: ['-', 'bat']  (class 0 is a placeholder, class 1 is the bat)
- License: Public Domain

Run with:
    .\\.venv\\Scripts\\activate.bat
    python scripts\\train_bat_detector.py

Output:
    runs/bat_detector/weights/best.pt  ← this is the file we ship to HF Space
    runs/bat_detector/results.png      ← training curves
    runs/bat_detector/confusion_matrix.png

Expected time: ~1.5-2 hours on a typical CPU. Faster on GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("ultralytics not installed. Run: pip install -r requirements.txt")


DATASET_ROOT = Path(r"C:\Users\KARTHIKK\Downloads\Cricket Bat detection.v1i.yolov8")
DATA_YAML = DATASET_ROOT / "data.yaml"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = PROJECT_ROOT / "runs"


def fix_data_yaml(src: Path) -> Path:
    """Roboflow's data.yaml uses relative paths that break depending on cwd.
    Write a normalized copy with absolute paths next to the original."""
    import yaml

    with open(src, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Replace relative paths with absolute ones based on the dataset root
    cfg["train"] = str((DATASET_ROOT / "train" / "images").resolve())
    cfg["val"] = str((DATASET_ROOT / "valid" / "images").resolve())
    cfg["test"] = str((DATASET_ROOT / "test" / "images").resolve())

    fixed = DATASET_ROOT / "data_fixed.yaml"
    with open(fixed, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    print(f"[setup] Wrote normalized config: {fixed}")
    return fixed


def main() -> None:
    if not DATA_YAML.exists():
        sys.exit(f"Dataset config not found: {DATA_YAML}")

    fixed_yaml = fix_data_yaml(DATA_YAML)

    print("[train] Loading YOLOv8n pretrained weights (auto-downloads on first run)")
    model = YOLO("yolov8n.pt")

    print("[train] Starting training. CPU = slow; expect ~1-2 hours.")
    print("[train] You can stop early with Ctrl+C; best weights are saved each epoch.\n")
    model.train(
        data=str(fixed_yaml),
        epochs=30,                  # plenty for a 1-class detector with 2475 images
        imgsz=640,
        batch=8,                    # safe for typical CPU RAM
        device="cpu",               # change to "0" if you have an NVIDIA GPU + CUDA torch
        project=str(RUNS_DIR),
        name="bat_detector",
        exist_ok=True,
        workers=2,
        cache=False,                # don't try to cache 2.8k images in RAM
        patience=8,                 # early stop if no val improvement for 8 epochs
        plots=True,                 # save training curves + confusion matrix
        save_period=-1,             # only save the best, not every epoch
    )

    best = RUNS_DIR / "bat_detector" / "weights" / "best.pt"
    print(f"\n[done] Best weights: {best}")
    print(f"[done] Size: {best.stat().st_size // 1024} KB")
    print("\nNext: send this best.pt to your project owner so they can integrate")
    print("it into the HF Space backend (alongside the YOLO-Pose model).")


if __name__ == "__main__":
    main()
