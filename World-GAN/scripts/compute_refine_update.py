import os
import re
import pickle
from pathlib import Path
from math import floor
import sys

import sys
# Ensure local packages are importable
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
from PyAnvilEditor.pyanvil import World


def region_extents(region_folder):
    rx_vals = []
    rz_vals = []
    p = Path(region_folder)
    if not p.exists():
        raise FileNotFoundError(region_folder)
    for f in p.iterdir():
        m = re.match(r'r\.(-?\d+)\.(-?\d+)\.mca$', f.name)
        if m:
            rx_vals.append(int(m.group(1)))
            rz_vals.append(int(m.group(2)))
    if not rx_vals:
        return None
    min_rx = min(rx_vals)
    max_rx = max(rx_vals)
    min_rz = min(rz_vals)
    max_rz = max(rz_vals)

    # region to block coords: region rx covers blocks rx*512 .. rx*512+511
    x0 = min_rx * 512
    x1 = max_rx * 512 + 511
    z0 = min_rz * 512
    z1 = max_rz * 512 + 511
    # full Y range
    y0, y1 = 0, 256
    return (x0, x1), (y0, y1), (z0, z1)


def scan_coarse(world, x0, x1, y0, y1, z0, z1, stride=8, max_checks=500000):
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
                if 'air' not in str(name).lower():
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
    rxmin = rxmax = rymin = rymax = rzmin = rzmax = None
    for x in range(xmin, xmax + 1):
        for z in range(zmin, zmax + 1):
            for y in range(ymin, ymax + 1):
                b = world.get_block((y, z, x))
                try:
                    name = b.get_state().name
                except Exception:
                    name = str(b)
                if 'air' not in str(name).lower():
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


def update_pickle(pkl_path, key, coords):
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    data[key] = coords
    with open(pkl_path, 'wb') as f:
        pickle.dump(data, f)


def main():
    repo = Path(__file__).resolve().parents[1]
    world = 'try2'
    region_folder = repo / 'input' / 'minecraft' / world / 'region'
    pkl = repo / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'

    coarse = region_extents(region_folder)
    if coarse is None:
        print('No region files found for', world)
        return
    print('Coarse extents:', coarse)
    # update pickle with coarse first
    update_pickle(pkl, world, coarse)
    print('Wrote coarse bbox to pickle under key', world)

    # refine by scanning for non-air
    with World(world, str(repo / 'input' / 'minecraft')) as w:
        found, coarse_found = scan_coarse(w, coarse[0][0], coarse[0][1], coarse[1][0], coarse[1][1], coarse[2][0], coarse[2][1], stride=8)
        if not found:
            print('No non-air blocks found in coarse scan; keeping coarse bbox')
            return
        print('Coarse non-air bbox:', coarse_found)
        refined = refine(w, coarse_found)
        if refined is None:
            print('Refinement found nothing; keeping coarse')
            return
        # convert refined (xmin,xmax,ymin,ymax,zmin,zmax) into ((x0,x1),(y0,y1),(z0,z1))
        refined_coords = ((refined[0], refined[1]), (refined[2], refined[3]), (refined[4], refined[5]))
        update_pickle(pkl, world, refined_coords)
        print('Wrote refined bbox to pickle under key', world)


if __name__ == '__main__':
    main()
