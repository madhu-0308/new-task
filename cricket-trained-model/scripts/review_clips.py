"""Interactive clip review using OpenCV — one shot class at a time.

Opens each .mp4 in an OpenCV window that AUTO-LOOPS the clip and reads
keypresses from the SAME window (so no PowerShell-vs-player focus
fight). Decisions per clip:

    k  keep    — leave the file in --source (training set)
    d  delete  — move to data/clips/_trash/<class>/<filename>  (recoverable)
    s  skip    — leave it alone, go to next
    r  replay  — restart the clip from the first frame
    q  quit    — end the review now (prints summary)

Usage
-----
    python scripts/review_clips.py --class pull_hook
        Reviews data/clips/pull_hook/*.mp4 in place.

    python scripts/review_clips.py --class drive --source data/incoming
        Reviews user-contributed clips and moves keepers into data/clips/drive/.

    python scripts/review_clips.py --class drive --dry-run
        Show what would happen, don't move/delete anything.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

import cv2

VALID_CLASSES = {
    "drive", "cut", "pull_hook", "sweep",
    "defensive", "innovative", "glance",
}


def _draw_overlay(frame, *, idx, total, name, kept, deleted, skipped):
    """Paint a small HUD on the video so the reviewer always knows where
    they are and which keys to press."""
    h, w = frame.shape[:2]
    bar_h = 60
    # Top bar
    cv2.rectangle(frame, (0, 0), (w, bar_h), (0, 0, 0), -1)
    cv2.putText(frame, f"[{idx + 1}/{total}]  {name}",
                (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"kept {kept}   deleted {deleted}   skipped {skipped}",
                (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)
    # Bottom bar with key legend
    cv2.rectangle(frame, (0, h - 34), (w, h), (0, 0, 0), -1)
    cv2.putText(frame, "[K]eep   [D]elete   [S]kip   [R]eplay   [Q]uit",
                (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 255, 140), 1, cv2.LINE_AA)


def review_class(
    cls: str,
    source_dir: Path,
    dest_dir: Path,
    trash_dir: Path,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Walk every clip in source_dir/<cls> and let the reviewer decide.
    Returns (kept, deleted, skipped) counts."""
    src_class_dir = source_dir / cls
    if not src_class_dir.is_dir():
        print(f"[review] {src_class_dir} does not exist — nothing to review.")
        return 0, 0, 0

    clips = sorted(src_class_dir.glob("*.mp4"))
    if not clips:
        print(f"[review] {src_class_dir} has no .mp4 files.")
        return 0, 0, 0

    in_place = src_class_dir.resolve() == (dest_dir / cls).resolve()
    print(f"[review] class={cls}  source={src_class_dir}  clips={len(clips)}")
    print(f"[review] keep -> "
          + ("(in-place, no move)" if in_place else str(dest_dir / cls)))
    print(f"[review] delete -> {trash_dir / cls}")
    if dry_run:
        print("[review] DRY-RUN: no files will actually be moved or deleted")
    print()

    if not in_place and not dry_run:
        (dest_dir / cls).mkdir(parents=True, exist_ok=True)
    if not dry_run:
        (trash_dir / cls).mkdir(parents=True, exist_ok=True)

    win = f"review:{cls}"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 800, 600)

    kept = deleted = skipped = 0

    try:
        for i, clip_path in enumerate(clips):
            cap = cv2.VideoCapture(str(clip_path))
            if not cap.isOpened():
                print(f"  [{i+1}/{len(clips)}] {clip_path.name} — could not open, skipping")
                skipped += 1
                continue

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            delay_ms = max(1, int(1000.0 / fps))

            decision = None  # k/d/s/q
            while decision is None:
                ret, frame = cap.read()
                if not ret:
                    # End of clip — loop back to first frame
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                _draw_overlay(
                    frame,
                    idx=i, total=len(clips), name=clip_path.name,
                    kept=kept, deleted=deleted, skipped=skipped,
                )
                cv2.imshow(win, frame)

                key = cv2.waitKey(delay_ms) & 0xFF
                if key == 255:
                    continue
                ch = chr(key).lower() if 32 <= key < 127 else ""
                if ch in ("k", "d", "s", "q"):
                    decision = ch
                elif ch == "r":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                elif key == 27:  # Esc -> quit
                    decision = "q"

            cap.release()

            if decision == "k":
                if in_place or dry_run:
                    print(f"  [{i+1}/{len(clips)}] {clip_path.name} -> KEEP")
                else:
                    target = dest_dir / cls / clip_path.name
                    if target.exists():
                        print(f"  [{i+1}/{len(clips)}] {clip_path.name} -> KEEP (already in dest)")
                    else:
                        shutil.move(str(clip_path), str(target))
                        print(f"  [{i+1}/{len(clips)}] {clip_path.name} -> KEEP (moved)")
                kept += 1

            elif decision == "d":
                if dry_run:
                    print(f"  [{i+1}/{len(clips)}] {clip_path.name} -> DELETE (dry-run)")
                else:
                    target = trash_dir / cls / clip_path.name
                    # If a previous review trashed a file of the same name,
                    # suffix this one so it isn't overwritten.
                    if target.exists():
                        stem, suf = target.stem, target.suffix
                        target = target.with_name(f"{stem}_{int(time.time())}{suf}")
                    shutil.move(str(clip_path), str(target))
                    # ALSO archive the matching .npy pose file if present
                    # so the next make_splits run doesn't drag a stale
                    # pose back into training.
                    npy = Path("data/poses") / cls / (clip_path.stem + ".npy")
                    if npy.exists():
                        npy_trash = trash_dir / cls / npy.name
                        if npy_trash.exists():
                            stem2, suf2 = npy_trash.stem, npy_trash.suffix
                            npy_trash = npy_trash.with_name(f"{stem2}_{int(time.time())}{suf2}")
                        shutil.move(str(npy), str(npy_trash))
                        extra = " (+ pose .npy)"
                    else:
                        extra = ""
                    print(f"  [{i+1}/{len(clips)}] {clip_path.name} -> DELETE{extra}")
                deleted += 1

            elif decision == "s":
                print(f"  [{i+1}/{len(clips)}] {clip_path.name} -> SKIP")
                skipped += 1

            else:  # q
                print(f"\n[review] Quit at clip {i+1}/{len(clips)}.")
                break
    finally:
        cv2.destroyAllWindows()

    return kept, deleted, skipped


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--class", dest="cls", required=True, choices=sorted(VALID_CLASSES),
                    help="Which shot class to review.")
    ap.add_argument("--source", default="data/clips",
                    help="Folder with <class>/*.mp4 to review. Default: data/clips")
    ap.add_argument("--dest", default="data/clips",
                    help="Where keepers go if --source != --dest. Default: data/clips")
    ap.add_argument("--trash", default="data/clips/_trash",
                    help="Where deleted clips are moved. Default: data/clips/_trash")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would happen, don't move/delete anything.")
    args = ap.parse_args()

    source = Path(args.source)
    dest   = Path(args.dest)
    trash  = Path(args.trash)

    print("=" * 60)
    print(f" Cricket Shot — clip review  (class={args.cls})")
    print("=" * 60)

    kept, deleted, skipped = review_class(
        args.cls, source, dest, trash, args.dry_run
    )

    print()
    print("-" * 60)
    print(f" Summary for '{args.cls}':  kept {kept}   deleted {deleted}   skipped {skipped}")
    print("-" * 60)
    if kept > 0 or deleted > 0:
        print()
        print("Next steps:")
        print(f"  python scripts/extract_poses.py --class {args.cls}")
        print(f"  python scripts/make_splits.py")
        print(f"  python src/train.py --epochs 80 --batch 16 --class-weights uniform "
              f"--exp exp_{args.cls}_reviewed")


if __name__ == "__main__":
    main()
