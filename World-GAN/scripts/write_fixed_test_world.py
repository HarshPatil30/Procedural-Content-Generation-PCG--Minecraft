#!/usr/bin/env python3
"""Write generated blocks from fixed_test dataset into a new Minecraft world."""
from pathlib import Path
import sys
import shutil
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
GEN_WORLD = 'Gen_FixedTest'   # Output world
DATA_DIR = WORLD_ROOT / 'fixed_test'

def main():
    print('=' * 60)
    print('World-GAN: Write Generated World from fixed_test')
    print('=' * 60)
    
    # Load data
    print(f'\nLoading data from {DATA_DIR}...')
    real_bdata = torch.load(DATA_DIR / 'real_bdata.pt')
    token_list = torch.load(DATA_DIR / 'token_list.pt')
    
    print(f'  real_bdata shape: {real_bdata.shape}')
    print(f'  token_list length: {len(token_list)}')
    
    # Convert tokens to namespaced IDs
    namespaced_tokens = []
    for tok in token_list:
        if not tok.startswith('minecraft:'):
            tok = f'minecraft:{tok}'
        namespaced_tokens.append(tok)
    
    # Prepare output world
    gen_world_path = WORLD_ROOT / GEN_WORLD
    source_world_path = WORLD_ROOT / SOURCE_WORLD
    
    print(f'\nPreparing output world: {gen_world_path}')
    
    # Create Gen_FixedTest folder structure if it doesn't exist
    if not gen_world_path.exists():
        print(f'  Creating {GEN_WORLD} from {SOURCE_WORLD} template...')
        shutil.copytree(source_world_path, gen_world_path)
    else:
        print(f'  {GEN_WORLD} exists')
    
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
    # real_bdata shape: (batch, channels, depth, height, width) or (depth, height, width)
    if real_bdata.ndim == 5:
        _, num_channels, D, H, W = real_bdata.shape
        # Convert one-hot to indices
        real_bdata = real_bdata[0].argmax(0)  # Take first batch, argmax over channels
    elif real_bdata.ndim == 3:
        D, H, W = real_bdata.shape
    else:
        raise ValueError(f"Unexpected real_bdata shape: {real_bdata.shape}")
    
    print(f'\nData cube dimensions: {D}x{H}x{W}')
    
    # Fixed origin (center of world)
    origin_x, origin_y, origin_z = 0, 64, 0
    print(f'World origin: ({origin_x}, {origin_y}, {origin_z})')
    
    # Write blocks
    print('\nWriting blocks to world...')
    block_counts = defaultdict(int)
    non_air_count = 0
    processed_chunks = set()
    
    with World(GEN_WORLD, str(WORLD_ROOT)) as wrld:
        for d in range(D):
            for h in range(H):
                for w in range(W):
                    token_idx = int(real_bdata[d, h, w].item())
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
    print('Done!')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
