import pickle
from pathlib import Path

pth = Path('input/minecraft/primordial_coords_dict.pkl')
if not pth.exists():
    raise SystemExit('primordial_coords_dict.pkl not found')

with open(pth, 'rb') as f:
    data = pickle.load(f)

# Coarse bbox centered at (-435,71,329), +/-128 in X/Z and full Y
data['seed_village'] = ((-563, -307), (0, 256), (201, 457))

with open(pth, 'wb') as f:
    pickle.dump(data, f)

print('Added seed_village to primordial_coords_dict.pkl')
