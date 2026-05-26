"""Minimal Flask server to accept video uploads and return shot + coaching feedback.

Run locally:
  .venv\Scripts\python src\server.py          # start web server
  .venv\Scripts\python src\server.py --test "path/to/video.mp4"   # run one prediction

The server reuses the same prediction + coaching pipeline used by `src/predict.py`.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

import numpy as np
import torch
import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# config
CKPT_PATH = Path(os.environ.get("CKPT_PATH", PROJECT_ROOT / "runs" / "exp1" / "best.pt"))
POSE_MODEL = Path(os.environ.get("POSE_MODEL", PROJECT_ROOT / "yolov8n-pose.pt"))
DEVICE = torch.device("cpu")

# lazy imports for modules that live in scripts/
import sys
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from extract_poses import extract_clip, T_FRAMES  # type: ignore

sys.path.insert(0, str(PROJECT_ROOT / "src"))
from model import PoseTransformer  # type: ignore
from coach import generate_coaching_feedback  # type: ignore

app = Flask(__name__)
CORS(app)


def load_checkpoint(path: Path, device: torch.device) -> tuple[torch.nn.Module, dict[int, str]]:
    try:
        ckpt = torch.load(str(path), map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(str(path), map_location=device)

    state_dict = ckpt["state_dict"]
    class_index = ckpt.get("class_index") or ckpt.get("class_idx")
    if class_index is None:
        raise RuntimeError("Checkpoint missing class_index mapping")
    id_to_name = {v: k for k, v in class_index.items()}
    # infer input dim
    in_proj_key = next((k for k in state_dict.keys() if k.endswith("in_proj.weight")), None)
    in_dim = state_dict[in_proj_key].shape[1] if in_proj_key is not None else 51

    model = PoseTransformer(num_classes=len(class_index), in_dim=int(in_dim)).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    return model, id_to_name


@app.route("/", methods=["GET"])
def index() -> str:
        return render_template("index.html")


def _pad_truncate_tensor(x: torch.Tensor, expected_in: int) -> torch.Tensor:
    if x.size(-1) < expected_in:
        pad = torch.zeros(x.size(0), x.size(1), expected_in - x.size(-1), device=x.device)
        x = torch.cat([x, pad], dim=-1)
    elif x.size(-1) > expected_in:
        x = x[:, :, :expected_in]
    return x


def predict_file(model: torch.nn.Module, id_to_name: dict[int, str], pose_model: Any, file_path: Path) -> dict[str, Any]:
    seq = extract_clip(file_path, pose_model)
    if seq is None:
        return {"error": "Pose extraction failed — couldn't reliably detect a batsman."}

    x = torch.from_numpy(seq.reshape(seq.shape[0], -1)).unsqueeze(0).to(DEVICE)
    expected_in = model.in_proj.in_features
    x = _pad_truncate_tensor(x, expected_in)

    with torch.no_grad():
        logits = model(x)
        probs = logits.softmax(-1).squeeze(0).cpu().numpy()

    topk = np.argsort(probs)[::-1][:3]
    preds = [{"name": id_to_name[int(cid)], "prob": float(probs[cid])} for cid in topk]
    shot = id_to_name[int(topk[0])]
    feedback = generate_coaching_feedback(seq, shot, probs, id_to_name)

    # Run optional object detection for ball / bat and resample to the
    # same T_FRAMES used by the pose extractor so clients can align results.
    def _detect_ball_bat(video_path: Path, det_model, target_T: int = T_FRAMES) -> dict[str, Any]:
        if det_model is None:
            return {"frames": [], "summary": {"ball_count": 0, "bat_count": 0}}
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {"frames": [], "summary": {"ball_count": 0, "bat_count": 0}}
        frames_boxes = []
        img_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        img_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            total += 1
            try:
                res = det_model(frame, verbose=False)[0]
            except Exception:
                frames_boxes.append({"ball": [], "bat": []})
                continue
            if hasattr(res, "boxes") and len(res.boxes) > 0:
                xy = res.boxes.xyxy.cpu().numpy()
                conf = res.boxes.conf.cpu().numpy() if res.boxes.conf is not None else np.ones((len(xy),), dtype=float)
                cls = res.boxes.cls.cpu().numpy() if res.boxes.cls is not None else np.zeros((len(xy),), dtype=int)
                ball_boxes = []
                bat_boxes = []
                for b, c, cl in zip(xy, conf, cls):
                    label = DET_NAMES.get(int(cl), "")
                    if "ball" in label:
                        ball_boxes.append({"conf": float(c), "bbox": [float(b[0]) / img_w, float(b[1]) / img_h, float(b[2]) / img_w, float(b[3]) / img_h]})
                    elif "bat" in label:
                        bat_boxes.append({"conf": float(c), "bbox": [float(b[0]) / img_w, float(b[1]) / img_h, float(b[2]) / img_w, float(b[3]) / img_h]})
                frames_boxes.append({"ball": ball_boxes, "bat": bat_boxes})
            else:
                frames_boxes.append({"ball": [], "bat": []})
        cap.release()

        if total == 0:
            return {"frames": [], "summary": {"ball_count": 0, "bat_count": 0}}
        idx = np.linspace(0, max(0, total - 1), num=target_T).astype(int)
        sampled = [frames_boxes[i] for i in idx]
        ball_count = sum(1 for f in sampled if len(f.get("ball", [])) > 0)
        bat_count = sum(1 for f in sampled if len(f.get("bat", [])) > 0)
        return {"frames": sampled, "summary": {"ball_count": int(ball_count), "bat_count": int(bat_count)}}

    detections = _detect_ball_bat(file_path, DET_MODEL)

    # Save results
    out_dir = PROJECT_ROOT / "predictions"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"pred_{int(time.time())}.json"
    out_data = {"predictions": preds, "feedback": feedback}
    if detections:
        out_data["objects"] = detections
    out_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")

    return out_data


# Load models once at startup
print("Loading checkpoint and pose model (this may take a moment)...")
MODEL, ID_TO_NAME = load_checkpoint(CKPT_PATH, DEVICE)
try:
    from ultralytics import YOLO
except Exception as e:
    raise
POSE_MODEL = YOLO(str(POSE_MODEL))
POSE_MODEL.to(str(DEVICE))
print("Models ready.")

# Optional: lightweight COCO detection model for ball/bat
DET_MODEL_PATH = Path(os.environ.get("DET_MODEL", "yolov8n.pt"))
try:
    DET_MODEL = YOLO(str(DET_MODEL_PATH))
    DET_MODEL.to(str(DEVICE))
    DET_NAMES = {int(k): v.lower() for k, v in getattr(DET_MODEL, "names", {}).items()} if hasattr(DET_MODEL, "names") else {}
except Exception:
    DET_MODEL = None
    DET_NAMES = {}
    print("Warning: detection model not available — continuing without ball/bat detection")


@app.route("/predict", methods=["POST"])
def predict_endpoint():
    if "video" not in request.files:
        return jsonify({"error": "No file uploaded (field name must be 'video')."}), 400
    f = request.files["video"]
    suffix = Path(f.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(f.read())
        tmp_path = Path(tmp.name)

    try:
        res = predict_file(MODEL, ID_TO_NAME, POSE_MODEL, tmp_path)
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass
    return jsonify(res)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--test", help="Run one prediction on this file and exit")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    args = ap.parse_args()
    if args.test:
        print(json.dumps(predict_file(MODEL, ID_TO_NAME, POSE_MODEL, Path(args.test)), indent=2))
    else:
        app.run(host=args.host, port=args.port)
