"""
Generate a dummy trained model for inference testing.
This allows testing the full prediction + coaching pipeline without the full training cycle.
"""

import torch
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))
from model import PoseTransformer

# Create a dummy model with random weights
num_classes = 15
model = PoseTransformer(num_classes=num_classes)

# Create class mapping (from classes.yaml)
class_names = [
    "Cover Drive", "Defensive", "Down The Wicket", "Flick", "Hook",
    "Late Cut", "Lofted Legside", "Lofted Offside", "Pull",
    "Reverse Sweep", "Scoop", "Square Cut", "Straight Drive",
    "Sweep", "Upper Cut"
]

class_index = {name: i for i, name in enumerate(class_names)}

# Create checkpoint
ckpt = {
    "state_dict": model.state_dict(),
    "class_index": class_index,
}

# Save to runs/exp1/best.pt
output_dir = Path(__file__).parent / "runs" / "exp1"
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / "best.pt"
torch.save(ckpt, output_path)

print(f"✓ Dummy model created at: {output_path}")
print(f"✓ Number of classes: {num_classes}")
print(f"✓ Classes: {class_names}")
print("\nNote: This is a randomly-initialized model for testing the inference pipeline.")
print("For production use, train a real model using scripts/train.py")
