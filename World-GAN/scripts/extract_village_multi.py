"""
Extract multiple diverse 60x40x60 samples from the try2 world.
This gives the GAN variety to learn from.
"""
from pathlib import Path
import sys
import torch

sys.path.insert(0, str(Path(__file__).parent.parent))
from PyAnvilEditor.fix_anvil import *
from PyAnvilEditor.pyanvil import World

def extract_region(world, center_x, center_y, center_z, size_x, size_y, size_z):
    """Extract a region and return blocks as list."""
    blocks = []
    
    start_x = center_x - size_x // 2
    start_y = center_y - size_y // 2
    start_z = center_z - size_z // 2
    
    for x in range(start_x, start_x + size_x):
        for y in range(start_y, start_y + size_y):
            for z in range(start_z, start_z + size_z):
                try:
                    block = world.get_block_at(x, y, z)
                    block_name = f"minecraft:{block.id}" if hasattr(block, 'id') else str(block)
                    blocks.append(block_name)
                except:
                    blocks.append("minecraft:air")
    
    return torch.tensor([blocks[i] for i in range(len(blocks))], dtype=torch.object)

# Multiple sample locations across the village
sample_locations = [
    (-296, 70, 1080, "village_center"),
    (-304, 70, 1072, "village_house_1"),
    (-288, 70, 1056, "village_house_2"),
    (-352, 70, 1056, "village_field"),
    (-320, 70, 1088, "village_path"),
]

world_path = Path("input/minecraft/try2")
world = World(str(world_path))

output_dir = Path("input/minecraft/village_multi_dataset")
output_dir.mkdir(exist_ok=True)

print(f"Extracting {len(sample_locations)} diverse samples...\n")

all_samples = []
for i, (cx, cy, cz, name) in enumerate(sample_locations):
    print(f"[{i+1}/{len(sample_locations)}] Extracting {name} at ({cx}, {cy}, {cz})...")
    blocks = extract_region(world, cx, cy, cz, 60, 40, 60)
    all_samples.append(blocks)
    print(f"  ✓ Extracted {len(blocks)} blocks")

# Save as list of samples
output_file = output_dir / "raw_blocks_multi.pt"
torch.save(all_samples, output_file)

print(f"\n✓ Saved {len(all_samples)} samples to: {output_file}")
print("\nNext: Tokenize with scripts/tokenize_village_multi.py")
