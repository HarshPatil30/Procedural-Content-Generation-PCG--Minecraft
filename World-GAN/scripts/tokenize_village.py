#!/usr/bin/env python3
"""
Tokenize the extracted village region.
Creates token_list.pt and real_bdata.pt for GAN training.
"""
import sys
from pathlib import Path
import torch
import numpy as np

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


def tokenize_village(raw_blocks_path, output_dir):
    """
    Convert raw block names to tokenized format.
    
    Args:
        raw_blocks_path: Path to raw_blocks.pt
        output_dir: Where to save token_list.pt and real_bdata.pt
    """
    print("="*60)
    print("World-GAN: Tokenize Village Region")
    print("="*60)
    
    # Load raw blocks
    print(f"\nLoading: {raw_blocks_path}")
    blocks = torch.load(str(raw_blocks_path))
    
    # Flatten to get all block names
    print("Flattening block data...")
    flat_blocks = []
    
    def flatten(lst):
        for item in lst:
            if isinstance(item, list):
                flatten(item)
            else:
                flat_blocks.append(item)
    
    flatten(blocks)
    
    print(f"  Total blocks: {len(flat_blocks):,}")
    
    # Create token list (unique block types)
    print("\nBuilding token list...")
    unique_blocks = sorted(set(flat_blocks))
    token_list = unique_blocks
    
    print(f"  Unique blocks: {len(token_list)}")
    for i, block in enumerate(token_list):
        count = flat_blocks.count(block)
        pct = (count / len(flat_blocks)) * 100
        print(f"    [{i:2d}] {block:30s} - {count:6,} ({pct:5.2f}%)")
    
    # Create block name to index mapping
    block_to_idx = {block: idx for idx, block in enumerate(token_list)}
    
    # Convert to indices
    print("\nConverting to indices...")
    
    def blocks_to_indices(lst):
        if isinstance(lst[0], str):
            return [block_to_idx[block] for block in lst]
        else:
            return [blocks_to_indices(item) for item in lst]
    
    indices = blocks_to_indices(blocks)
    indices_array = np.array(indices, dtype=np.int32)
    
    print(f"  Indices shape: {indices_array.shape}")
    
    # Convert to one-hot encoded tensor
    print("\nCreating one-hot encoded tensor...")
    num_tokens = len(token_list)
    shape = indices_array.shape
    
    # Reshape to (D, H, W) format expected by World-GAN
    # Our extraction is (X, Y, Z) which maps to (width_x, height_y, width_z)
    # World-GAN expects (depth, height, width) so we use (width_z, height_y, width_x)
    indices_tensor = torch.from_numpy(indices_array).long()
    
    # Permute dimensions: (X, Y, Z) -> (Z, Y, X) for World-GAN
    indices_tensor = indices_tensor.permute(2, 1, 0)
    
    print(f"  Permuted shape (D, H, W): {indices_tensor.shape}")
    
    # Create one-hot encoding
    # Shape will be (num_tokens, D, H, W)
    depth, height, width = indices_tensor.shape
    one_hot = torch.zeros((num_tokens, depth, height, width), dtype=torch.float32)
    
    for d in range(depth):
        for h in range(height):
            for w in range(width):
                token_idx = indices_tensor[d, h, w].item()
                one_hot[token_idx, d, h, w] = 1.0
    
    print(f"  One-hot shape (C, D, H, W): {one_hot.shape}")
    print(f"  Non-zero elements: {one_hot.nonzero().size(0):,}")
    
    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    
    token_path = output_dir / "token_list.pt"
    bdata_path = output_dir / "real_bdata.pt"
    
    print(f"\nSaving outputs...")
    torch.save(token_list, str(token_path))
    print(f"  ✓ {token_path}")
    
    torch.save(one_hot, str(bdata_path))
    print(f"  ✓ {bdata_path}")
    
    print("\n" + "="*60)
    print("Tokenization complete!")
    print("="*60)
    print(f"\nDataset ready for training:")
    print(f"  Tokens: {len(token_list)}")
    print(f"  Shape: {one_hot.shape} (channels, depth, height, width)")
    print(f"  Size: {one_hot.numel():,} elements")
    print(f"  Memory: {one_hot.element_size() * one_hot.numel() / 1024 / 1024:.2f} MB")


def main():
    # Paths
    dataset_dir = repo_root / "input" / "minecraft" / "village_dataset"
    raw_blocks_path = dataset_dir / "raw_blocks.pt"
    
    # Validate input
    if not raw_blocks_path.exists():
        print(f"ERROR: raw_blocks.pt not found at: {raw_blocks_path}")
        print("Please run extract_village_region.py first!")
        return 1
    
    # Tokenize
    tokenize_village(raw_blocks_path, dataset_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
