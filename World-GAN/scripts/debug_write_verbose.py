#!/usr/bin/env python3
"""Debug verbose: write one block and inspect the internals."""
from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from PyAnvilEditor.pyanvil import World, set_block_in_chunk
import anvil

WORLD = 'Gen_FixedTest'
WORLD_ROOT = repo / 'input' / 'minecraft'

def main():
    tx, ty, tz = 1, 64, 1
    print(f'Debug: write single block at ({tx}, {ty}, {tz})')
    
    with World(WORLD, str(WORLD_ROOT)) as wrld:
        chunk, reg = wrld.get_chunk_for_world_coords(tx, tz)
        if chunk is None or reg is None:
            print('Region/chunk not available')
            return 2

        # Inspect section before write
        sec_idx = ty // 16
        print(f'Section index: {sec_idx}')
        sec = None
        if hasattr(chunk, 'sections'):
            print(f'chunk.sections type: {type(chunk.sections)}')
            if isinstance(chunk.sections, dict):
                sec = chunk.sections.get(sec_idx)
            elif isinstance(chunk.sections, list):
                if sec_idx < len(chunk.sections):
                    sec = chunk.sections[sec_idx]
        
        if sec is None and hasattr(chunk, 'get_section'):
            try:
                sec = chunk.get_section(sec_idx)
                print('Got section via get_section()')
            except Exception as e:
                print(f'get_section failed: {e}')
        
        if sec is not None:
            print(f'Section type: {type(sec)}')
            print(f'Section has value attr: {hasattr(sec, "value")}')
            print(f'Section is dict: {isinstance(sec, dict)}')
            if isinstance(sec, dict):
                print(f'sec dict keys: {list(sec.keys())}')
                print(f'Palette before (dict): {sec.get("Palette", [])[:3]}...')
                print(f'BlockStates before (dict): {sec.get("BlockStates", [])[:3]}...')
            elif hasattr(sec, 'value'):
                val = sec.value
                print(f'sec.value type: {type(val)}')
                print(f'sec.value is dict: {isinstance(val, dict)}')
                if isinstance(val, dict):
                    print(f'sec.value keys: {list(val.keys())}')
                    print(f'Palette before: {val.get("Palette", [])[:3]}...')
                    print(f'BlockStates before: {val.get("BlockStates", [])[:3]}...')
                else:
                    print(f'sec.value is not dict, type={type(val)}')

        lx = tx - (getattr(chunk, 'x', (tx // 16)) * 16)
        lz = tz - (getattr(chunk, 'z', (tz // 16)) * 16)
        ly = ty

        print(f'Local coords: lx={lx}, ly={ly}, lz={lz}')
        try:
            set_block_in_chunk(chunk, lx, ly, lz, 'minecraft:stone', region=reg)
            print('set_block_in_chunk completed')
        except Exception as e:
            print(f'set_block_in_chunk failed: {e}')
            import traceback
            traceback.print_exc()
            return 4

        # Inspect section after write
        if sec is not None:
            if isinstance(sec, dict):
                print(f'Palette after (dict): {sec.get("Palette", [])[:3]}...')
                print(f'BlockStates after (dict): {sec.get("BlockStates", [])[:3]}...')
            elif hasattr(sec, 'value') and isinstance(sec.value, dict):
                print(f'Palette after (value): {sec.value.get("Palette", [])[:3]}...')
                print(f'BlockStates after (value): {sec.value.get("BlockStates", [])[:3]}...')

        # save region
        print('Saving region...')
        try:
            if hasattr(reg, 'save'):
                reg.save()
                print('Region saved via save()')
            elif hasattr(reg, 'save_in_place'):
                reg.save_in_place()
                print('Region saved via save_in_place()')
        except Exception as e:
            print(f'Region save failed: {e}')
            import traceback
            traceback.print_exc()

    # Reopen and verify
    rf = Path(WORLD_ROOT) / WORLD / 'region'
    rx = tx // 512 if tx >= 0 else -((-tx - 1) // 512) - 1
    rz = tz // 512 if tz >= 0 else -((-tz - 1) // 512) - 1
    region_file = rf / f'r.{rx}.{rz}.mca'
    print(f'\nReopening region file: {region_file}')
    if not region_file.exists():
        print('Region file missing')
        return 5

    try:
        reg2 = anvil.Region.from_file(str(region_file))
        chunk_x = tx // 16 if tx >= 0 else -((-tx - 1) // 16) - 1
        chunk_z = tz // 16 if tz >= 0 else -((-tz - 1) // 16) - 1
        ch2 = reg2.get_chunk(chunk_x, chunk_z)
        if ch2 is None:
            print('Chunk missing')
            return 6
        lx2 = tx - (getattr(ch2, 'x', (tx // 16)) * 16)
        lz2 = tz - (getattr(ch2, 'z', (tz // 16)) * 16)
        b = ch2.get_block(lx2, ty, lz2)
        name = None
        if hasattr(b, 'namespaced'):
            name = b.namespaced
        elif hasattr(b, 'id'):
            name = b.id
        else:
            name = str(b)
        print(f'Read back block at ({tx}, {ty}, {tz}) => {name}')
        if name != 'minecraft:stone' and 'stone' not in str(name):
            print(f'ERROR: expected minecraft:stone but got {name}')
            return 7
    except Exception as e:
        print(f'Verification failed: {e}')
        import traceback
        traceback.print_exc()
        return 8

    print('Success: block written and verified as minecraft:stone')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
