#!/usr/bin/env python3
"""
Extract multiple diverse 60x40x60 samples from different biomes/locations in try2.
This gives the GAN variety: forests, mountains, caves, plains, villages, etc.
"""
import sys
from pathlib import Path
import torch
from tqdm import tqdm

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import PyAnvilEditor.fix_anvil  # noqa: F401
from anvil import Region


def extract_region_blocks(region_cache, center_x, center_y, center_z, width, height, depth):
    """Extract a region and return block names as list using native anvil methods."""
    start_x = center_x - width // 2
    start_y = center_y - height // 2
    start_z = center_z - depth // 2
    
    blocks = []
    print(f"    Extracting from ({start_x}, {start_y}, {start_z}) to ({start_x+width}, {start_y+height}, {start_z+depth})")
    
    for x in range(start_x, start_x + width):
        for y in range(start_y, start_y + height):
            for z in range(start_z, start_z + depth):
                try:
                    # Calculate region coordinates
                    rx = x >> 9  # x // 512
                    rz = z >> 9  # z // 512
                    region_key = (rx, rz)
                    
                    # Get or load region
                    if region_key not in region_cache:
                        region_file = repo_root / "input" / "minecraft" / "try2" / "region" / f"r.{rx}.{rz}.mca"
                        if region_file.exists():
                            region_cache[region_key] = Region.from_file(str(region_file))
                        else:
                            region_cache[region_key] = None
                    
                    region = region_cache[region_key]
                    if region is None:
                        blocks.append("minecraft:air")
                        continue
                    
                    # Get chunk coordinates (local to region)
                    cx = (x >> 4) & 31  # (x // 16) % 32
                    cz = (z >> 4) & 31  # (z // 16) % 32
                    
                    chunk = region.get_chunk(cx, cz)
                    if chunk is None:
                        blocks.append("minecraft:air")
                        continue
                    
                    # Get block (local to chunk)
                    lx = x & 15  # x % 16
                    lz = z & 15  # z % 16
                    
                    block = chunk.get_block(lx, y, lz)
                    block_str = str(block)
                    
                    # Extract block ID from "Block(minecraft:block_name)"
                    if 'Block(' in block_str:
                        block_id = block_str.replace('Block(', '').replace(')', '')
                    else:
                        block_id = "minecraft:air"
                    
                    blocks.append(block_id)
                    
                except Exception as e:
                    blocks.append("minecraft:air")
    
    return blocks


def main():
    print("=" * 70)
    print("Extract Diverse Samples from try2 World")
    print("=" * 70)
    
    # Region cache for efficient loading
    region_cache = {}
    
    # Diverse sample locations - SCANNED from actual try2 world
    # Format: (x, y, z, description)
    sample_locations = [
        # Known village area
        (-296, 70, 1080, "village_center"),
        (-304, 70, 1072, "village_house"),
        (-288, 68, 1056, "village_field"),
        (-320, 70, 1088, "village_path"),
        
        # Scanned valid locations from try2
        (-72, 70, -408, "coal_ore_area"),
        (-264, 70, -264, "stone_mountain_1"),
        (-200, 70, -232, "stone_area_2"),
        (-392, 70, 88, "snowy_region"),
        (-456, 70, 504, "stone_mountain_2"),
        (-200, 70, 472, "oak_forest"),
        (-24, 70, 520, "dirt_plains"),
        (-440, 70, 584, "stone_hills"),
        (-200, 70, 1528, "far_mountains"),
        (-8, 70, 1352, "grass_plains"),
        (-72, 70, 1448, "stone_valley"),
    ]
    
    print(f"\nExtracting {len(sample_locations)} diverse 60x40x60 samples...")
    print(f"Size: 60×40×60 = {60*40*60:,} blocks per sample\n")
    
    all_samples = []
    all_labels = []
    
    for i, (cx, cy, cz, description) in enumerate(sample_locations):
        print(f"[{i+1}/{len(sample_locations)}] {description}")
        print(f"    Center: ({cx}, {cy}, {cz})")
        
        blocks = extract_region_blocks(region_cache, cx, cy, cz, 60, 40, 60)
        
        # Count unique blocks for verification
        unique_blocks = set(blocks)
        air_count = blocks.count("minecraft:air")
        solid_count = len(blocks) - air_count
        
        print(f"    ✓ {len(blocks):,} blocks extracted")
        print(f"      Unique types: {len(unique_blocks)}, Solid: {solid_count:,}, Air: {air_count:,}\n")
        
        all_samples.append(blocks)
        all_labels.append(description)
    
    # Save samples
    output_dir = repo_root / "input" / "minecraft" / "diverse_dataset"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Saving samples...")
    print("=" * 70)
    
    # Save as list of raw block lists
    output_file = output_dir / "raw_blocks_list.pt"
    torch.save(all_samples, output_file)
    print(f"✓ Saved {len(all_samples)} samples to: {output_file}")
    
    # Save labels
    labels_file = output_dir / "sample_labels.pt"
    torch.save(all_labels, labels_file)
    print(f"✓ Saved labels to: {labels_file}")
    
    print("\n" + "=" * 70)
    print("Extraction Complete!")
    print("=" * 70)
    print(f"Total samples: {len(all_samples)}")
    print(f"Blocks per sample: {60*40*60:,}")
    print(f"Total blocks: {len(all_samples) * 60*40*60:,}")
    print("\nNext steps:")
    print("  1. Run: python scripts/tokenize_diverse.py")
    print("  2. Train with diverse data for natural variation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
