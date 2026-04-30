#!/usr/bin/env python3
"""Inspect anvil-parser Chunk/Section structure directly."""
from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

import anvil

WORLD = 'Gen_FixedTest'
WORLD_ROOT = repo / 'input' / 'minecraft'

def main():
    world_path = Path(WORLD_ROOT) / WORLD
    region_path = world_path / 'region'
    region_file = region_path / 'r.0.0.mca'
    
    if not region_file.exists():
        print(f'Region file not found: {region_file}')
        return 1
    
    print(f'Opening region: {region_file}')
    reg = anvil.Region.from_file(str(region_file))
    
    # Get chunk (1,1) = chunk coords for world (1,1)
    chunk_x, chunk_z = 0, 0
    print(f'Getting chunk ({chunk_x}, {chunk_z})')
    ch = reg.get_chunk(chunk_x, chunk_z)
    
    if ch is None:
        print('Chunk is None')
        return 2
    
    print(f'Chunk type: {type(ch)}')
    print(f'Chunk attributes: {[x for x in dir(ch) if not x.startswith("_") and not callable(getattr(ch, x))]}')
    
    # Check ch.data
    if hasattr(ch, 'data'):
        print(f'\nch.data type: {type(ch.data)}')
        print(f'ch.data.value: {ch.data.value}')
        
        # Try to access as dict-like
        print(f'ch.data get: {ch.data.get}')
        try:
            level = ch.data['Level']
            print(f'ch.data["Level"] exists: {level}')
            print(f'Level type: {type(level)}')
            if hasattr(level, 'value'):
                print(f'Level.value type: {type(level.value)}')
                if isinstance(level.value, dict):
                    print(f'Level.value keys: {list(level.value.keys())}')
        except Exception as e:
            print(f'Could not access ch.data["Level"]: {e}')
        
        # Try tags
        try:
            print(f'ch.data.tags: {ch.data.tags}')
        except Exception as e:
            print(f'Could not access ch.data.tags: {e}')
        
        # Try value with iter
        try:
            print(f'ch.data items: {list(ch.data.items())}')
        except Exception as e:
            print(f'Could not iter ch.data: {e}')
    
    # Try to access sections
    if hasattr(ch, 'sections'):
        print(f'\nch.sections type: {type(ch.sections)}')
        if isinstance(ch.sections, dict):
            print(f'ch.sections keys: {list(ch.sections.keys())}')
        elif isinstance(ch.sections, (list, tuple)):
            print(f'ch.sections length: {len(ch.sections)}')
    
    # Access Sections from NBT
    try:
        print(f'\n--- Accessing Sections from ch.data ---')
        sections_tag = ch.data['Sections']
        print(f'Sections tag type: {type(sections_tag)}')
        print(f'Sections tag value type: {type(sections_tag.value) if hasattr(sections_tag, "value") else "N/A"}')
        
        # Iterate over sections
        found_sec_4 = False
        for i, sec_tag in enumerate(sections_tag):
            if hasattr(sec_tag, '__getitem__'):
                y_tag = sec_tag.get('Y')
                y_val = y_tag.value if y_tag and hasattr(y_tag, 'value') else y_tag
                print(f'  Section {i}: Y={y_val}, type={type(sec_tag)}')
                if y_val == 4:
                    found_sec_4 = True
                    print(f'    --- Found Section Y=4 ---')
                    palette_tag = sec_tag.get('Palette')
                    if palette_tag:
                        print(f'    Palette: {palette_tag}')
                        if hasattr(palette_tag, 'value'):
                            print(f'    Palette.value: {palette_tag.value}')
                    blockstates_tag = sec_tag.get('BlockStates')
                    if blockstates_tag:
                        bs_list = blockstates_tag.value if hasattr(blockstates_tag, 'value') else blockstates_tag
                        print(f'    BlockStates length: {len(bs_list) if hasattr(bs_list, "__len__") else "N/A"}')
                        if hasattr(bs_list, '__getitem__'):
                            print(f'    BlockStates first few: {[bs_list[i] for i in range(min(5, len(bs_list)))] if hasattr(bs_list, "__len__") else "N/A"}')
        
        if not found_sec_4:
            print(f'  --- Section Y=4 NOT FOUND ---')
            print(f'  Need to create it to write at y=64')
    except Exception as e:
        print(f'Could not access Sections: {e}')
        import traceback
        traceback.print_exc()
    
    # Try to read a block
    print('\nTrying to read block at (1, 64, 1):')
    try:
        b = ch.get_block(1, 64, 1)
        print(f'Block type: {type(b)}')
        if hasattr(b, 'namespaced'):
            print(f'Block namespaced: {b.namespaced}')
        if hasattr(b, 'id'):
            print(f'Block id: {b.id}')
        print(f'Block str: {str(b)}')
    except Exception as e:
        print(f'get_block failed: {e}')
        import traceback
        traceback.print_exc()
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
