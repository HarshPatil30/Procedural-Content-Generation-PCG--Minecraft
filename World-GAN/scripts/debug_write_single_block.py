from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

# Fix broken anvil-parser namespace package
import PyAnvilEditor.fix_anvil

from PyAnvilEditor.pyanvil import World
from PyAnvilEditor.nbt_block_writer import set_block_in_chunk_nbt
import anvil

WORLD = 'Gen_FixedTest'
WORLD_ROOT = repo / 'input' / 'minecraft'

def main():
    tx, ty, tz = 1, 64, 1
    print('Debug: write single block at', (tx, ty, tz))
    with World(WORLD, str(WORLD_ROOT)) as wrld:
        chunk, reg = wrld.get_chunk_for_world_coords(tx, tz)
        if chunk is None or reg is None:
            print('Region/chunk not available; attempting to create region/chunk')
            # try to load region directly
            rx = tx // 512 if tx >= 0 else -((-tx - 1) // 512) - 1
            rz = tz // 512 if tz >= 0 else -((-tz - 1) // 512) - 1
            reg = wrld._load_region(rx, rz)
            if reg is None:
                print('Failed: region file not found and could not be created')
                return 2
            chunk_x = tx // 16 if tx >= 0 else -((-tx - 1) // 16) - 1
            chunk_z = tz // 16 if tz >= 0 else -((-tz - 1) // 16) - 1
            try:
                chunk = reg.get_chunk(chunk_x, chunk_z)
            except Exception:
                chunk = None
            if chunk is None:
                print('Failed: could not obtain or create chunk')
                return 3

        lx = tx - (getattr(chunk, 'x', (tx // 16)) * 16)
        lz = tz - (getattr(chunk, 'z', (tz // 16)) * 16)
        ly = ty

        # Determine region file path
        rx = tx // 512 if tx >= 0 else -((-tx - 1) // 512) - 1
        rz = tz // 512 if tz >= 0 else -((-tz - 1) // 512) - 1
        region_file = WORLD_ROOT / WORLD / 'region' / f'r.{rx}.{rz}.mca'

        try:
            set_block_in_chunk_nbt(chunk, lx, ly, lz, 'minecraft:stone', region=reg, region_file_path=str(region_file))
        except Exception as e:
            print('Warning: write failed:', e)
            return 4

        # save region
        print('set_block_in_chunk_nbt completed (region file written)')

    # reopen and verify
    rf = Path(WORLD_ROOT) / WORLD / 'region'
    rx = tx // 512 if tx >= 0 else -((-tx - 1) // 512) - 1
    rz = tz // 512 if tz >= 0 else -((-tz - 1) // 512) - 1
    region_file = rf / f'r.{rx}.{rz}.mca'
    if not region_file.exists():
        print('Region file missing after save:', region_file)
        return 5

    try:
        reg2 = anvil.Region.from_file(str(region_file))
        chunk_x = tx // 16 if tx >= 0 else -((-tx - 1) // 16) - 1
        chunk_z = tz // 16 if tz >= 0 else -((-tz - 1) // 16) - 1
        ch2 = reg2.get_chunk(chunk_x, chunk_z)
        if ch2 is None:
            print('Chunk missing after reopen')
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
        print('Read back block at', (tx, ty, tz), '=>', name)
        if name != 'minecraft:stone' and 'stone' not in str(name):
            print('Warning: expected minecraft:stone but got', name)
            return 7
    except Exception as e:
        print('Verification failed:', e)
        import traceback
        traceback.print_exc()
        return 8

    print('Success: block written and verified as minecraft:stone')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

