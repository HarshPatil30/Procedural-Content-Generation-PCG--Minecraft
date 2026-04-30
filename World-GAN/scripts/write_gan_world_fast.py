#!/usr/bin/env python3
"""
Write GAN-Generated World (FAST VERSION - Batched Chunk Writes)

This version batches all block changes per chunk and writes each chunk only once,
dramatically reducing I/O operations from ~40,000 to ~20.
"""

import sys
from pathlib import Path
import argparse
import shutil
import torch

# Add PyAnvilEditor to path and apply namespace fix
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import PyAnvilEditor.fix_anvil  # Must be first to patch namespace
from PyAnvilEditor.pyanvil import World
from PyAnvilEditor.mca_writer import write_chunk_to_region
import nbt


def set_block_in_chunk_fast(chunk, lx, ly, lz, block_name):
    """
    Set a block in chunk NBT data (without writing to disk yet).
    
    Args:
        chunk: Chunk object from anvil-parser
        lx, ly, lz: Local chunk coordinates (0-15, 0-255, 0-15)
        block_name: Namespaced block name (e.g. 'minecraft:stone')
    """
    section_y = ly // 16
    sections = chunk.data['Level']['Sections']
    
    # Find or create section
    section = None
    for sec in sections:
        if sec['Y'].value == section_y:
            section = sec
            break
    
    if section is None:
        # Create new section
        section = nbt.TAG_Compound()
        section.tags.append(nbt.TAG_Byte(name='Y', value=section_y))
        section.tags.append(nbt.TAG_List(name='Palette', type=nbt.TAG_Compound))
        section.tags.append(nbt.TAG_Long_Array(name='BlockStates'))
        sections.tags.append(section)
    
    # Get or initialize palette
    if 'Palette' not in section:
        section.tags.append(nbt.TAG_List(name='Palette', type=nbt.TAG_Compound))
    palette = section['Palette']
    
    # Find or add block in palette
    block_index = None
    for i, entry in enumerate(palette):
        if entry['Name'].value == block_name:
            block_index = i
            break
    
    if block_index is None:
        # Add new palette entry
        entry = nbt.TAG_Compound()
        entry.tags.append(nbt.TAG_String(name='Name', value=block_name))
        palette.tags.append(entry)
        block_index = len(palette) - 1
    
    # Calculate BlockStates array parameters
    palette_size = len(palette)
    bits_per_block = max(4, (palette_size - 1).bit_length())
    blocks_per_long = 64 // bits_per_block
    array_size = (4096 + blocks_per_long - 1) // blocks_per_long
    
    # Get or initialize BlockStates
    if 'BlockStates' not in section or len(section['BlockStates'].value) != array_size:
        section['BlockStates'] = nbt.TAG_Long_Array(name='BlockStates')
        section['BlockStates'].value = [0] * array_size
    
    blockstates = section['BlockStates'].value
    
    # Calculate position in BlockStates array
    block_pos = (ly % 16) * 256 + lz * 16 + lx
    long_index = block_pos // blocks_per_long
    bit_offset = (block_pos % blocks_per_long) * bits_per_block
    
    # Clear old value and set new value
    mask = (1 << bits_per_block) - 1
    blockstates[long_index] = (blockstates[long_index] & ~(mask << bit_offset)) | (block_index << bit_offset)


def main():
    parser = argparse.ArgumentParser(description='Write GAN-generated blocks to Minecraft world (FAST)')
    parser.add_argument('--sample-id', type=int, default=0, help='GAN sample ID to use (0-99)')
    parser.add_argument('--output-world', default='Gen_Try2', help='Output world name')
    parser.add_argument('--token-list', default=None, help='Path to token_list.pt (auto-detected if not specified)')
    args = parser.parse_args()
    
    print('=' * 60)
    print('World-GAN: Write GAN-Generated World (FAST VERSION)')
    print('=' * 60)
    print()
    
    # Paths
    sample_file = repo_root / 'output' / 'try2_examples' / 'torch_blockdata' / f'{args.sample_id}.pt'
    if args.token_list:
        token_file = Path(args.token_list)
    else:
        token_file = repo_root / 'input' / 'minecraft' / 'try2' / 'token_list.pt'
    
    if not sample_file.exists():
        print(f'ERROR: Sample file not found: {sample_file}')
        return 1
    
    if not token_file.exists():
        print(f'ERROR: Token list not found: {token_file}')
        return 1
    
    # Load GAN sample
    print(f'Loading sample {args.sample_id} from output/try2_examples/torch_blockdata...')
    sample_data = torch.load(sample_file, map_location='cpu', weights_only=False)
    
    # Extract blockdata from tuple (sample format: (blockdata, ?, ?))
    if isinstance(sample_data, tuple):
        gen_out = sample_data[0]
    else:
        gen_out = sample_data
    
    print(f'  Generated data shape: {gen_out.shape}')
    
    # Load token list
    token_list = torch.load(token_file, map_location='cpu', weights_only=False)
    print(f'  Token list length: {len(token_list)}')
    print()
    
    # Convert 5D tensor to 3D indices
    # Shape: (batch, channels, depth, height, width) -> (depth, height, width)
    if len(gen_out.shape) == 5:
        gen_out = gen_out[0]  # Remove batch dimension
    
    # Convert one-hot to indices
    indices = torch.argmax(gen_out, dim=0)  # Shape: (depth, height, width)
    
    # Prepare output world
    world_dir = repo_root / 'input' / 'minecraft' / args.output_world
    empty_world = repo_root / 'input' / 'minecraft' / 'Empty_World'
    
    print(f'Preparing output world: {world_dir}')
    if world_dir.exists():
        print(f'  Cleaning existing {args.output_world}...')
        shutil.rmtree(world_dir)
    
    print(f'  Creating {args.output_world} from Empty_World template...')
    shutil.copytree(empty_world, world_dir)
    
    # Clear region files
    region_dir = world_dir / 'region'
    print(f'  Clearing old region files...')
    if region_dir.exists():
        shutil.rmtree(region_dir)
    region_dir.mkdir(exist_ok=True)
    
    # Copy empty region template
    empty_region = empty_world / 'region'
    if empty_region.exists():
        print(f'  Copying fresh region template from Empty_World...')
        for mca_file in empty_region.glob('*.mca'):
            shutil.copy2(mca_file, region_dir)
    print()
    
    # Data cube dimensions
    depth, height, width = indices.shape
    print(f'Data cube dimensions: {depth}x{height}x{width}')
    
    # World coordinates (origin)
    start_x, start_y, start_z = 0, 64, 0
    print(f'World origin: ({start_x}, {start_y}, {start_z})')
    print()
    
    # Open world
    wrld = World(str(world_dir))
    
    # Group blocks by chunk
    print('Grouping blocks by chunk...')
    chunk_blocks = {}  # {(chunk_x, chunk_z): [(lx, ly, lz, block_name), ...]}
    
    total_blocks = 0
    for d in range(depth):
        for h in range(height):
            for w in range(width):
                block_idx = indices[d, h, w].item()
                
                # Skip air blocks
                if block_idx == 0:
                    continue
                
                # Map to block name
                if block_idx >= len(token_list):
                    continue
                block_name = token_list[block_idx]
                
                # Calculate world coordinates
                wx = start_x + w
                wy = start_y + h
                wz = start_z + d
                
                # Calculate chunk coordinates
                chunk_x = wx >> 4
                chunk_z = wz >> 4
                
                # Local chunk coordinates
                lx = wx & 0xF
                ly = wy
                lz = wz & 0xF
                
                # Add to chunk's block list
                chunk_key = (chunk_x, chunk_z)
                if chunk_key not in chunk_blocks:
                    chunk_blocks[chunk_key] = []
                
                chunk_blocks[chunk_key].append((lx, ly, lz, block_name))
                total_blocks += 1
    
    print(f'  Total non-air blocks: {total_blocks}')
    print(f'  Affected chunks: {len(chunk_blocks)}')
    print()
    
    # Write blocks chunk by chunk
    print('Writing blocks to world...')
    chunks_written = 0
    blocks_written = 0
    
    for (chunk_x, chunk_z), block_list in chunk_blocks.items():
        # Get chunk
        wx = chunk_x << 4
        wz = chunk_z << 4
        chunk, reg = wrld.get_chunk_for_world_coords(wx, wz)
        
        if chunk is None or reg is None:
            print(f'  WARNING: Could not load chunk ({chunk_x}, {chunk_z})')
            continue
        
        # Apply all blocks to this chunk
        for lx, ly, lz, block_name in block_list:
            set_block_in_chunk_fast(chunk, lx, ly, lz, block_name)
            blocks_written += 1
        
        # Write chunk ONCE after all blocks applied
        region_file = world_dir / 'region' / reg.file_path.name
        write_chunk_to_region(str(region_file), chunk)
        
        chunks_written += 1
        print(f'  [{chunks_written}/{len(chunk_blocks)}] Chunk ({chunk_x}, {chunk_z}): wrote {len(block_list)} blocks')
    
    print()
    print('=' * 60)
    print('COMPLETE!')
    print('=' * 60)
    print(f'Total blocks written: {blocks_written}')
    print(f'Total chunks modified: {chunks_written}')
    print(f'Output world: {world_dir}')
    print()
    print('Next step: Copy to Minecraft saves folder')
    print(f'  xcopy /E /I "{world_dir}" "%APPDATA%\\.minecraft\\saves\\{args.output_world}"')
    print()
    
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
