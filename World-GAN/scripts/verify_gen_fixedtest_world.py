from pathlib import Path
import sys
import torch
from collections import Counter

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from PyAnvilEditor.pyanvil import World

p = repo / 'input' / 'minecraft'
world_name = 'Gen_FixedTest'
world_dir = p / world_name

if not world_dir.exists():
    print('World folder not found:', world_dir)
    raise SystemExit(1)

# load token list and bdata
ft = p / 'fixed_test'
if not ft.exists():
    print('fixed_test dataset missing at', ft)
    raise SystemExit(1)

tokens = torch.load(str(ft / 'token_list.pt'))
real = torch.load(str(ft / 'real_bdata.pt'))
# if real is one-hot, convert to indices
if isinstance(real, torch.Tensor) and real.ndim == 5:
    # shape [1, C, Y, Z, X]
    indices = real.argmax(dim=1).squeeze(0).numpy()
else:
    indices = real.numpy() if hasattr(real, 'numpy') else real

# start coords (must match write_fixed_test_world.py)
start_y = 60
start_z = -310
start_x = -342
start_coords = (start_y, start_z, start_x)

print('Scanning world', world_name, 'at', start_coords, 'shape', indices.shape)

non_air_positions = []
name_counts = Counter()

with World(world_name, str(p), debug=False) as wrld:
    sy, sz, sx = start_coords
    ny, nz, nx = indices.shape
    for iy in range(ny):
        for iz in range(nz):
            for ix in range(nx):
                idx = int(indices[iy, iz, ix])
                tok = tokens[idx] if idx < len(tokens) else str(idx)
                wy = sy + iy
                wz = sz + iz
                wx = sx + ix
                b = wrld.get_block((wy, wz, wx))
                bname = b.get_state().name
                if bname is None:
                    bname = str(b.get_state())
                name_counts[bname] += 1
                # consider non-air if name not equals minecraft:air or contains 'Air' substring
                if not (isinstance(bname, str) and ('air' in bname.lower())):
                    non_air_positions.append(((wy, wz, wx), tok, bname))

print('Total unique block names found in scanned area:', len(name_counts))
print('Top 20 block names in world area:')
for nm, c in name_counts.most_common(20):
    print(f'  {nm}: {c}')

print('\nNumber of positions where world block is not air (by name heuristic):', len(non_air_positions))
print('Sample non-air positions (up to 20):')
for item in non_air_positions[:20]:
    print('  world_coord(y,z,x)=', item[0], 'token=', item[1], 'written_name=', item[2])

if len(non_air_positions) == 0:
    print('\nWarning: no non-air blocks detected in that area — something went wrong.')
else:
    print('\nVerification passed: non-air blocks present. You can open the world in Minecraft using the folder:')
    print(str(world_dir))
    print('\nTo open in Minecraft: copy or move this folder to your Minecraft `saves` directory and launch Minecraft (same major version).')

print('\nDone.')
