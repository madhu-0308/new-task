"""
Generate stratified train/val/test splits over data/poses/<class>/*.npy.

Writes:
  data/splits/train.txt
  data/splits/val.txt
  data/splits/test.txt
  data/splits/class_index.json   # name -> id (only classes with data)
  data/splits/class_weights.json # inverse-freq weights for training

Each line in *.txt is: <class>/<filename.npy>\t<class_id>

Usage:
    python scripts/make_splits.py
    python scripts/make_splits.py --val 0.15 --test 0.15 --seed 42
"""

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSES_DIR = PROJECT_ROOT / "data" / "poses"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--val", type=float, default=0.15, help="Val fraction")
    ap.add_argument("--test", type=float, default=0.15, help="Test fraction")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.val + args.test >= 1.0:
        sys.exit("val + test must be < 1")

    rng = random.Random(args.seed)

    by_class: dict[str, list[Path]] = {}
    for cls in CLASS_NAMES:
        cdir = POSES_DIR / cls
        files = sorted(cdir.glob("*.npy")) if cdir.exists() else []
        if files:
            by_class[cls] = files

    if not by_class:
        sys.exit(f"No pose files found under {POSES_DIR}. Run extract_poses.py first.")

    # Stable class IDs based on order in CLASS_NAMES, but only for classes with data.
    class_index = {name: idx for idx, name in enumerate(by_class.keys())}

    train, val, test = [], [], []
    counts = defaultdict(lambda: [0, 0, 0])  # [train, val, test] per class

    for cls, files in by_class.items():
        files = list(files)
        rng.shuffle(files)
        n = len(files)
        # ensure at least 1 in val/test if we have >=3 samples
        n_test = max(1, int(round(n * args.test))) if n >= 3 else 0
        n_val = max(1, int(round(n * args.val))) if n >= 3 else 0
        # never let train shrink below 1
        if n_val + n_test >= n:
            n_val = max(0, n - n_test - 1)
        n_train = n - n_val - n_test

        cid = class_index[cls]
        for f in files[:n_train]:
            train.append((f, cid))
        for f in files[n_train:n_train + n_val]:
            val.append((f, cid))
        for f in files[n_train + n_val:]:
            test.append((f, cid))
        counts[cls] = [n_train, n_val, n_test]

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    def write_split(name: str, samples: list[tuple[Path, int]]):
        rng.shuffle(samples)  # mix classes
        lines = []
        for path, cid in samples:
            rel = path.relative_to(POSES_DIR).as_posix()
            lines.append(f"{rel}\t{cid}")
        (SPLITS_DIR / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    write_split("train", train)
    write_split("val", val)
    write_split("test", test)

    # class_index.json
    (SPLITS_DIR / "class_index.json").write_text(
        json.dumps(class_index, indent=2), encoding="utf-8"
    )

    # inverse-frequency class weights (computed on the training split)
    train_counts = Counter(cid for _, cid in train)
    total = sum(train_counts.values())
    # weight = total / (n_classes * count); normalize so mean == 1
    n_cls = len(class_index)
    raw = {cid: total / (n_cls * c) for cid, c in train_counts.items()}
    mean_w = sum(raw.values()) / len(raw)
    weights = {cid: round(w / mean_w, 4) for cid, w in raw.items()}
    (SPLITS_DIR / "class_weights.json").write_text(
        json.dumps({"by_id": {str(k): v for k, v in weights.items()},
                    "by_name": {name: weights[cid] for name, cid in class_index.items()}},
                   indent=2),
        encoding="utf-8",
    )

    # report
    print(f"\nSplit sizes:  train={len(train)}  val={len(val)}  test={len(test)}")
    print(f"\n{'class':<14} {'id':>3}  {'train':>5} {'val':>4} {'test':>4}  weight")
    for cls, cid in class_index.items():
        t, v, te = counts[cls]
        w = weights.get(cid, 1.0)
        print(f"{cls:<14} {cid:>3}  {t:>5} {v:>4} {te:>4}  {w:>6.3f}")

    print(f"\nWritten to: {SPLITS_DIR}")


if __name__ == "__main__":
    main()
