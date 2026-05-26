import torch
from pathlib import Path

# Load from temp location
temp_model_dir = Path(r"C:\Users\madhu\AppData\Local\Temp\cricket_model\best")

try:
    # Load as directory-based checkpoint
    ckpt = torch.load(str(temp_model_dir), map_location='cpu')
    print(f"Loaded successfully!")
    print(f"Checkpoint type: {type(ckpt)}")
    if isinstance(ckpt, dict):
        print(f"Keys: {list(ckpt.keys())}")
    
    # Save as proper .pt file to the original location
    output_path = r"C:\Users\madhu\OneDrive\Desktop\next-level\cricket-trained-model\runs\exp1\best.pt"
    torch.save(ckpt, output_path)
    print(f"✓ Model saved to: {output_path}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
