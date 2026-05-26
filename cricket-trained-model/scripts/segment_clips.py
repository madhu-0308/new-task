"""
Split per-class videos in data/raw_videos/<class>/ into per-shot candidate clips
in data/clips/<class>/. Class is inherited from the source folder, so no
manual labeling is needed for the class itself.

You will still want a quick keep/trash review pass after this (scripts/review_clips.py)
to remove non-shot frames (scoreboards, crowd, slow-mo replays of context).

Usage:
    python scripts/segment_clips.py                    # process every class folder
    python scripts/segment_clips.py --class drive      # only one class
    python scripts/segment_clips.py --threshold 30     # less sensitive scene cuts
    python scripts/segment_clips.py --min 1.0 --max 10 # adjust duration filter
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from scenedetect import detect, ContentDetector
except ImportError:
    sys.exit("scenedetect not installed. Run: pip install -r requirements.txt")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw_videos"
CLIPS_DIR = PROJECT_ROOT / "data" / "clips"

CLASS_NAMES = ["drive", "cut", "pull_hook", "sweep", "defensive", "glance", "innovative", "other"]


def detect_scenes(video_path: Path, threshold: float):
    scenes = detect(str(video_path), ContentDetector(threshold=threshold))
    return [(s.seconds, e.seconds) for s, e in scenes]


def cut_clip(src: Path, start: float, end: float, dst: Path) -> bool:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.3f}",
        "-i", str(src),
        "-t", f"{end - start:.3f}",
        "-vf", "scale=-2:480,fps=25",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-an",
        str(dst),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    ffmpeg failed: {r.stderr.strip()[:200]}")
        return False
    return True


def process_class(cls: str, threshold: float, min_dur: float, max_dur: float) -> dict:
    src_dir = RAW_DIR / cls
    dst_dir = CLIPS_DIR / cls
    if not src_dir.exists():
        return {"videos": 0, "detected": 0, "kept": 0}
    videos = sorted(src_dir.glob("*.mp4"))
    if not videos:
        return {"videos": 0, "detected": 0, "kept": 0}

    dst_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {cls} ({len(videos)} videos) ===")

    detected_total = 0
    kept_total = 0
    for v in videos:
        print(f"  detecting scenes in {v.name} ...")
        scenes = detect_scenes(v, threshold)
        detected_total += len(scenes)
        video_id = v.stem.split("_")[0]
        kept_here = 0
        for idx, (start, end) in enumerate(scenes):
            dur = end - start
            if dur < min_dur or dur > max_dur:
                continue
            out_name = f"{cls}_{video_id}_s{idx:03d}_{int(start)}s.mp4"
            out_path = dst_dir / out_name
            if out_path.exists():
                kept_here += 1
                continue
            if cut_clip(v, start, end, out_path):
                kept_here += 1
        kept_total += kept_here
        print(f"    -> {kept_here}/{len(scenes)} clips kept")
    return {"videos": len(videos), "detected": detected_total, "kept": kept_total}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--class", dest="cls", help="Only this class")
    ap.add_argument("--threshold", type=float, default=27.0)
    ap.add_argument("--min", dest="min_dur", type=float, default=1.5)
    ap.add_argument("--max", dest="max_dur", type=float, default=8.0)
    args = ap.parse_args()

    classes = [args.cls] if args.cls else CLASS_NAMES
    if args.cls and args.cls not in CLASS_NAMES:
        sys.exit(f"Unknown class '{args.cls}'. Known: {CLASS_NAMES}")

    grand = {"videos": 0, "detected": 0, "kept": 0}
    for cls in classes:
        stats = process_class(cls, args.threshold, args.min_dur, args.max_dur)
        for k in grand:
            grand[k] += stats[k]

    print(f"\nTotal: {grand['kept']} clips from {grand['detected']} scenes "
          f"across {grand['videos']} videos.")


if __name__ == "__main__":
    main()
