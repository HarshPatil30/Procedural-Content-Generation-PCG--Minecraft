#!/usr/bin/env python3
"""Diagnostic checks for World-GAN token lists and generator output.

Saves: none. Prints diagnostics to stdout.
"""
from pathlib import Path
import sys
import argparse
import pickle
from collections import Counter

import torch


def load_maybe_torch(path: Path):
    """Load with torch.load if possible, else fall back to pickle."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        return torch.load(str(path))
    except Exception:
        with open(path, 'rb') as f:
            return pickle.load(f)


def print_token_lists(train_path: Path, fixed_path: Path):
    try:
        train_tokens = load_maybe_torch(train_path)
    except FileNotFoundError:
        print(f"ERROR: training token list not found: {train_path}")
        train_tokens = None

    try:
        fixed_tokens = load_maybe_torch(fixed_path)
    except FileNotFoundError:
        print(f"ERROR: fixed_test token list not found: {fixed_path}")
        fixed_tokens = None

    if train_tokens is None and fixed_tokens is None:
        return None, None

    if train_tokens is None:
        train_tokens = []
    if fixed_tokens is None:
        fixed_tokens = []

    print(f"TRAIN token_list length: {len(train_tokens)}")
    print(f"FIXED_TEST token_list length: {len(fixed_tokens)}")
    print()

    max_len = max(len(train_tokens), len(fixed_tokens))
    mismatches = []
    for i in range(max_len):
        t = train_tokens[i] if i < len(train_tokens) else '<MISSING>'
        f = fixed_tokens[i] if i < len(fixed_tokens) else '<MISSING>'
        print(f"Index {i}: TRAIN={repr(t)} / FIXED={repr(f)}", end='')
        if t != f:
            print("  <-- mismatch")
            mismatches.append(i)
        else:
            print()

    # warn about extra minecraft:air in fixed_test that train doesn't have
    if train_tokens and fixed_tokens:
        train_air = sum(1 for x in train_tokens if isinstance(x, str) and x == 'minecraft:air')
        fixed_air = sum(1 for x in fixed_tokens if isinstance(x, str) and x == 'minecraft:air')
        if fixed_air > train_air:
            print(f"\nWARNING: fixed_test has {fixed_air} 'minecraft:air' entries but training has {train_air}.")

    if mismatches:
        print(f"\nWARNING: Token lists differ at indices: {mismatches}")

    return train_tokens, fixed_tokens


def inspect_generator_output(gen_path: Path):
    if not gen_path.exists():
        print(f"Generator output not found: {gen_path}")
        return None

    try:
        data = load_maybe_torch(gen_path)
    except Exception as e:
        print(f"Failed to load generator output {gen_path}: {e}")
        return None

    # Expecting tensor with class dimension at dim=1, or classes at last dim
    if not isinstance(data, torch.Tensor):
        try:
            data = torch.as_tensor(data)
        except Exception:
            print("Generator output is not tensor-like")
            return None

    if data.ndim < 2:
        print(f"Generator output has unexpected shape: {tuple(data.shape)}")
        return None

    # If channels are last, try to move them to dim=1
    # Common shapes: [B, C, Y, Z, X] or [B, Y, Z, X, C] or [C, Y, Z]
    shape = tuple(data.shape)
    if data.ndim >= 4 and data.shape[1] <= 256:
        # assume [B, C, ...]
        arg = torch.argmax(data, dim=1)
    elif data.ndim >= 4 and data.shape[-1] <= 256:
        # assume channels last
        data_perm = data.permute(0, -1, *range(1, data.ndim - 1))
        arg = torch.argmax(data_perm, dim=1)
    elif data.ndim == 3:
        # [C, Y, X] -> argmax over dim 0
        arg = torch.argmax(data, dim=0)
    else:
        # fallback: argmax over dim 1
        try:
            arg = torch.argmax(data, dim=1)
        except Exception as e:
            print(f"Could not compute argmax on generator output: {e}")
            return None

    unique = torch.unique(arg)
    counts = Counter(arg.flatten().tolist())

    print(f"\nGenerator argmax shape: {tuple(arg.shape)}")
    print(f"Unique predicted class indices: {unique}")
    print("Count per class index:")
    for k in sorted(counts.keys()):
        print(f"{k} -> {counts[k]} voxels")

    if len(counts) == 1 and 0 in counts:
        print("\nWARNING: Generator is producing only class index 0 (air).")
        print("This will result in an all-air world.")

    return arg


def main():
    parser = argparse.ArgumentParser(description="Diagnose World-GAN token lists and generator output")
    parser.add_argument('--train', '-t', required=True, help='Train dataset folder name (under input/minecraft)')
    parser.add_argument('--fixed', '-f', default='fixed_test', help='Fixed test folder name (default: fixed_test)')
    parser.add_argument('--gen', '-g', default='input/minecraft/fixed_test/gen_out.pt', help='Generator output path')
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    train_tokens_path = repo / 'input' / 'minecraft' / args.train / 'token_list.pt'
    fixed_tokens_path = repo / 'input' / 'minecraft' / args.fixed / 'token_list.pt'

    train_tokens, fixed_tokens = print_token_lists(train_tokens_path, fixed_tokens_path)

    gen_path = Path(args.gen)
    # Allow relative paths from repo root
    if not gen_path.exists():
        gen_path = repo / args.gen

    arg = inspect_generator_output(gen_path)

    print('\nFINAL SUMMARY:')
    if train_tokens is None or fixed_tokens is None:
        print('High-priority: missing one or both token lists.')
    else:
        if train_tokens != fixed_tokens:
            print('High-priority WARNING: token lists do not match exactly.')
        else:
            print('Token lists match exactly.')

    if arg is None:
        print('Generator output: missing or unusable. Could be writer or generator issue.')
    else:
        uniq = set(torch.unique(arg).tolist())
        if uniq == {0}:
            print('Generator outputs only index 0. This can be normal for early GAN training.')
        else:
            print('Generator outputs multiple classes; if worlds are still all-air, the writer is likely the issue.')


if __name__ == '__main__':
    main()
