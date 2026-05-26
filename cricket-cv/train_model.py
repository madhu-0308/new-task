"""
YOLOv8 Fine-Tuning Script
--------------------------
Fine-tunes a YOLOv8 model on a cricket dataset downloaded from Roboflow.

Dataset: https://universe.roboflow.com/yolo-hnlmq/cricket-bhb8k
Classes: ball, bat, stumps, crease_line

Usage
-----
    # Download dataset and train from scratch:
    python train_model.py

    # Use an already downloaded dataset:
    python train_model.py --data path/to/data.yaml

    # Resume from a checkpoint:
    python train_model.py --resume runs/train/cricket_yolo/weights/last.pt

    # Quick smoke test (1 epoch):
    python train_model.py --epochs 1 --device cpu

Options
-------
    --data       Path to data.yaml (auto-downloaded if not provided)
    --base       Base YOLOv8 model (default: yolov8n.pt)
    --epochs     Number of training epochs (default: 50)
    --imgsz      Image size (default: 640)
    --batch      Batch size (default: 16, use -1 for auto)
    --device     cuda / cpu / mps (default: auto-detect)
    --project    Output directory (default: runs/train)
    --name       Experiment name (default: cricket_yolo)
    --resume     Path to checkpoint to resume from
    --roboflow-key  Roboflow API key (or set env var ROBOFLOW_API_KEY)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("cricket_cv.train")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

# Roboflow dataset coordinates
_RF_WORKSPACE = "yolo-hnlmq"
_RF_PROJECT   = "cricket-bhb8k"
_RF_VERSION   = 1

# Class mapping for the cricket dataset
CLASS_NAMES = ["ball", "bat", "stumps", "crease_line"]

_DATA_YAML_FALLBACK = """\
# Auto-generated data config (fallback when Roboflow download unavailable)
# Replace 'path' with the actual dataset root.
path: ./cricket_dataset
train: images/train
val:   images/valid
test:  images/test

nc: 4
names: ['ball', 'bat', 'stumps', 'crease_line']
"""


def download_roboflow_dataset(api_key: str, dest_dir: str = "cricket_dataset") -> str:
    """
    Download the cricket dataset from Roboflow.

    Returns the path to the generated data.yaml file.
    """
    try:
        from roboflow import Roboflow  # type: ignore
    except ImportError:
        logger.error(
            "roboflow package not installed. Run:  pip install roboflow"
        )
        sys.exit(1)

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(_RF_WORKSPACE).project(_RF_PROJECT)
    dataset = project.version(_RF_VERSION).download(
        "yolov8",
        location=dest_dir,
        overwrite=False,
    )
    data_yaml = Path(dest_dir) / "data.yaml"
    if not data_yaml.exists():
        # Some Roboflow versions put it at the project root
        data_yaml = Path(dataset.location) / "data.yaml"
    logger.info("Dataset downloaded: %s", dataset.location)
    logger.info("data.yaml: %s", data_yaml)
    return str(data_yaml)


def create_fallback_yaml(dest: str = "cricket_dataset/data.yaml") -> str:
    """Write a placeholder data.yaml so training can still be attempted."""
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_DATA_YAML_FALLBACK)
    logger.warning(
        "Wrote fallback data.yaml to %s. "
        "You must populate the 'cricket_dataset' folder with images and labels "
        "before running training.",
        dest,
    )
    return str(p)


def train(
    data_yaml: str,
    base_model: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "",
    project: str = "runs/train",
    name: str = "cricket_yolo",
    resume: str = "",
) -> str:
    """
    Fine-tune YOLOv8 on the cricket dataset.

    Returns the path to the best weights file.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run:  pip install ultralytics")
        sys.exit(1)

    import torch

    if not device:
        if torch.cuda.is_available():
            device = "0"       # first GPU
            logger.info("Using CUDA GPU: %s", torch.cuda.get_device_name(0))
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
            logger.info("Using Apple MPS.")
        else:
            device = "cpu"
            logger.warning("No GPU found. Training on CPU — this will be slow.")

    if resume:
        logger.info("Resuming training from: %s", resume)
        model = YOLO(resume)
    else:
        logger.info("Loading base model: %s", base_model)
        model = YOLO(base_model)

    logger.info(
        "Starting training: epochs=%d  imgsz=%d  batch=%d  device=%s",
        epochs, imgsz, batch, device,
    )

    model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        # Training hyperparameters tuned for cricket
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        # Augmentation — heavier augmentation helps with broadcast footage
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        # Validation
        val=True,
        save=True,
        save_period=10,
        patience=15,
        verbose=True,
        # Logging
        plots=True,
    )

    best_pt = Path(project) / name / "weights" / "best.pt"
    if best_pt.exists():
        logger.info("Best weights saved at: %s", best_pt)
    else:
        logger.warning("Could not locate best.pt after training.")

    return str(best_pt)


def validate(weights: str, data_yaml: str, imgsz: int = 640, device: str = "") -> None:
    """Run validation / benchmark on the fine-tuned model."""
    from ultralytics import YOLO
    import torch

    if not device:
        device = "0" if torch.cuda.is_available() else "cpu"

    model = YOLO(weights)
    metrics = model.val(data=data_yaml, imgsz=imgsz, device=device)

    print("\n" + "=" * 50)
    print(f"  mAP50      : {metrics.box.map50:.4f}")
    print(f"  mAP50-95   : {metrics.box.map:.4f}")
    print(f"  Precision  : {metrics.box.mp:.4f}")
    print(f"  Recall     : {metrics.box.mr:.4f}")
    print("=" * 50)


def export_model(weights: str, fmt: str = "onnx", imgsz: int = 640) -> None:
    """Export model to ONNX / TensorRT / CoreML etc. for deployment."""
    from ultralytics import YOLO
    model = YOLO(weights)
    path = model.export(format=fmt, imgsz=imgsz, half=False)
    logger.info("Model exported to: %s", path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune YOLOv8 on the cricket dataset from Roboflow",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--data",   default="",
                        help="Path to data.yaml (auto-download if empty)")
    parser.add_argument("--base",   default="yolov8n.pt",
                        help="Base YOLOv8 model")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz",  type=int, default=640)
    parser.add_argument("--batch",  type=int, default=16,
                        help="Batch size (-1 = auto)")
    parser.add_argument("--device", default="",
                        help="cuda device id, 'cpu', or '' for auto")
    parser.add_argument("--project", default="runs/train")
    parser.add_argument("--name",    default="cricket_yolo")
    parser.add_argument("--resume",  default="",
                        help="Checkpoint path to resume from")
    parser.add_argument("--roboflow-key", default="",
                        help="Roboflow API key (or set ROBOFLOW_API_KEY env var)")
    parser.add_argument("--export",  default="",
                        help="Export format after training (e.g. onnx, coreml)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Skip training, only validate --base weights")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Resolve data.yaml
    data_yaml = args.data
    if not data_yaml:
        api_key = args.roboflow_key or os.environ.get("ROBOFLOW_API_KEY", "")
        if api_key:
            data_yaml = download_roboflow_dataset(api_key)
        else:
            logger.warning(
                "No Roboflow API key provided. "
                "Set --roboflow-key or ROBOFLOW_API_KEY env var to auto-download. "
                "Creating fallback data.yaml — populate the dataset manually."
            )
            data_yaml = create_fallback_yaml()

    if args.validate_only:
        validate(args.base, data_yaml, args.imgsz, args.device)
        sys.exit(0)

    best_weights = train(
        data_yaml=data_yaml,
        base_model=args.base,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
    )

    # Optional post-training validation
    validate(best_weights, data_yaml, args.imgsz, args.device)

    # Optional export
    if args.export:
        export_model(best_weights, fmt=args.export, imgsz=args.imgsz)

    print(f"\nTraining complete. Best weights: {best_weights}")
    print(f"Use with main.py:  python main.py --video match.mp4 --model {best_weights}")
