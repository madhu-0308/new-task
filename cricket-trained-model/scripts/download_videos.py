"""
Download per-class cricket shot compilations from YouTube.

Reads scripts/urls_by_class.yaml and saves each URL's video into
data/raw_videos/<class>/, so videos inherit their class from the folder.

Usage:
    python scripts/download_videos.py                 # download every class
    python scripts/download_videos.py --class drive   # only one class
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
    import yt_dlp
except ImportError as e:
    sys.exit(f"Missing dependency: {e}. Run: pip install -r requirements.txt")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
URLS_FILE = PROJECT_ROOT / "scripts" / "urls_by_class.yaml"
RAW_DIR = PROJECT_ROOT / "data" / "raw_videos"


def load_urls() -> dict[str, list[str]]:
    if not URLS_FILE.exists():
        sys.exit(f"URL file not found: {URLS_FILE}")
    data = yaml.safe_load(URLS_FILE.read_text(encoding="utf-8")) or {}
    out: dict[str, list[str]] = {}
    for cls, entry in data.items():
        urls = (entry or {}).get("urls") or []
        out[cls] = [u for u in urls if u and not u.startswith("#")]
    return out


def build_options(class_dir: Path) -> dict:
    return {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(class_dir / "%(id)s_%(title).80s.%(ext)s"),
        "download_archive": str(class_dir / ".download_archive.txt"),
        "ignoreerrors": True,
        "noplaylist": False,
        "quiet": False,
        "restrictfilenames": True,
        "concurrent_fragment_downloads": 4,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--class", dest="cls", help="Download only this class")
    args = ap.parse_args()

    urls_by_class = load_urls()

    if args.cls:
        if args.cls not in urls_by_class:
            sys.exit(f"Unknown class '{args.cls}'. Known: {list(urls_by_class)}")
        urls_by_class = {args.cls: urls_by_class[args.cls]}

    total = sum(len(v) for v in urls_by_class.values())
    if total == 0:
        sys.exit("No URLs in urls_by_class.yaml. Add some under the class keys first.")

    print(f"Found {total} URL(s) across {len([c for c, u in urls_by_class.items() if u])} class(es).\n")

    for cls, urls in urls_by_class.items():
        if not urls:
            continue
        class_dir = RAW_DIR / cls
        class_dir.mkdir(parents=True, exist_ok=True)
        print(f"=== {cls} ({len(urls)} URLs) -> {class_dir} ===")
        with yt_dlp.YoutubeDL(build_options(class_dir)) as ydl:
            ydl.download(urls)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
