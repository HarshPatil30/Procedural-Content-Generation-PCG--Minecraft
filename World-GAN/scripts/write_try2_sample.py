"""Write a generated try2 GAN sample to a Minecraft world."""
import sys
sys.path.insert(0, 's:/CEVI/World-GAN')

import torch
import argparse
from pathlib import Path
import shutil

# Import anvil with namespace fix
import PyAnvilEditor.fix_anvil  # This automatically patches the namespace on import
from PyAnvilEditor.pyanvil import World, set_block_in_chunk
from anvil import Region

def write_sample_to_world(sample_id, output_world_name):
    """Write a generated sample to a Minecraft world."""
    
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
    
    for i in range(len(unique_blocks)):
        idx = unique_blocks[i].item()
        if idx < len(token_list):
            block_name = token_list[idx]
            count = (indices == idx).sum().item()
            block_counts[block_name] = count
    
    print(f"\nBlock distribution:")
    sorted_blocks = sorted(block_counts.items(), key=lambda x: x[1], reverse=True)
    for block, count in sorted_blocks[:15]:
        pct = 100 * count / (d*h*w)
        print(f"  {block}: {count:,} ({pct:.1f}%)")
    
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
    
    # Use template region files
    template_regions = list(Path('input/minecraft/Empty_World/region').glob('*.mca'))
    region_cache = {}
    
    for template_region_path in template_regions:
        dest_path = output_path / 'region' / template_region_path.name
        if not dest_path.exists():
            shutil.copy(template_region_path, dest_path)
    
    # Write blocks starting at origin (0, 60, 0)
    start_x, start_y, start_z = 0, 60, 0
    
    print(f"\nWriting blocks to world...")
    print(f"  Starting position: ({start_x}, {start_y}, {start_z})")
    
    blocks_written = 0
    chunks_modified = set()
    
    for dz in range(d):
        for dy in range(h):
            for dx in range(w):
                idx = indices[dz, dy, dx].item()
                if idx >= len(token_list):
                    continue
                
                block_name = token_list[idx]
                
                # Skip air blocks for efficiency
                if 'air' in block_name.lower():
                    continue
                
                # World coordinates
                wx = start_x + dx
                wy = start_y + dy
                wz = start_z + dz
                
                # Calculate region and chunk
                rx = wx >> 9
                rz = wz >> 9
                cx = (wx >> 4)
                cz = (wz >> 4)
                
                # Load region
                region_key = (rx, rz)
                if region_key not in region_cache:
                    region_file = output_path / 'region' / f'r.{rx}.{rz}.mca'
                    if region_file.exists():
                        region_cache[region_key] = Region.from_file(str(region_file))
                    else:
                        continue
                
                region = region_cache[region_key]
                
                # Get chunk
                try:
                    chunk = region.get_chunk(cx, cz)
                except:
                    continue
                
                # Calculate local coordinates
                lx = wx - (cx * 16)
                lz = wz - (cz * 16)
                
                # Set block
                try:
                    set_block_in_chunk(chunk, lx, wy, lz, block_name, region)
                    blocks_written += 1
                    chunks_modified.add((rx, rz, cx, cz))
                except Exception as e:
                    if blocks_written == 0:  # Only print first error
                        print(f"  Warning: Failed to set block at ({wx},{wy},{wz}): {e}")
    
    # Save all modified regions
    print(f"\nSaving {len(region_cache)} region files...")
    for (rx, rz), region in region_cache.items():
        region_file = output_path / 'region' / f'r.{rx}.{rz}.mca'
        try:
            region.save(str(region_file))
        except:
            pass
    
    print(f"\n{'='*70}")
    print(f"Sample written to world: {output_world_name}")
    print(f"{'='*70}")
    print(f"  Blocks written: {blocks_written:,}")
    print(f"  Chunks modified: {len(chunks_modified)}")
    print(f"  World location: {output_path}")
    print(f"\nOpen in Minecraft and teleport to: /tp @s {start_x} {start_y+5} {start_z}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Write generated try2 sample to Minecraft world')
    parser.add_argument('--sample_id', type=int, default=0, help='Sample ID to write (0-99)')
    parser.add_argument('--output_world', type=str, default='Gen_Try2_Sample', help='Output world name')
    
    args = parser.parse_args()
    write_sample_to_world(args.sample_id, args.output_world)
