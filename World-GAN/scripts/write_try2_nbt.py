"""Write generated try2 samples to Minecraft worlds using NBT writer."""
import sys
sys.path.insert(0, 's:/CEVI/World-GAN')

import torch
import argparse
from pathlib import Path
import shutil

from PyAnvilEditor.nbt_block_writer_batch import set_blocks_in_chunk_batch
from nbt import nbt
import os

def write_sample_to_world(sample_id, output_world_name):
    """Write a generated sample to a Minecraft world using NBT writer."""
    
    # Load the sample
    sample_path = Path(f'output/try2_examples/torch_blockdata/{sample_id}.pt')
    if not sample_path.exists():
        print(f"Error: Sample {sample_id} not found at {sample_path}")
        return
    
    print(f"Loading sample {sample_id}...")
    sample_data = torch.load(sample_path, weights_only=True)
    
    # Sample is a tuple (rendered_level, token_list, opt)
    if isinstance(sample_data, tuple):
        sample = sample_data[0]  # Get the rendered level
        print(f"  Loaded tuple with {len(sample_data)} items")
    else:
        sample = sample_data
    
    print(f"  Sample shape: {sample.shape}")
    
    # Remove batch dimension if present
    if sample.dim() == 5:
        sample = sample.squeeze(0)  # [C, D, H, W]
    
    print(f"  After squeeze: {sample.shape}")
    
    # Load token list
    token_list = torch.load('input/minecraft/try2/token_list.pt', weights_only=False)
    print(f"  Token list: {len(token_list)} blocks")
    
    # Convert from one-hot to indices
    indices = torch.argmax(sample, dim=0)  # [D, H, W]
    print(f"  Indices shape: {indices.shape}")
    
    # Count unique blocks
    unique_blocks = torch.unique(indices)
    print(f"  Unique block indices: {len(unique_blocks)}")
    
    # Convert indices to block names
    block_counts = {}
    d, h, w = indices.shape
    print(f"\nConverting {d}×{h}×{w} = {d*h*w:,} blocks...")
    
    blocks_to_write = []
    
    for dz in range(d):
        for dy in range(h):
            for dx in range(w):
                idx = indices[dz, dy, dx].item()
                if idx >= len(token_list):
                    continue
                
                block_name = token_list[idx]
                
                # Count for stats
                if block_name not in block_counts:
                    block_counts[block_name] = 0
                block_counts[block_name] += 1
                
                # Skip air blocks for efficiency
                if 'air' in block_name.lower():
                    continue
                
                # World coordinates (start at 0, 60, 0)
                wx = dx
                wy = 60 + dy
                wz = dz
                
                blocks_to_write.append((wx, wy, wz, block_name))
    
    print(f"\nBlock distribution:")
    sorted_blocks = sorted(block_counts.items(), key=lambda x: x[1], reverse=True)
    for block, count in sorted_blocks[:15]:
        pct = 100 * count / (d*h*w)
        print(f"  {block}: {count:,} ({pct:.1f}%)")
    
    print(f"\nNon-air blocks to write: {len(blocks_to_write):,}")
    
    # Prepare output world
    output_path = Path('input/minecraft') / output_world_name
    print(f"\nPreparing world: {output_world_name}")
    
    # Copy template from Empty_World if it doesn't exist
    if not output_path.exists():
        template = Path('input/minecraft/Empty_World')
        if template.exists():
            shutil.copytree(template, output_path)
            print(f"  Copied template from Empty_World")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / 'region').mkdir(exist_ok=True)
    
    # Write blocks using NBT writer
    print(f"\nGrouping blocks by chunk...")
    chunk_blocks = {}  # (cx, cz) -> [(lx, ly, lz, block_name), ...]
    
    for wx, wy, wz, block_name in blocks_to_write:
        cx = wx >> 4
        cz = wz >> 4
        lx = wx & 15
        lz = wz & 15
        
        key = (cx, cz)
        if key not in chunk_blocks:
            chunk_blocks[key] = []
        chunk_blocks[key].append((lx, wy, lz, block_name))
    
    print(f"  Total chunks to modify: {len(chunk_blocks)}")
    
    # Import anvil for reading region files
    import PyAnvilEditor.fix_anvil
    from anvil import Region
    
    print(f"\nWriting blocks...")
    chunks_written = 0
    for (cx, cz), block_list in chunk_blocks.items():
        rx = cx >> 5
        rz = cz >> 5
        
        region_file = output_path / 'region' / f'r.{rx}.{rz}.mca'
        if not region_file.exists():
            print(f"  Skipping chunk ({cx},{cz}) - region file doesn't exist")
            continue
        
        try:
            # Load region
            region = Region.from_file(str(region_file))
            
            # Get chunk
            chunk = region.get_chunk(cx, cz)
            
            # Write blocks to chunk
            set_blocks_in_chunk_batch(chunk, block_list, region, str(region_file))
            
            chunks_written += 1
            if chunks_written % 10 == 0:
                print(f"  Progress: {chunks_written}/{len(chunk_blocks)} chunks...")
        
        except Exception as e:
            print(f"  Error writing chunk ({cx},{cz}): {e}")
            continue
    
    print(f"  Chunks written: {chunks_written}")
    
    print(f"\n{'='*70}")
    print(f"Sample written to world: {output_world_name}")
    print(f"{'='*70}")
    print(f"  World location: {output_path}")
    print(f"  Blocks written: {len(blocks_to_write):,}")
    print(f"  Chunks modified: {chunks_written}")
    print(f"\nOpen in Minecraft and teleport to: /tp @s 20 70 20")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Write generated try2 sample to Minecraft world')
    parser.add_argument('--sample_id', type=int, default=0, help='Sample ID to write (0-99)')
    parser.add_argument('--output_world', type=str, default='Gen_Try2_NBT', help='Output world name')
    
    args = parser.parse_args()
    write_sample_to_world(args.sample_id, args.output_world)
