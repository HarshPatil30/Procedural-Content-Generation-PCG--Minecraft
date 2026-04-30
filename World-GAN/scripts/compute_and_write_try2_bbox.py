import json
from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
from PyAnvilEditor.pyanvil import World
import pickle

WORLD_NAME = 'try2'
INPUT_DIR = str(repo / 'input' / 'minecraft')
OUT_DIR = repo / 'output'
OUT_DIR.mkdir(exist_ok=True)
HITS_FILE = OUT_DIR / 'try2_sparse_hits.json'
PICKLE_FILE = repo / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'

# Sparse scan parameters
COARSE_BBOX = ((-512, 1023), (0, 256), (-512, 1023))
STRIDE = 32
Y_SAMPLES = list(range(60, 80, 4))
MAX_HITS = 200
PADDING = 8

print('Scanning world', WORLD_NAME, 'for up to', MAX_HITS, 'non-air hits...')

hits = []
counts = {}
with World(WORLD_NAME, INPUT_DIR) as w:
    x0, x1 = COARSE_BBOX[0]
    y0, y1 = COARSE_BBOX[1]
    z0, z1 = COARSE_BBOX[2]
    for y in Y_SAMPLES:
        for x in range(x0, x1+1, STRIDE):
            for z in range(z0, z1+1, STRIDE):
                b = w.get_block((y, z, x))
                try:
                    name = b.get_state().name
                except Exception:
                    name = str(b)
                name = str(name)
                if 'air' not in name.lower():
                    hits.append((int(x), int(y), int(z), name))
                    counts[name] = counts.get(name, 0) + 1
                    if len(hits) >= MAX_HITS:
                        break
            if len(hits) >= MAX_HITS:
                break
        if len(hits) >= MAX_HITS:
            break

print('Found', len(hits), 'hits; writing', HITS_FILE)
HITS_FILE.write_text(json.dumps({'hits':hits,'counts':counts}, indent=2))

if len(hits) == 0:
    print('No non-air hits found. Aborting bbox update.')
    raise SystemExit(1)

xs = [h[0] for h in hits]
ys = [h[1] for h in hits]
zs = [h[2] for h in hits]

x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)
z_min, z_max = min(zs), max(zs)

x_min_p = x_min - PADDING
x_max_p = x_max + PADDING
y_min_p = max(0, y_min - PADDING)
y_max_p = min(256, y_max + PADDING)
z_min_p = z_min - PADDING
z_max_p = z_max + PADDING

new_bbox = ((x_min_p, x_max_p), (y_min_p, y_max_p), (z_min_p, z_max_p))

print('Computed tight bbox (padded):', new_bbox)

# Update pickle
if not PICKLE_FILE.exists():
    print('Pickle not found at', PICKLE_FILE, '— creating new dict')
    d = {}
else:
    with open(PICKLE_FILE, 'rb') as f:
        d = pickle.load(f)

d[WORLD_NAME] = new_bbox
with open(PICKLE_FILE, 'wb') as f:
    pickle.dump(d, f)

print('Updated', PICKLE_FILE, 'with key', WORLD_NAME)
print('Done.')
