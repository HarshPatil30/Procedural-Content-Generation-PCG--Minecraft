"""
Generate samples from the trained diverse GAN.
"""
import argparse
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import torch
from config import Config
from models.generator import Level_GeneratorConcatSkip2CleanAdd


def parse_args():
    parser = argparse.ArgumentParser(description='Generate samples from trained diverse GAN')
    parser.add_argument('--num_samples', type=int, default=10, help='number of samples to generate')
    parser.add_argument('--not_cuda', action='store_true', help='use CPU instead of CUDA')
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("=" * 70)
    print("Generate Samples from Diverse GAN")
    print("=" * 70)
    
    # Load model
    model_dir = repo_root / "output" / "diverse_dataset"
    checkpoint = torch.load(model_dir / "models.pth", map_location='cpu')
    token_list = torch.load(model_dir / "token_list.pt")
    
    num_channels = checkpoint['num_channels']
    noise_amp = checkpoint['noise_amp']
    
    print(f"\nModel info:")
    print(f"  Block types: {num_channels}")
    print(f"  Noise amplitude: {noise_amp}")
    
    # Device
    device = torch.device('cpu' if args.not_cuda else 'cuda')
    print(f"  Device: {device}")
    
    # Setup config
    opt = Config()
    opt.nc_current = num_channels
    opt.nfc = 64
    opt.num_layer = 5
    opt.ker_size = 3
    opt.level_shape = [60, 40, 60]
    opt.not_cuda = args.not_cuda
    
    # Load generator
    generator = Level_GeneratorConcatSkip2CleanAdd(opt=opt, use_softmax=True).to(device)
    generator.load_state_dict(checkpoint['generator'])
    generator.eval()
    
    print(f"\nGenerating {args.num_samples} samples...\n")
    
    # Generate samples
    samples = []
    with torch.no_grad():
        for i in range(args.num_samples):
            # Random noise
            noise = torch.randn(1, num_channels, 60, 40, 60).to(device) * noise_amp
            prev = torch.zeros(1, num_channels, 60, 40, 60).to(device)
            
            # Generate
            fake = generator(noise, prev)
            
            # Convert to indices (argmax over channel dimension)
            indices = fake.argmax(dim=1).squeeze(0).cpu()  # Shape: [60, 40, 60]
            
            samples.append(indices)
            print(f"  [{i+1}/{args.num_samples}] Generated sample {i}")
            print(f"      Shape: {indices.shape}")
            print(f"      Unique blocks: {len(indices.unique())}")
    
    # Save samples
    output_dir = repo_root / "output" / "diverse_dataset_examples"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, sample in enumerate(samples):
        output_file = output_dir / f"sample_{i}.pt"
        torch.save(sample, output_file)
    
    # Also save token list
    torch.save(token_list, output_dir / "token_list.pt")
    
    print("\n" + "=" * 70)
    print("Generation Complete!")
    print("=" * 70)
    print(f"\n✓ Saved {len(samples)} samples to: {output_dir}")
    print(f"✓ Saved token list")
    print(f"\nNext: Write samples to Minecraft worlds with write_diverse_world.py")


if __name__ == "__main__":
    main()
