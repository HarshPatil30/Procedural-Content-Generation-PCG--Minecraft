import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PyAnvilEditor.pyanvil import World

def main():
    repo = Path(__file__).resolve().parents[1]
    world = 'try2'
    bbox = ((-512, 1023), (0, 256), (-512, 1023))
    x0, x1 = bbox[0]
    y0, y1 = bbox[1]
    z0, z1 = bbox[2]

    hits = []
    counts = {}
    max_hits = 200

    with World(world, str(repo / 'input' / 'minecraft')) as w:
        # sample coarse grid: stride 32 in X/Z, sample surface y-range
        stride = 32
        y_samples = list(range(60, 80, 4))
        for y in y_samples:
            for x in range(x0, x1+1, stride):
                for z in range(z0, z1+1, stride):
                    b = w.get_block((y, z, x))
                    try:
                        name = b.get_state().name
                    except Exception:
                        name = str(b)
                    name = str(name)
                    if 'air' not in name.lower():
                        hits.append((x, y, z, name))
                        counts[name] = counts.get(name, 0) + 1
                        if len(hits) >= max_hits:
                            break
                if len(hits) >= max_hits:
                    break
            if len(hits) >= max_hits:
                break

    print('Found', len(hits), 'non-air samples (sparse grid).')
    print('Top block types:')
    for name, c in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:20]:
        print(f'  {name}: {c}')

    print('\nFirst 50 hits:')
    for i, (x, y, z, name) in enumerate(hits[:50]):
        print(f'{i+1:3d}: ({x:6d}, {y:3d}, {z:6d}) {name}')

if __name__ == '__main__':
    main()
