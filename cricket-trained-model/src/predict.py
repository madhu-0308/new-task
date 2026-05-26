"""End-to-end inference: predict the shot class for a video file or URL.

Pipeline: video -> YOLO-Pose -> normalized (T, 17, 3) sequence -> trained model -> top-k.

Accepts local files OR URLs (YouTube, Google Drive, and anything yt-dlp supports).

Usage:
    python src/predict.py path/to/clip.mp4
    python src/predict.py https://youtu.be/XXXX
    python src/predict.py https://drive.google.com/file/d/XXXX/view
    python src/predict.py https://youtu.be/XXXX --start 12 --end 14    # trim to seconds 12-14
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

# allow local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import PoseTransformer  # noqa: E402
from coach import generate_coaching_feedback  # noqa: E402

# reuse the pose-extraction primitives
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from extract_poses import extract_clip  # noqa: E402

try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("ultralytics not installed. Run: pip install -r requirements.txt")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CKPT = PROJECT_ROOT / "runs" / "exp1" / "best.pt"
DEFAULT_POSE_MODEL = "yolov8n-pose.pt"


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def download_to_tmp(url: str, tmpdir: Path) -> Path:
    try:
        import yt_dlp
    except ImportError:
        sys.exit("yt-dlp not installed. Run: pip install -r requirements.txt")
    opts = {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(tmpdir / "input.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    print(f"Downloading {url} ...")
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    files = sorted(tmpdir.glob("input.*"))
    if not files:
        sys.exit("Download failed — no file produced.")
    return files[0]


def trim_clip(src: Path, start: float, end: float, dst: Path) -> Path:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{end - start:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-an", str(dst),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg trim failed: {r.stderr.strip()[:200]}")
    return dst


def video_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", help="Path to .mp4 OR a URL (YouTube / Drive / etc.)")
    ap.add_argument("--ckpt", default=str(DEFAULT_CKPT))
    ap.add_argument("--pose-model", default=DEFAULT_POSE_MODEL)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--device", default=None)
    ap.add_argument("--start", type=float, default=None, help="Trim start in seconds")
    ap.add_argument("--end", type=float, default=None, help="Trim end in seconds")
    ap.add_argument("--keep", action="store_true", help="Keep the downloaded temp file")
    args = ap.parse_args()

    # resolve input -> local file, possibly trimmed
    tmpdir: Path | None = None
    if is_url(args.video):
        tmpdir = Path(tempfile.mkdtemp(prefix="predict_"))
        video_path = download_to_tmp(args.video, tmpdir)
    else:
        video_path = Path(args.video)
        if not video_path.exists():
            sys.exit(f"Video not found: {video_path}")

    if args.start is not None or args.end is not None:
        tmpdir = tmpdir or Path(tempfile.mkdtemp(prefix="predict_"))
        start = args.start or 0.0
        dur = video_duration(video_path)
        end = args.end if args.end is not None else dur
        trimmed = tmpdir / "trimmed.mp4"
        print(f"Trimming to {start:.2f}-{end:.2f}s ...")
        video_path = trim_clip(video_path, start, end, trimmed)

    dur = video_duration(video_path)
    if dur > 12:
        print(f"WARNING: clip is {dur:.1f}s long. The model was trained on ~2s clips. "
              "Predictions on long videos will be muddy — use --start/--end to trim.")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    # load classifier (be explicit about weights_only for PyTorch>=2.6 compatibility)
    try:
        ckpt = torch.load(args.ckpt, map_location=device, weights_only=False)
    except TypeError:
        # older PyTorch versions do not accept the weights_only kwarg
        ckpt = torch.load(args.ckpt, map_location=device)
    class_index: dict[str, int] = ckpt["class_index"]
    id_to_name = {v: k for k, v in class_index.items()}
    num_classes = len(class_index)

    # infer input dimension from checkpoint state_dict (handles older/newer model configs)
    state_dict = ckpt["state_dict"]
    in_proj_key = next((k for k in state_dict.keys() if k.endswith("in_proj.weight")), None)
    if in_proj_key is not None:
        in_dim = state_dict[in_proj_key].shape[1]
    else:
        in_dim = 51
    model = PoseTransformer(num_classes=num_classes, in_dim=in_dim).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    # extract pose sequence
    print(f"Extracting pose from {video_path.name} ...")
    pose_model = YOLO(args.pose_model)
    seq = extract_clip(video_path, pose_model)
    if seq is None:
        sys.exit("Pose extraction failed — couldn't reliably detect a batsman.")

    # forward
    x = torch.from_numpy(seq.reshape(seq.shape[0], -1)).unsqueeze(0).to(device)
    # ensure input width matches model's expected in_dim (pad or truncate as needed)
    expected_in = model.in_proj.in_features
    if x.size(-1) < expected_in:
        pad = torch.zeros(x.size(0), x.size(1), expected_in - x.size(-1), device=x.device)
        x = torch.cat([x, pad], dim=-1)
    elif x.size(-1) > expected_in:
        x = x[:, :, :expected_in]

    with torch.no_grad():
        logits = model(x)
        probs = logits.softmax(-1).squeeze(0).cpu().numpy()

    topk = np.argsort(probs)[::-1][: args.topk]
    print(f"\nPrediction for {video_path.name}:")
    print(f"  {'class':<14s}  prob")
    print(f"  {'-' * 14}  -----")
    for cid in topk:
        print(f"  {id_to_name[int(cid)]:<14s}  {probs[cid]:.3f}")

    feedback = generate_coaching_feedback(seq, id_to_name[topk[0]], probs, id_to_name)
    print("\nPersonalized coach feedback:")
    print(f"  {feedback['coach']}")
    print(f"  predicted shot : {feedback['shot']}")
    print(f"  confidence     : {feedback['shot_confidence']:.2f}")
    print(f"  main issue     : {feedback['issue']}")
    print(f"  notes          : {feedback['notes']}")
    print(f"  advice         : {feedback['advice']}")

    if tmpdir is not None and not args.keep:
        shutil.rmtree(tmpdir, ignore_errors=True)
    elif tmpdir is not None:
        print(f"\nKept temp file at: {video_path}")


if __name__ == "__main__":
    main()
