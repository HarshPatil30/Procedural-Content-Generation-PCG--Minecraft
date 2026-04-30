import sys
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

import torch
from PyAnvilEditor.pyanvil import World

OUT_DIR = repo / 'input' / 'minecraft' / 'fixed_test'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# center and shape
cx, cy, cz = -320, 60, -288
shape_x, shape_y, shape_z = 45, 20, 45

x0 = cx - shape_x // 2
x1 = x0 + shape_x
y0 = cy
y1 = y0 + shape_y
z0 = cz - shape_z // 2
z1 = z0 + shape_z

print('Sampling box (x,y,z):', (x0, x1), (y0, y1), (z0, z1))

uniques = []
# indices array y,z,x
import numpy as np
indices = np.zeros((y1 - y0, z1 - z0, x1 - x0), dtype=np.int64)
non_air_count = 0

with World('try2', str(repo / 'input' / 'minecraft')) as w:
    for j, y in enumerate(range(y0, y1)):
        for k, z in enumerate(range(z0, z1)):
            for l, x in enumerate(range(x0, x1)):
                b = w.get_block((y, z, x))
                try:
                    name = b.get_state().name
                except Exception:
                    name = str(b)
                name = str(name)
                if name not in uniques:
                    uniques.append(name)
                idx = uniques.index(name)
                indices[j, k, l] = idx
                if 'air' not in name.lower():
                    non_air_count += 1

print('Found', len(uniques), 'unique tokens. Non-air blocks:', non_air_count)

# build one-hot tensor: shape (1, n_tokens, y, z, x)
n_tokens = len(uniques)
y_len = indices.shape[0]
z_len = indices.shape[1]
x_len = indices.shape[2]

oh = torch.zeros((1, n_tokens, y_len, z_len, x_len), dtype=torch.uint8)
for i in range(n_tokens):
    oh[0, i] = torch.from_numpy((indices == i).astype('uint8'))

# Save
torch.save(oh, str(OUT_DIR / 'real_bdata.pt'))
torch.save(uniques, str(OUT_DIR / 'token_list.pt'))
print('Saved real_bdata.pt and token_list.pt to', OUT_DIR)
