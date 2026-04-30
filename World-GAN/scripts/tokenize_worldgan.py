#!/usr/bin/env python3
"""Regenerate or validate token_list.pt for a World-GAN training world.

Features:
- Checks that the named world folder exists under `input/minecraft`.
- Warns if region files are missing or empty.
- If `token_list.pt` is missing in the train folder, scans region files and regenerates it.
- Saves `token_list.pt` using `torch.save()` and prints a summary.

This script has no external deps other than PyTorch and the repo's `PyAnvilEditor`.
"""
from pathlib import Path
import sys
import re
from collections import Counter
import argparse
import torch
# Ensure repo root is on sys.path so local packages (PyAnvilEditor) can be imported
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


def friendly_exit(msg: str, code: int = 1):
    print(f"ERROR: {msg}")
    sys.exit(code)


def find_region_files(world_dir: Path):
    region_dir = world_dir / 'region'
    if not region_dir.exists() or not region_dir.is_dir():
        return []
    return sorted(region_dir.glob('r.*.*.mca'))


def check_region_files(region_files):
    if not region_files:
        print('WARNING: no region files found (world may be empty or corrupted).')
        return False
    bad = []
    for p in region_files:
        try:
            if p.stat().st_size == 0:
                bad.append(p)
        except Exception:
            bad.append(p)
    if bad:
        print('WARNING: some region files are empty or unreadable:')
        for b in bad:
            print('  ', b)
        return False
    return True


def load_token_list(token_path: Path):
    if not token_path.exists():
        return None
    try:
        return torch.load(str(token_path))
    except Exception:
        # try pickle fallback
        import pickle

        with open(token_path, 'rb') as f:
            return pickle.load(f)


def save_token_list(token_path: Path, tokens):
    token_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        torch.save(tokens, str(token_path))
        print(f'Saved token list to {token_path}')
    except Exception as e:
        print(f'Failed to save token list with torch.save(): {e}')
        # fallback to pickle
        import pickle

        with open(token_path, 'wb') as f:
            pickle.dump(tokens, f)
        print(f'Saved token list (pickle fallback) to {token_path}')


def normalize_block_name(name):
    # Convert object-repr air placeholders and non-namespaced short names to safe strings
    if not isinstance(name, str):
        return 'minecraft:air'
    # Common PyAnvil placeholder form
    if 'PyAnvilEditor.pyanvil.Air' in name or name.startswith('<PyAnvilEditor'):
        return 'minecraft:air'
    # Convert short form 'stone' -> 'minecraft:stone' optionally,
    # but keep existing namespaced tokens intact.
    if ':' in name:
        return name
    # Keep short names (the rest of the pipeline is tolerant), but also offer namespaced option
    return name


def regenerate_token_list_from_world(world_name: str, input_dir: Path):
    # lazy import anvil via PyAnvilEditor wrapper usage
    try:
        from PyAnvilEditor.pyanvil import World
    except Exception as e:
        friendly_exit(f"PyAnvilEditor is required to scan world regions: {e}")

    tokens = Counter()
    world_dir = input_dir / world_name
    region_files = find_region_files(world_dir)
    if not region_files:
        friendly_exit(f"No region files found for world '{world_name}' at {world_dir}.")

    print(f'Scanning {len(region_files)} region file(s) for block types...')

    # Use World wrapper to open and sample blocks; iterate through region files' chunk locations
    try:
        with World(world_name, str(input_dir), debug=False) as wrld:
            # find a reasonable scanning box: try to derive from region filenames
            # We'll scan each region file's chunks by iterating over region coordinates and sampling chunk blocks
            for rf in region_files:
                m = re.match(r'r\.(-?\d+)\.(-?\d+)\.mca', rf.name)
                if not m:
                    continue
                rx = int(m.group(1))
                rz = int(m.group(2))
                # region coordinate rx, rz -> block coordinate range is 512*rx .. 512*(rx+1)
                x0 = rx * 512
                z0 = rz * 512
                # sample a grid inside region to avoid extremely slow full scans
                # We'll sample at chunk centers every 16 blocks across region
                for bx in range(x0, x0 + 512, 16 * 4):
                    for bz in range(z0, z0 + 512, 16 * 4):
                        # scan a vertical column of typical y range
                        for by in range(0, 128, 8):
                            try:
                                b = wrld.get_block((by, bz, bx))
                                name = b.get_state().name
                                name = normalize_block_name(name)
                                tokens[name] += 1
                            except Exception:
                                continue
    except Exception as e:
        friendly_exit(f'Failed scanning world using PyAnvilEditor.World: {e}')

    unique_tokens = list(tokens.keys())
    print(f'Found {len(unique_tokens)} unique token names (sample):')
    for t in unique_tokens[:50]:
        print('  ', t)

    return unique_tokens


def main():
    parser = argparse.ArgumentParser(description='Tokenize or regenerate token_list.pt for a world')
    parser.add_argument('--train', '-t', default='try2', help='Train dataset folder name under input/minecraft')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    input_dir = repo_root / 'input' / 'minecraft'
    train_dir = input_dir / args.train

    if not train_dir.exists():
        friendly_exit(f"Train folder does not exist: {train_dir}. Please check your config train_dataset setting.")

    region_files = find_region_files(train_dir)
    ok = check_region_files(region_files)

    token_path = train_dir / 'token_list.pt'
    tokens = load_token_list(token_path)
    if tokens is None:
        print(f"token_list.pt not found in {train_dir}. Regenerating by scanning region files...")
        new_tokens = regenerate_token_list_from_world(args.train, input_dir)
        if not new_tokens:
            friendly_exit('No tokens found while regenerating. World may be empty or unreadable.')
        # Save the tokens (keep as list of strings)
        save_token_list(token_path, new_tokens)
    else:
        print(f'Found existing token_list.pt with {len(tokens)} tokens at {token_path}')

    if not ok:
        print('\nNote: region file checks reported issues — tokenization may be incomplete or unreliable.')


if __name__ == '__main__':
    main()
