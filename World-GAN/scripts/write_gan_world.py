#!/usr/bin/env python3
"""Write GAN-generated blocks from try2 samples into a new Minecraft world."""
from pathlib import Path
import sys
import shutil
import argparse
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

# Fix broken anvil-parser namespace package
import PyAnvilEditor.fix_anvil

from PyAnvilEditor.pyanvil import World
from PyAnvilEditor.nbt_block_writer import set_block_in_chunk_nbt
import torch
from collections import defaultdict

# Paths
WORLD_ROOT = repo / 'input' / 'minecraft'
SOURCE_WORLD = 'Empty_World'  # Template world to copy structure from

def main():
    parser = argparse.ArgumentParser(description='Write GAN-generated world from samples')
    parser.add_argument('--samples-dir', '-s', default='output/try2_examples/torch_blockdata',
                        help='Directory containing generated .pt sample files')
    parser.add_argument('--sample-id', '-i', type=int, default=0,
                        help='Which sample ID to use (0-99)')
    parser.add_argument('--output-world', '-o', default='Gen_Try2',
                        help='Output world name under input/minecraft/')
    parser.add_argument('--token-list', '-t', default='input/minecraft/try2/token_list.pt',
                        help='Path to token_list.pt')
    args = parser.parse_args()
    
    print('=' * 60)
    print('World-GAN: Write GAN-Generated World')
    print('=' * 60)
    
    # Load sample
    samples_dir = repo / args.samples_dir
    sample_file = samples_dir / f'{args.sample_id}.pt'
    
    if not sample_file.exists():
        print(f'ERROR: Sample file not found: {sample_file}')
        return 1
    
    print(f'\nLoading sample {args.sample_id} from {samples_dir}...')
    sample_data = torch.load(sample_file)
    
    # Sample is a tuple: (blockdata_tensor, ?, ?)
    if isinstance(sample_data, tuple):
        gen_bdata = sample_data[0]
    else:
        gen_bdata = sample_data
    
    print(f'  Generated data shape: {gen_bdata.shape}')
    
    # Load token list
    token_path = repo / args.token_list
    if not token_path.exists():
        print(f'ERROR: Token list not found: {token_path}')
        return 1
    
    token_list = torch.load(token_path)
    print(f'  Token list length: {len(token_list)}')
    
    # Convert tokens to namespaced IDs
    namespaced_tokens = []
    for tok in token_list:
        if not tok.startswith('minecraft:'):
            tok = f'minecraft:{tok}'
        namespaced_tokens.append(tok)
    
    # Prepare output world
    gen_world_path = WORLD_ROOT / args.output_world
    source_world_path = WORLD_ROOT / SOURCE_WORLD
    
    print(f'\nPreparing output world: {gen_world_path}')
    
    # Create output world folder structure if it doesn't exist
    if not gen_world_path.exists():
        print(f'  Creating {args.output_world} from {SOURCE_WORLD} template...')
        shutil.copytree(source_world_path, gen_world_path)
    else:
        print(f'  {args.output_world} exists')
    
    # Clear old region files
    region_dir = gen_world_path / 'region'
    if region_dir.exists():
        print(f'  Clearing old region files in {region_dir}...')
        for mca_file in region_dir.glob('*.mca'):
            if mca_file.name != 'r.0.0.mca.backup':  # Keep backup
                mca_file.unlink()
                print(f'    Deleted {mca_file.name}')
    
    # Copy a fresh Empty_World region file as starting point
    source_region = source_world_path / 'region' / 'r.0.0.mca'
    dest_region = region_dir / 'r.0.0.mca'
    if source_region.exists():
        print(f'  Copying fresh region template from {SOURCE_WORLD}...')
        shutil.copy(source_region, dest_region)
    
    # Get data dimensions
    # gen_bdata shape: (batch, channels, depth, height, width) or (depth, height, width)
    if gen_bdata.ndim == 5:
        _, num_channels, D, H, W = gen_bdata.shape
        # Convert one-hot to indices
        gen_bdata = gen_bdata[0].argmax(0)  # Take first batch, argmax over channels
    elif gen_bdata.ndim == 3:
        D, H, W = gen_bdata.shape
    else:
        print(f'ERROR: Unexpected gen_bdata shape: {gen_bdata.shape}')
        return 1
    
    print(f'\nData cube dimensions: {D}x{H}x{W}')
    
    # Fixed origin (center of world)
    origin_x, origin_y, origin_z = 0, 64, 0
    print(f'World origin: ({origin_x}, {origin_y}, {origin_z})')
    
    # Write blocks
    print('\nWriting blocks to world...')
    block_counts = defaultdict(int)
    non_air_count = 0
    processed_chunks = set()
    
    with World(args.output_world, str(WORLD_ROOT)) as wrld:
        for d in range(D):
            for h in range(H):
                for w in range(W):
                    token_idx = int(gen_bdata[d, h, w].item())
                    if token_idx < 0 or token_idx >= len(namespaced_tokens):
                        continue
                    
                    block_name = namespaced_tokens[token_idx]
                    
                    # Skip air
                    if 'air' in block_name.lower():
                        continue
                    
                    # World coordinates
                    wx = origin_x + w
                    wy = origin_y + h
                    wz = origin_z + d
                    
                    # Get chunk and region
                    chunk, reg = wrld.get_chunk_for_world_coords(wx, wz)
                    if chunk is None or reg is None:
                        print(f'WARNING: Could not get chunk for ({wx}, {wy}, {wz})')
                        continue
                    
                    # Local coordinates within chunk
                    lx = wx - (chunk.x * 16)
                    lz = wz - (chunk.z * 16)
                    ly = wy
                    
                    # Determine region file path
                    rx = wx // 512 if wx >= 0 else -((-wx - 1) // 512) - 1
                    rz = wz // 512 if wz >= 0 else -((-wz - 1) // 512) - 1
                    region_file = region_dir / f'r.{rx}.{rz}.mca'
                    
                    # Write block
                    try:
                        set_block_in_chunk_nbt(chunk, lx, ly, lz, block_name, 
                                              region=reg, region_file_path=str(region_file))
                        print(f'[WRITE] ({wx:3d}, {wy:3d}, {wz:3d}) = {block_name}')
                        block_counts[block_name] += 1
                        non_air_count += 1
                        
                        # Track chunk for saving
                        chunk_key = (chunk.x, chunk.z, rx, rz)
                        processed_chunks.add(chunk_key)
                        
                    except Exception as e:
                        print(f'ERROR writing block at ({wx}, {wy}, {wz}): {e}')
    
    # Summary
    print('\n' + '=' * 60)
    print('SUMMARY')
    print('=' * 60)
    print(f'Total non-air blocks written: {non_air_count}')
    print(f'Total chunks processed: {len(processed_chunks)}')
    print(f'\nTop 10 block types:')
    sorted_blocks = sorted(block_counts.items(), key=lambda x: x[1], reverse=True)
    for block_name, count in sorted_blocks[:10]:
        print(f'  {block_name}: {count}')
    
    print(f'\nWorld written to: {gen_world_path}')
    print('\nTo play in Minecraft:')
    print(f'  xcopy /E /I "{gen_world_path}" "%APPDATA%\\.minecraft\\saves\\{args.output_world}"')
    print('Done!')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
