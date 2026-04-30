import os
import pickle
import sys
from pathlib import Path

# Ensure repo root is on sys.path so we can import the local PyAnvilEditor
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
from PyAnvilEditor.pyanvil import World


def load_coords(pth):
    with open(pth, 'rb') as f:
        data = pickle.load(f)
    return data


def is_air(name):
    if name is None:
        return True
    s = str(name).lower()
    return 'air' in s


def scan_coarse(world, x0, x1, y0, y1, z0, z1, stride=4, max_checks=1000000):
    found = False
    xmin = xmax = ymin = ymax = zmin = zmax = None
    checks = 0
    for x in range(x0, x1 + 1, stride):
        for z in range(z0, z1 + 1, stride):
            for y in range(y0, y1 + 1, stride):
                checks += 1
                if checks > max_checks:
                    return found, (xmin, xmax, ymin, ymax, zmin, zmax)
                b = world.get_block((y, z, x))
                try:
                    name = b.get_state().name
                except Exception:
                    name = str(b)
                if not is_air(name):
                    if not found:
                        xmin = xmax = x
                        ymin = ymax = y
                        zmin = zmax = z
                        found = True
                    else:
                        xmin = min(xmin, x)
                        xmax = max(xmax, x)
                        ymin = min(ymin, y)
                        ymax = max(ymax, y)
                        zmin = min(zmin, z)
                        zmax = max(zmax, z)
    return found, (xmin, xmax, ymin, ymax, zmin, zmax)


def refine(world, bbox):
    xmin, xmax, ymin, ymax, zmin, zmax = bbox
    if xmin is None:
        return None
    # brute-force refine by checking every block in the small bbox
    rxmin = rxmax = None
    rymin = rymax = None
    rzmin = rzmax = None
    for x in range(xmin, xmax + 1):
        for z in range(zmin, zmax + 1):
            for y in range(ymin, ymax + 1):
                b = world.get_block((y, z, x))
                try:
                    name = b.get_state().name
                except Exception:
                    name = str(b)
                if not is_air(name):
                    if rxmin is None:
                        rxmin = rxmax = x
                        rymin = rymax = y
                        rzmin = rzmax = z
                    else:
                        rxmin = min(rxmin, x)
                        rxmax = max(rxmax, x)
                        rymin = min(rymin, y)
                        rymax = max(rymax, y)
                        rzmin = min(rzmin, z)
                        rzmax = max(rzmax, z)
    return rxmin, rxmax, rymin, rymax, rzmin, rzmax


def main():
    repo_root = Path(__file__).resolve().parents[1]
    pkl = repo_root / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'
    if not pkl.exists():
        print('primordial_coords_dict.pkl not found at', pkl)
        return
    data = load_coords(pkl)
    if 'village' not in data:
        print('No "village" entry found in primordial_coords_dict.pkl. Keys:')
        print(list(data.keys()))
        return
    coords = data['village']
    print('village coords from pickle:', coords)

    # Attempt to interpret coords tuple of ((x0,x1),(y0,y1),(z0,z1))
    try:
        (x0, x1), (y0, y1), (z0, z1) = coords
    except Exception:
        # try alternate ordering
        try:
            (y0, y1), (z0, z1), (x0, x1) = coords
        except Exception:
            print('Unrecognized coords format:', coords)
            return

    print(f'Scanning world for non-air blocks in bbox x[{x0},{x1}] y[{y0},{y1}] z[{z0},{z1}] (coarse)')
    world_root = repo_root / 'input' / 'minecraft'
    world_name = 'try1'
    with World(world_name, str(world_root)) as w:
        found, coarse = scan_coarse(w, x0, x1, y0, y1, z0, z1, stride=4)
        if not found:
            print('No non-air blocks found at coarse stride=4 in the given bbox. Try larger bbox or different area name.')
            return
        print('Coarse found bbox (stride=4):', coarse)
        refined = refine(w, coarse)
        print('Refined bbox:', refined)


if __name__ == '__main__':
    main()
