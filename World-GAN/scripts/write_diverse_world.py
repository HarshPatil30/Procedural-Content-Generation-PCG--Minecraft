"""
Write diverse GAN samples to Minecraft worlds.
"""
import argparse
from pathlib import Path
import sys
import shutil
from collections import defaultdict

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import torch
import PyAnvilEditor.fix_anvil  # noqa
from PyAnvilEditor.nbt_block_writer_batch import set_blocks_in_chunk_batch
from anvil import Region


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_id', type=int, default=0, help='Sample ID to write (0-9)')
    parser.add_argument('--output_world', type=str, default='Diverse_World', help='Output world name')
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("=" * 70)
    print("Write Diverse GAN Sample to Minecraft World")
    print("=" * 70)
    
    # Load sample and tokens
    sample_dir = repo_root / "output" / "diverse_dataset_examples"
    sample = torch.load(sample_dir / f"sample_{args.sample_id}.pt")
    tokens = torch.load(sample_dir / "token_list.pt")
    
    print(f"\nLoaded sample {args.sample_id}")
    print(f"  Shape: {sample.shape}")
    print(f"  Tokens: {len(tokens)}")
    print(f"  Unique blocks in sample: {len(sample.unique())}")
    
    # Convert indices to block names
    depth, height, width = sample.shape
    print(f"\nConverting {depth}×{height}×{width} = {depth*height*width:,} blocks...")
    
    blocks_by_chunk = defaultdict(list)
    origin_x, origin_y, origin_z = 0, 64, 0
    
    non_air = 0
    for d in range(depth):
        for h in range(height):
            for w in range(width):
                idx = sample[d, h, w].item()
                block_name = tokens[idx]
                
                if 'air' not in block_name.lower():
                    non_air += 1
                    wx = origin_x + d
                    wy = origin_y + h
                    wz = origin_z + w
                    
                    cx, cz = wx >> 4, wz >> 4
                    blocks_by_chunk[(cx, cz)].append((wx, wy, wz, block_name))
    
    print(f"  Non-air blocks: {non_air:,}")
    print(f"  Chunks to modify: {len(blocks_by_chunk)}")
    
    # Prepare output world
    world_dir = repo_root / "input" / "minecraft" / args.output_world
    template_world = repo_root / "input" / "minecraft" / "Empty_World"
    
    print(f"\nPreparing world: {args.output_world}")
    if world_dir.exists():
        shutil.rmtree(world_dir)
    shutil.copytree(template_world, world_dir)
    
    # Clear region files
    region_dir = world_dir / "region"
    for f in region_dir.glob("*.mca"):
        f.unlink()
    
    print(f"\nWriting blocks to world...")
    
    total_written = 0
    for i, ((cx, cz), block_list) in enumerate(blocks_by_chunk.items(), 1):
        print(f"  [{i}/{len(blocks_by_chunk)}] Chunk ({cx:3}, {cz:3}) - {len(block_list):,} blocks")
        
        # Get region file
        rx, rz = cx >> 5, cz >> 5
        region_file = region_dir / f"r.{rx}.{rz}.mca"
        
        # Copy template region if doesn't exist
        if not region_file.exists():
            template_region = template_world / "region" / f"r.{rx}.{rz}.mca"
            if template_region.exists():
                shutil.copy(template_region, region_file)
        
        # Load region
        region = Region.from_file(str(region_file))
        
        # Get chunk
        local_cx, local_cz = cx & 31, cz & 31
        chunk = region.get_chunk(local_cx, local_cz)
        
        if chunk:
            # Write blocks
            set_blocks_in_chunk_batch(chunk, block_list, region, str(region_file))
            total_written += len(block_list)
    
    print(f"\n✓ Wrote {total_written:,} blocks to {len(blocks_by_chunk)} chunks")
    print(f"\n✓ World saved to: {world_dir}")
    print(f"\nTo play in Minecraft:")
    print(f'  xcopy /E /I "{world_dir}" "%APPDATA%\\.minecraft\\saves\\{args.output_world}"')


if __name__ == "__main__":
    main()
