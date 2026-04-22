import torch
from pathlib import Path

# Get the directory where this script is actually saved
script_dir = Path(__file__).parent.absolute()
model_path = script_dir / "qwen3-4b-sentence-mil_f2.pt"

# map_location='cpu' is critical here so you don't 
# accidentally trigger an Out of Memory error on your GPU
checkpoint = torch.load(model_path, map_location='cpu')

print("--- Layer Shapes ---")
# No need for ['model_state_dict']!
for key, value in list(checkpoint.items())[:10]: 
    print(f"{key}: {value.shape}")