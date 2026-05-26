"""Train the pose-sequence classifier.

Usage:
    python src/train.py                 # default 80 epochs, batch 32
    python src/train.py --epochs 120
    python src/train.py --device cuda
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

# allow `python src/train.py` without package install
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import PoseDataset  # noqa: E402
from model import PoseTransformer  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPLITS = PROJECT_ROOT / "data" / "splits"
POSES = PROJECT_ROOT / "data" / "poses"
RUNS = PROJECT_ROOT / "runs"


def eval_loader(model, loader, device, num_classes: int):
    model.eval()
    correct = total = 0
    cm = np.zeros((num_classes, num_classes), dtype=int)
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            pred = model(x).argmax(-1)
            correct += (pred == y).sum().item()
            total += y.size(0)
            for yt, yp in zip(y.cpu().numpy(), pred.cpu().numpy()):
                cm[yt, yp] += 1
    return correct / max(total, 1), cm


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--device", default=None, help="cuda or cpu (auto if omitted)")
    ap.add_argument("--exp", default="exp1", help="Run name under runs/")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--class-weights",
        choices=["inverse", "sqrt-inverse", "uniform"],
        default="sqrt-inverse",
        help="Use inverse-frequency, softened inverse-frequency, or equal class weights. "
             "sqrt-inverse is the safe default for small imbalanced datasets — full inverse "
             "weighting collapses the model onto the rarest class when sample counts are tiny.",
    )
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device = {device}")

    class_index = json.loads((SPLITS / "class_index.json").read_text(encoding="utf-8"))
    names = list(class_index.keys())
    num_classes = len(class_index)

    weights_data = json.loads((SPLITS / "class_weights.json").read_text(encoding="utf-8"))
    if args.class_weights == "uniform":
        weights = torch.ones(num_classes, dtype=torch.float32, device=device)
    elif args.class_weights == "sqrt-inverse":
        weight_values = np.sqrt(
            [weights_data["by_id"][str(i)] for i in range(num_classes)]
        ).astype(np.float32)
        weight_values = weight_values / weight_values.mean()
        weights = torch.tensor(weight_values, dtype=torch.float32, device=device)
    else:
        weights = torch.tensor(
            [weights_data["by_id"][str(i)] for i in range(num_classes)], dtype=torch.float32
        ).to(device)

    train_ds = PoseDataset(SPLITS / "train.txt", POSES, augment=True)
    val_ds = PoseDataset(SPLITS / "val.txt", POSES, augment=False)
    test_ds = PoseDataset(SPLITS / "test.txt", POSES, augment=False)
    print(f"train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}  classes={num_classes}")
    print(f"class_weights = {args.class_weights}")

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=64, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=64, num_workers=0)

    model = PoseTransformer(num_classes=num_classes).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model params = {n_params:,}")

    loss_fn = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    opt = AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    sched = CosineAnnealingLR(opt, T_max=args.epochs)

    exp_dir = RUNS / args.exp
    exp_dir.mkdir(parents=True, exist_ok=True)

    best_val = -1.0
    history = []
    for ep in range(1, args.epochs + 1):
        model.train()
        run_loss = run_correct = run_total = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss = loss_fn(logits, y)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            run_loss += loss.item() * y.size(0)
            run_correct += (logits.argmax(-1) == y).sum().item()
            run_total += y.size(0)
        sched.step()

        train_loss = run_loss / max(run_total, 1)
        train_acc = run_correct / max(run_total, 1)
        val_acc, _ = eval_loader(model, val_loader, device, num_classes)

        if val_acc > best_val:
            best_val = val_acc
            torch.save({"state_dict": model.state_dict(),
                        "class_index": class_index,
                        "epoch": ep}, exp_dir / "best.pt")

        history.append({"epoch": ep, "loss": train_loss,
                        "train_acc": train_acc, "val_acc": val_acc})
        if ep == 1 or ep % 5 == 0 or ep == args.epochs:
            print(f"ep{ep:3d}  loss={train_loss:.3f}  train={train_acc:.3f}  "
                  f"val={val_acc:.3f}  best_val={best_val:.3f}")

    # final test with the best checkpoint
    ckpt = torch.load(exp_dir / "best.pt", map_location=device)
    model.load_state_dict(ckpt["state_dict"])
    test_acc, cm = eval_loader(model, test_loader, device, num_classes)

    print(f"\n=== Test accuracy: {test_acc:.3f}  (best val: {best_val:.3f}) ===")
    print(f"\nConfusion matrix (rows=true, cols=pred):")
    header = "       " + " ".join(f"{n[:7]:>8}" for n in names)
    print(header)
    for i, name in enumerate(names):
        row = " ".join(f"{cm[i, j]:>8d}" for j in range(num_classes))
        print(f"{name[:7]:>7} {row}")

    # per-class recall (diagonal / row sum)
    print(f"\nPer-class recall:")
    for i, name in enumerate(names):
        denom = cm[i].sum()
        rec = cm[i, i] / denom if denom else 0.0
        print(f"  {name:<12s}  {rec:.3f}   ({cm[i, i]}/{denom})")

    (exp_dir / "results.json").write_text(json.dumps({
        "test_acc": test_acc,
        "best_val_acc": best_val,
        "epochs": args.epochs,
        "class_weights": args.class_weights,
        "history": history,
        "confusion_matrix": cm.tolist(),
        "class_index": class_index,
    }, indent=2), encoding="utf-8")
    print(f"\nSaved: {exp_dir/'best.pt'}, {exp_dir/'results.json'}")


if __name__ == "__main__":
    main()
