#!/usr/bin/env python3
"""
Tokenize diverse samples for multi-sample GAN training.
"""
import sys
from pathlib import Path
import torch

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

print("=" * 70)
print("Tokenize Diverse Samples")
print("=" * 70)

# Load raw samples
input_dir = repo_root / "input" / "minecraft" / "diverse_dataset"
samples_file = input_dir / "raw_blocks_list.pt"
labels_file = input_dir / "sample_labels.pt"

print(f"\nLoading: {samples_file}")
all_samples = torch.load(samples_file)
labels = torch.load(labels_file)

print(f"Loaded {len(all_samples)} samples")

# Build global token list from ALL samples
print("\nBuilding global token list from all samples...")
all_blocks = set()
for sample_blocks in all_samples:
    all_blocks.update(sample_blocks)

token_list = sorted(list(all_blocks))
print(f"Total unique blocks across all samples: {len(token_list)}")

# Show top blocks
print("\nToken list:")
for i, block in enumerate(token_list[:20]):
    print(f"  [{i:2}] {block}")
if len(token_list) > 20:
    print(f"  ... and {len(token_list) - 20} more")

# Create token to index mapping
block_to_idx = {block: idx for idx, block in enumerate(token_list)}

print("\nConverting samples to indices...")
samples_as_indices = []

for i, (sample_blocks, label) in enumerate(zip(all_samples, labels)):
    print(f"  [{i+1}/{len(all_samples)}] {label}")
    
    # Convert to indices
    indices = torch.zeros(60, 40, 60, dtype=torch.long)
    idx = 0
    for x in range(60):
        for y in range(40):
            for z in range(60):
                block_name = sample_blocks[idx]
                indices[x, y, z] = block_to_idx[block_name]
                idx += 1
    
    samples_as_indices.append(indices)
    
    # Stats
    unique_in_sample = len(set(sample_blocks))
    print(f"      Unique blocks in sample: {unique_in_sample}")

print("\nCreating one-hot encoded tensors...")
one_hot_samples = []

for i, indices in enumerate(samples_as_indices):
    # Create one-hot: (C, D, H, W)
    one_hot = torch.nn.functional.one_hot(indices, num_classes=len(token_list))
    # Permute to (C, D, H, W)
    one_hot = one_hot.permute(3, 0, 1, 2).float()
    one_hot_samples.append(one_hot)
    print(f"  [{i+1}/{len(samples_as_indices)}] {labels[i]}: {one_hot.shape}")

print("\n" + "=" * 70)
print("Saving outputs...")
print("=" * 70)

# Save token list
token_file = input_dir / "token_list.pt"
torch.save(token_list, token_file)
print(f"✓ {token_file}")

# Save one-hot samples as list
real_bdata_file = input_dir / "real_bdata_list.pt"
torch.save(one_hot_samples, real_bdata_file)
print(f"✓ {real_bdata_file}")

# Also save a single stacked tensor for compatibility
# Stack all samples into batch dimension
stacked = torch.stack(one_hot_samples, dim=0)  # (N, C, D, H, W)
stacked_file = input_dir / "real_bdata_stacked.pt"
torch.save(stacked, stacked_file)
print(f"✓ {stacked_file}")
print(f"   Shape: {stacked.shape} (batch, channels, depth, height, width)")

print("\n" + "=" * 70)
print("Tokenization Complete!")
print("=" * 70)
print(f"Samples: {len(one_hot_samples)}")
print(f"Tokens: {len(token_list)}")
print(f"Sample shape: {one_hot_samples[0].shape}")
print(f"Stacked shape: {stacked.shape}")
print(f"\nDataset ready for training!")
