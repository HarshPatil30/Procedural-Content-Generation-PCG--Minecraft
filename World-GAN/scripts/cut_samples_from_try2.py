import os
import math
import sys
import torch
from pathlib import Path
import pickle
import numpy as np
from tqdm import tqdm

# ensure repo root is on sys.path so local imports like `minecraft` resolve
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from minecraft.level_utils import read_level_from_file

repo = Path(__file__).resolve().parents[1]
PICKLE = repo / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'
if not PICKLE.exists():
    raise SystemExit('primordial_coords_dict.pkl not found')
with open(PICKLE, 'rb') as f:
    d = pickle.load(f)
if 'try2' not in d:
    raise SystemExit('try2 not in pickle')

bbox = d['try2']  # ((x0,x1),(y0,y1),(z0,z1))
(x0,x1),(y0,y1),(z0,z1) = bbox

num_samples = 100
shape = [45, 20, 45]  # x,y,z
save_tensors = True

dir2save = repo / 'output' / 'try2_examples'
(os.makedirs(dir2save, exist_ok=True) or None)
(os.makedirs(dir2save / 'torch_blockdata', exist_ok=True) or None)

# grid layout within bbox in X/Z
len_n = math.ceil(math.sqrt(num_samples))
# compute usable ranges (allow for shape size)
usable_x0 = x0
usable_x1 = x1 - shape[0]
usable_z0 = z0
usable_z1 = z1 - shape[2]
if usable_x1 < usable_x0:
    usable_x0, usable_x1 = x0, x1
if usable_z1 < usable_z0:
    usable_z0, usable_z1 = z0, z1

if len_n == 1:
    xs = [int((usable_x0 + usable_x1) / 2)]
    zs = [int((usable_z0 + usable_z1) / 2)]
else:
    xs = [int(usable_x0 + i * max(1, (usable_x1 - usable_x0) // (len_n - 1))) for i in range(len_n)]
    zs = [int(usable_z0 + i * max(1, (usable_z1 - usable_z0) // (len_n - 1))) for i in range(len_n)]

# choose posy within bbox; try to center or use min allowed
posy = max(y0, min(63, y1 - shape[1]))

n = 0
for xi in range(len(xs)):
    for zi in range(len(zs)):
        if n >= num_samples:
            break
        posx = xs[xi]
        posz = zs[zi]
        # read_level_from_file expects coords in (y, z, x) order: ((y0,y1),(z0,z1),(x0,x1))
        curr_coords = ((posy, posy + shape[1]),
                   (posz, posz + shape[2]),
                   (posx, posx + shape[0]))
        print(f'[{n+1}/{num_samples}] Using coords (y,z,x): {curr_coords} (posx={posx}, posy={posy}, posz={posz})')

        try:
            print(f'[{n+1}/{num_samples}] Extracting at posx={posx}, posy={posy}, posz={posz}...')
            I_curr = read_level_from_file(str(repo / 'input' / 'minecraft'), 'try2', curr_coords, None, None)
        except Exception as e:
            import traceback
            print(f'Error extracting sample {n} at ({posx},{posy},{posz}):', e)
            traceback.print_exc()
            # skip this sample position but continue with next
            n += 1
            continue

        if save_tensors:
            out_path = dir2save / 'torch_blockdata' / f'{n}.pt'
            try:
                torch.save(I_curr, str(out_path))
                print(f'  Saved sample {n} -> {out_path.name}')
            except Exception as e:
                print(f'  Failed to save sample {n}:', e)
        n += 1

print('Saved', n, 'samples to', dir2save)
