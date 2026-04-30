#!/usr/bin/env python3
"""
Extract a village region from the try2 Minecraft world.
Uses direct region file access to bypass World class issues.
"""
import sys
from pathlib import Path
import torch

# Add parent directory to path for imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Fix anvil namespace before importing
import PyAnvilEditor.fix_anvil  # noqa: F401
import anvil


def get_region_and_local_coords(world_x, world_z):
    """Get region file and local chunk coordinates within that region."""
    chunk_x = world_x >> 4  # Divide by 16
    chunk_z = world_z >> 4
    
    region_x = chunk_x >> 5  # Divide by 32
    region_z = chunk_z >> 5
    
    local_chunk_x = chunk_x & 31  # Modulo 32
    local_chunk_z = chunk_z & 31
    
    return region_x, region_z, local_chunk_x, local_chunk_z


def extract_village_region(world_path, center_coords, size, output_path):
    """
    Extract a region of blocks from a Minecraft world.
    
    Args:
        world_path: Path to Minecraft world folder
        center_coords: (x, y, z) center coordinates
        size: (width_x, height_y, width_z) dimensions of extraction
        output_path: Where to save raw_blocks.pt
    """
    cx, cy, cz = center_coords
    wx, hy, wz = size
    
    # Calculate bounding box
    x_start = cx - wx // 2
    x_end = x_start + wx
    y_start = cy - hy // 2
    y_end = y_start + hy
    z_start = cz - wz // 2
    z_end = z_start + wz
    
    print("="*60)
    print("World-GAN: Extract Village Region (Direct Region Access)")
    print("="*60)
    print(f"\nWorld: {world_path}")
    print(f"Center: ({cx}, {cy}, {cz})")
    print(f"Size: {wx}x{hy}x{wz} blocks")
    print(f"\nBounding box:")
    print(f"  X: {x_start} to {x_end}")
    print(f"  Y: {y_start} to {y_end}")
    print(f"  Z: {z_start} to {z_end}")
    print(f"\nTotal blocks to extract: {wx * hy * wz:,}")
    
    # Cache for region files
    region_cache = {}
    region_dir = world_path / "region"
    
    # Initialize 3D array to store block names
    # Shape: (width_x, height_y, width_z)
    blocks = []
    
    print("\nExtracting blocks...")
    
    for x in range(x_start, x_end):
        x_slice = []
        for y in range(y_start, y_end):
            y_slice = []
            for z in range(z_start, z_end):
                try:
                    # Get region file and local chunk coords
                    rx, rz, lcx, lcz = get_region_and_local_coords(x, z)
                    region_key = (rx, rz)
                    
                    # Load region file if not cached
                    if region_key not in region_cache:
                        region_file = region_dir / f"r.{rx}.{rz}.mca"
                        if region_file.exists():
                            try:
                                region_cache[region_key] = anvil.Region.from_file(str(region_file))
                            except Exception:
                                region_cache[region_key] = None
                        else:
                            region_cache[region_key] = None
                    
                    region = region_cache[region_key]
                    
                    if region is None:
                        block_name = "minecraft:air"
                    else:
                        # Try to get chunk
                        try:
                            chunk = region.get_chunk(lcx, lcz)
                            if chunk is None:
                                block_name = "minecraft:air"
                            else:
                                # Get local coordinates within chunk
                                lx = x & 15  # Modulo 16
                                lz = z & 15
                                block = chunk.get_block(lx, y, lz)
                                
                                # Extract block name
                                if hasattr(block, 'id'):
                                    block_name = str(block.id)
                                elif hasattr(block, 'name'):
                                    block_name = str(block.name)
                                else:
                                    block_name = str(block)
                                
                                # Ensure namespaced format
                                if ':' not in block_name:
                                    block_name = f"minecraft:{block_name}"
                        except Exception:
                            block_name = "minecraft:air"
                except Exception:
                    # Default to air if any error
                    block_name = "minecraft:air"
                
                y_slice.append(block_name)
            x_slice.append(y_slice)
        
        blocks.append(x_slice)
        
        # Progress indicator
        progress = ((x - x_start + 1) / wx) * 100
        if (x - x_start + 1) % 10 == 0 or x == x_end - 1:
            print(f"  Progress: {progress:.1f}% ({x - x_start + 1}/{wx} X-slices)")
    
    print(f"\n✓ Extracted {wx * hy * wz:,} blocks")
    
    # Save as PyTorch tensor
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(blocks, str(output_path))
    print(f"✓ Saved to: {output_path}")
    
    # Show block statistics
    flat_blocks = []
    def flatten(lst):
        for item in lst:
            if isinstance(item, list):
                flatten(item)
            else:
                flat_blocks.append(item)
    flatten(blocks)
    
    unique_blocks = sorted(set(flat_blocks))
    print(f"\n✓ Found {len(unique_blocks)} unique block types:")
    for block in unique_blocks[:10]:  # Show first 10
        count = flat_blocks.count(block)
        print(f"  - {block}: {count} blocks")
    if len(unique_blocks) > 10:
        print(f"  ... and {len(unique_blocks) - 10} more")
    
    print("\n" + "="*60)
    print("Extraction complete!")
    print("="*60)


if __name__ == "__main__":
    # Configuration
    center_x = -340
    center_y = 62
    center_z = 1056
    
    # Size of region to extract
    width_x = 60    # X-axis (east-west)
    height_y = 40   # Y-axis (vertical)
    width_z = 60    # Z-axis (north-south)
    
    # Paths
    world_path = repo_root / "input" / "minecraft" / "try2"
    output_path = repo_root / "input" / "minecraft" / "village_dataset" / "raw_blocks.pt"
    
    extract_village_region(
        world_path=world_path,
        center_coords=(center_x, center_y, center_z),
        size=(width_x, height_y, width_z),
        output_path=output_path
    )
