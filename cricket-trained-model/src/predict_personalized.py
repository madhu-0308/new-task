"""Inference with user tracking and personalized feedback.

Usage:
    python src/predict_personalized.py USER_ID video.mp4
    python src/predict_personalized.py USER_ID video.mp4 --actual-shot "Cover Drive" --feedback
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import PoseTransformer  # noqa: E402
from coach import generate_coaching_feedback  # noqa: E402
from user_manager import UserManager  # noqa: E402
from analytics import AnalyticsTracker  # noqa: E402
from personalized_coach import PersonalizedCoach  # noqa: E402

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


def run_prediction(
    video_path: Path,
    ckpt: Path,
    pose_model_name: str,
    device: str,
    topk: int = 3,
) -> tuple[str, float, np.ndarray, dict[int, str], np.ndarray]:
    try:
        ckpt_data = torch.load(str(ckpt), map_location=device, weights_only=False)
    except TypeError:
        ckpt_data = torch.load(str(ckpt), map_location=device)
    class_index: dict[str, int] = ckpt_data["class_index"]
    id_to_name = {v: k for k, v in class_index.items()}
    state_dict = ckpt_data["state_dict"]
    in_proj_key = next((k for k in state_dict.keys() if k.endswith("in_proj.weight")), None)
    in_dim = state_dict[in_proj_key].shape[1] if in_proj_key is not None else 51
    model = PoseTransformer(num_classes=len(class_index), in_dim=in_dim).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    pose_model = YOLO(pose_model_name)
    seq = extract_clip(video_path, pose_model)
    if seq is None:
        sys.exit("Pose extraction failed — couldn't reliably detect a batsman.")

    x = torch.from_numpy(seq.reshape(seq.shape[0], -1)).unsqueeze(0).to(device)
    expected_in = model.in_proj.in_features
    if x.size(-1) < expected_in:
        pad = torch.zeros(x.size(0), x.size(1), expected_in - x.size(-1), device=x.device)
        x = torch.cat([x, pad], dim=-1)
    elif x.size(-1) > expected_in:
        x = x[:, :, :expected_in]

    with torch.no_grad():
        logits = model(x)
        probs = logits.softmax(-1).squeeze(0).cpu().numpy()

    top_idx = int(np.argsort(probs)[::-1][0])
    shot = id_to_name[top_idx]
    confidence = float(probs[top_idx])
    return shot, confidence, seq, id_to_name, probs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("user_id", help="Registered user id (see coach_cli.py user create)")
    ap.add_argument("video", help="Path to .mp4 OR URL")
    ap.add_argument("--ckpt", default=str(DEFAULT_CKPT))
    ap.add_argument("--pose-model", default=DEFAULT_POSE_MODEL)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--device", default=None)
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--actual-shot", default=None, help="Ground-truth shot for feedback")
    ap.add_argument("--feedback", action="store_true", help="Show session coaching feedback")
    args = ap.parse_args()

    users = UserManager()
    try:
        profile = users.get_user(args.user_id)
    except KeyError:
        sys.exit(f"Unknown user '{args.user_id}'. Create with: python src/coach_cli.py user create {args.user_id}")

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
        video_path = trim_clip(video_path, start, end, trimmed)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"User: {profile.display_name} ({profile.skill_level})")
    print(f"Extracting pose from {video_path.name} ...")

    shot, confidence, seq, id_to_name, probs = run_prediction(
        video_path, Path(args.ckpt), args.pose_model, device, args.topk
    )

    tracker = AnalyticsTracker()
    pred_id = tracker.record_prediction(
        args.user_id,
        str(video_path),
        shot,
        confidence,
    )

    if args.actual_shot:
        tracker.record_feedback(pred_id, args.actual_shot)

    pose_feedback = generate_coaching_feedback(seq, shot, probs, id_to_name)
    print(f"\nPrediction: {shot} ({confidence:.3f}) [tracked id={pred_id}]")
    print(f"  Issue : {pose_feedback['issue']}")
    print(f"  Advice: {pose_feedback['advice']}")

    if args.feedback:
        coach = PersonalizedCoach(users, tracker)
        session = coach.get_session_feedback(args.user_id)
        print(f"\n--- Session Feedback ---")
        print(session["greeting"])
        print(session["session_message"])
        if session["recommendations"]:
            print("\nRecommendations:")
            for r in session["recommendations"]:
                print(f"  • {r}")
        if session["technical_tips"]:
            print("\nTechnical Tips:")
            for t in session["technical_tips"]:
                print(f"  • {t}")

    if tmpdir is not None and not args.keep:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
