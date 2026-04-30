#!/usr/bin/env python3
"""Normalize token_list.pt files to namespaced Minecraft IDs.

Rules:
- If token is not a string -> replace with 'minecraft:air'
- If token contains ':' -> leave as-is
- Otherwise prefix with 'minecraft:'

This script updates token_list.pt in-place for each provided world folder (or all folders under input/minecraft).
"""
from pathlib import Path
import sys
import argparse
import torch


def normalize_token(tok):
    if not isinstance(tok, str):
        return 'minecraft:air'
    tok = tok.strip()
    if ':' in tok:
        return tok
    # special-case common synonyms that already are 'air' or 'cave_air'
    if tok == '' or tok.lower().startswith('<pyanviteditor'):
        return 'minecraft:air'
    return f'minecraft:{tok}'


def process_folder(folder: Path):
    token_path = folder / 'token_list.pt'
    if not token_path.exists():
        print(f'No token_list.pt in {folder}, skipping')
        return False
    try:
        tokens = torch.load(str(token_path))
    except Exception:
        import pickle

        with open(token_path, 'rb') as f:
            tokens = pickle.load(f)

    print(f'Normalizing {token_path} (len={len(tokens)})')
    new_tokens = [normalize_token(t) for t in tokens]
    # show diffs for user
    diffs = [(i, old, new) for i, (old, new) in enumerate(zip(tokens, new_tokens)) if old != new]
    if diffs:
        print('Sample changes:')
        for i, old, new in diffs[:50]:
            print(f'  idx {i}: {repr(old)} -> {repr(new)}')

    # save back
    torch.save(new_tokens, str(token_path))
    print(f'Saved normalized tokens to {token_path}')
    return True


def main():
    parser = argparse.ArgumentParser(description='Normalize token_list.pt to namespaced Minecraft IDs')
    parser.add_argument('--folders', '-f', nargs='*', help='World folders under input/minecraft to normalize (default: try2 fixed_test)')
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    input_minecraft = repo / 'input' / 'minecraft'

    targets = args.folders if args.folders else ['try2', 'fixed_test']
    for t in targets:
        folder = input_minecraft / t
        if not folder.exists():
            print(f'Folder not found: {folder} -- skipping')
            continue
        process_folder(folder)


if __name__ == '__main__':
    main()
