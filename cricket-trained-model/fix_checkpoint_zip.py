from pathlib import Path
import zipfile
import torch

MODEL_DIR = Path("runs") / "exp1"
OUT = MODEL_DIR / "best.pt"

if not MODEL_DIR.exists():
    raise SystemExit(f"Model dir not found: {MODEL_DIR}")

print(f"Packing files from {MODEL_DIR} into {OUT} ...")
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_STORED) as zf:
    # Torch expects files inside a top-level subdirectory in the archive
    # Place everything inside a top-level folder (e.g., 'best/'), with numeric files in 'best/data/'
    prefix = OUT.stem
    for p in sorted(MODEL_DIR.iterdir()):
        if p.name == OUT.name:
            continue
        if not p.is_file():
            continue
        if p.name.isdigit():
            arcname = f"{prefix}/data/{p.name}"
        else:
            arcname = f"{prefix}/{p.name}"
        zf.write(p, arcname=arcname)

print(f"Created archive: {OUT}")

try:
    ckpt = torch.load(str(OUT), map_location="cpu")
    print("Loaded checkpoint successfully.")
    if isinstance(ckpt, dict):
        print("Keys:", list(ckpt.keys()))
    else:
        print("Loaded object type:", type(ckpt))
except Exception as e:
    print("Error loading packed checkpoint:", type(e).__name__, e)
