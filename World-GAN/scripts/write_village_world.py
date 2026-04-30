#!/usr/bin/env python3
"""
Write a GAN-generated village sample to a Minecraft world.
Uses the optimized MCA writer with proper chunking.
"""
import sys
import shutil
from pathlib import Path
from collections import defaultdict
import argparse
import torch

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Fix anvil namespace
import PyAnvilEditor.fix_anvil  # noqa: F401
from PyAnvilEditor.pyanvil import World
from PyAnvilEditor.nbt_block_writer_batch import set_blocks_in_chunk_batch


def write_village_world(sample_id, output_world_name, token_list_path, sample_path):
    """
    Write a GAN-generated village sample to a Minecraft world.
    
    Args:
        sample_id: Which sample to write (0-9)
        output_world_name: Name of output world
        token_list_path: Path to token_list.pt
        sample_path: Path to the sample .pt file
    """
    print("="*60)
    print("World-GAN: Write Village World")
    print("="*60)
    
    # Load token list
    print(f"\nLoading token list: {token_list_path}")
    token_list = torch.load(str(token_list_path))
    print(f"  Tokens: {len(token_list)}")
    
    # Load GAN sample
    print(f"\nLoading sample {sample_id}: {sample_path}")
    sample_data = torch.load(str(sample_path))
    
    # Extract blockdata from tuple
    if isinstance(sample_data, tuple):
        blockdata = sample_data[0]
    else:
        blockdata = sample_data
    
    print(f"  Sample shape: {blockdata.shape}")
    
    # Remove batch dimension if present
    if blockdata.dim() == 5:
        blockdata = blockdata[0]  # (batch, channels, D, H, W) -> (channels, D, H, W)
    
    print(f"  Working shape: {blockdata.shape}")
    
    # Convert from one-hot to indices
    print(f"\nLoading sample...")
    # Check if it's already indices or one-hot
    if blockdata.dim() == 3:
        # Already converted to indices (D, H, W)
        print(f"  Format: Block indices (D, H, W)")
        indices = blockdata
    elif blockdata.dim() == 4:
        # One-hot format (C, D, H, W) - convert to indices
        print(f"  Format: One-hot encoded (C, D, H, W)")
        indices = blockdata.argmax(dim=0)
    else:
        raise ValueError(f"Unexpected sample shape: {blockdata.shape}")
    
    print(f"  Indices shape: {indices.shape}")
    print(f"  Unique indices: {indices.unique().tolist()}")
    
    # Prepare output world
    world_dir = repo_root / "input" / "minecraft" / output_world_name
    template_world = repo_root / "input" / "minecraft" / "Empty_World"  # Use Empty_World for blank slate
    
    print(f"\nPreparing output world: {world_dir}")
    
    # Copy from template
    if world_dir.exists():
        print("  Removing old world...")
        shutil.rmtree(world_dir)
    
    print(f"  Copying from {template_world.name} template...")
    shutil.copytree(template_world, world_dir)
    
    # Clear region files (keep structure but remove content)
    region_dir = world_dir / "region"
    print(f"  Clearing region files...")
    for region_file in region_dir.glob("*.mca"):
        region_file.unlink()
    
    # Copy minimal region files from try2 for structure
    template_region_dir = template_world / "region"
    # Just copy one region file for structure reference
    source_region = template_region_dir / "r.0.0.mca"
    if source_region.exists():
        shutil.copy2(source_region, region_dir / "r.0.0.mca")
    
    print("  ✓ World prepared")
    
    # Get dimensions
    depth, height, width = indices.shape
    print(f"\nData cube dimensions: {depth}x{height}x{width}")
    
    # World origin (center the structure)
    origin_x = 0
    origin_y = 64
    origin_z = 0
    
    print(f"World origin: ({origin_x}, {origin_y}, {origin_z})")
    
    # Group blocks by chunk to minimize I/O
    print("\nGrouping blocks by chunk...")
    chunk_blocks = defaultdict(list)  # {(chunk_x, chunk_z): [(wx, wy, wz, block_name), ...]}
    
    non_air_count = 0
    
    for d in range(depth):
        for h in range(height):
            for w in range(width):
                idx = indices[d, h, w].item()
                
                # Skip air blocks
                if idx >= len(token_list):
                    continue
                    
                block_name = token_list[idx]
                if block_name == "minecraft:air":
                    continue
                
                # Calculate world coordinates
                wx = origin_x + w
                wy = origin_y + h
                wz = origin_z + d
                
                # Calculate chunk coordinates
                chunk_x = wx >> 4  # Divide by 16
                chunk_z = wz >> 4
                
                chunk_blocks[(chunk_x, chunk_z)].append((wx, wy, wz, block_name))
                non_air_count += 1
    
    print(f"  Non-air blocks: {non_air_count:,}")
    print(f"  Chunks to modify: {len(chunk_blocks)}")
    
    # Write blocks chunk by chunk
    print("\nWriting blocks to world...")
    
    with World(output_world_name, str(world_dir.parent)) as wrld:
        total_chunks = len(chunk_blocks)
        
        for chunk_idx, ((chunk_x, chunk_z), blocks) in enumerate(chunk_blocks.items(), 1):
            print(f"  [{chunk_idx}/{total_chunks}] Chunk ({chunk_x:3d}, {chunk_z:3d}) - {len(blocks):,} blocks")
            
            # Get chunk once
            chunk, reg = wrld.get_chunk_for_world_coords(chunk_x * 16, chunk_z * 16)
            
            if chunk is None:
                print(f"  WARNING: Could not load chunk ({chunk_x}, {chunk_z})")
                continue
            
            # Get region file path
            region_x = chunk_x >> 5  # Divide by 32
            region_z = chunk_z >> 5
            region_file = world_dir / "region" / f"r.{region_x}.{region_z}.mca"
            
            # Convert world coords to chunk-local coords and prepare batch
            chunk_local_blocks = []
            for wx, wy, wz, block_name in blocks:
                lx = wx & 15  # Modulo 16
                lz = wz & 15
                chunk_local_blocks.append((lx, wy, lz, block_name))
            
            # Write all blocks in this chunk at once
            try:
                set_blocks_in_chunk_batch(
                    chunk=chunk,
                    block_list=chunk_local_blocks,
                    region=reg,
                    region_file_path=str(region_file)
                )
            except Exception as e:
                print(f"  ERROR writing chunk ({chunk_x}, {chunk_z}): {e}")
    
    print(f"\n✓ Wrote {non_air_count:,} blocks to {total_chunks} chunks")
    
    # Summary
    print("\n" + "="*60)
    print("World generation complete!")
    print("="*60)
    print(f"\nWorld location: {world_dir}")
    print(f"World name: {output_world_name}")
    print(f"\nBlock statistics:")
    
    # Count blocks by type
    block_counts = defaultdict(int)
    for blocks in chunk_blocks.values():
        for _, _, _, block_name in blocks:
            block_counts[block_name] += 1
    
    for block_name, count in sorted(block_counts.items(), key=lambda x: -x[1])[:10]:
        pct = (count / non_air_count) * 100
        print(f"  {block_name:30s}: {count:6,} ({pct:5.2f}%)")
    
    if len(block_counts) > 10:
        print(f"  ... and {len(block_counts) - 10} more block types")
    
    print(f"\nTo play this world in Minecraft, run:")
    print(f'  xcopy /E /I "S:\\CEVI\\World-GAN\\input\\minecraft\\{output_world_name}" "%APPDATA%\\.minecraft\\saves\\{output_world_name}"')


def main():
    parser = argparse.ArgumentParser(description='Write GAN village sample to Minecraft world')
    parser.add_argument('--sample-id', type=int, default=0, help='Sample ID to write (default: 0)')
    parser.add_argument('--output-world', type=str, default='Gen_VillageGAN', help='Output world name')
    args = parser.parse_args()
    
    # Paths
    dataset_dir = repo_root / "input" / "minecraft" / "village_dataset"
    token_list_path = dataset_dir / "token_list.pt"
    
    samples_dir = repo_root / "output" / "village_dataset_examples" / "torch_blockdata" / "torch_blockdata"
    sample_path = samples_dir / f"{args.sample_id}_sc3.pt"
    
    # Validate inputs
    if not token_list_path.exists():
        print(f"ERROR: token_list.pt not found at: {token_list_path}")
        print("Please run scripts/tokenize_village.py first!")
        return 1
    
    if not sample_path.exists():
        print(f"ERROR: Sample {args.sample_id} not found at: {sample_path}")
        print("Please run scripts/generate_village_samples.py first!")
        return 1
    
    # Write world
    write_village_world(
        sample_id=args.sample_id,
        output_world_name=args.output_world,
        token_list_path=token_list_path,
        sample_path=sample_path
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
