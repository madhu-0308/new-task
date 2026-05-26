"""Quick local test for the session analyzer.

Usage:
    python scripts/test_session.py "C:\\Users\\KARTHIKK\\Downloads\\vid\\6shots.mp4"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make the HF Space module importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HF_DIR = PROJECT_ROOT.parent / "hf-space-cricket"
sys.path.insert(0, str(HF_DIR))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    args = ap.parse_args()

    if not args.video.exists():
        sys.exit(f"Video not found: {args.video}")

    from shot_classifier.session import analyze_session
    print(f"Analyzing {args.video} ...\n")
    result = analyze_session(args.video)

    if "error" in result:
        print(f"\nERROR: {result['error']}")
        sys.exit(1)

    # Pretty header
    print("\n" + "=" * 70)
    print(f"Session report — {args.video.name}")
    print(f"  Duration: {result['video_seconds']:.1f}s")
    print(f"  Balls detected: {result['balls_detected']}")
    print(f"  Wall time: {result.get('elapsed_seconds', '?')}s")
    print("=" * 70)

    for b in result["balls"]:
        print(
            f"\n  Ball #{b['index']}  ({b['start_sec']:.1f}-{b['end_sec']:.1f}s, peak {b['peak_sec']:.1f}s)"
        )
        print(f"    shot       : {b['shot']:<12}  conf {b['confidence']:.2f}")
        print(f"    topk       : " + ", ".join(
            f"{t['class']}({t['confidence']:.2f})" for t in b['topk']
        ))
        sig = b["signals"]
        print(f"    signals    : bat-path={sig['bat_path_straightness']}  "
              f"head-still={sig['head_stillness']}  "
              f"foot-commit={sig['foot_commitment']}")
        print(f"    grade      : {b['grade']:.1f}/10  ({', '.join(b['notes'])})")

    print("\n" + "-" * 70)
    print("Session summary:")
    s = result["summary"]
    print(f"  shot counts        : {s['shot_counts']}")
    print(f"  per-class average  : {s['per_class_avg_grade']}")
    print(f"  weakest shot       : {s['weakest_shot']}")
    print(f"  weakness reason    : {s['weakness_reason']}")
    print(f"  session grade      : {s['session_grade']}/10")
    print("-" * 70)

    out = Path("scripts/last_session_report.json")
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"\nFull JSON written to {out}")


if __name__ == "__main__":
    main()
