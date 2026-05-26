import torch
import pickle
from pathlib import Path

# Load the model from the extracted directory
model_dir = Path("runs/exp1/best")

try:
    # Try to load as a directory-based checkpoint
    ckpt = torch.load(model_dir, map_location='cpu')
    print("Successfully loaded model from directory")
    print(f"Checkpoint keys: {ckpt.keys() if isinstance(ckpt, dict) else 'Not a dict'}")
    
    # Save it as a proper .pt file
    output_path = Path("runs/exp1/best.pt")
    torch.save(ckpt, output_path)
    print(f"Model saved to {output_path}")
    
except Exception as e:
    print(f"Error loading from directory: {e}")
    
    # Try alternative method: load from data.pkl
    try:
        with open(model_dir / "data.pkl", "rb") as f:
            data = pickle.load(f)
            print(f"Loaded from data.pkl: {type(data)}")
    except Exception as e2:
        print(f"Error loading from data.pkl: {e2}")
