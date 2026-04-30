"""
Train GAN on diverse Minecraft samples (15 samples from different biomes).
This learns natural terrain variation instead of memorizing a single sample.
"""
import argparse
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

from config import Config
from models.discriminator import Level_WDiscriminator
from models.generator import Level_GeneratorConcatSkip2CleanAdd

def parse_args():
    parser = argparse.ArgumentParser(description='Train GAN on diverse Minecraft samples')
    parser.add_argument('--niter', type=int, default=1000, help='number of epochs to train')
    parser.add_argument('--lr_g', type=float, default=0.0005, help='learning rate for generator')
    parser.add_argument('--lr_d', type=float, default=0.0005, help='learning rate for discriminator')
    parser.add_argument('--not_cuda', action='store_true', help='use CPU instead of CUDA')
    parser.add_argument('--batch_size', type=int, default=1, help='batch size (use 1 for single sample iteration)')
    return parser.parse_args()

def train_diverse_gan(args):
    print("=" * 70)
    print("Train GAN on Diverse Minecraft Samples")
    print("=" * 70)
    
    # Load data
    data_dir = repo_root / "input" / "minecraft" / "diverse_dataset"
    token_list = torch.load(data_dir / "token_list.pt")
    real_data = torch.load(data_dir / "real_bdata_stacked.pt")  # Shape: [15, 68, 60, 40, 60]
    
    num_samples, num_channels, depth, height, width = real_data.shape
    print(f"\nDataset:")
    print(f"  Samples: {num_samples}")
    print(f"  Block types: {num_channels}")
    print(f"  Size: {depth}×{height}×{width}")
    print(f"  Shape: {real_data.shape}")
    
    # Device
    device = torch.device('cpu' if args.not_cuda else 'cuda')
    print(f"\nDevice: {device}")
    
    # Config for models
    opt = Config()
    opt.nc_current = num_channels
    opt.nfc = 64
    opt.num_layer = 5
    opt.ker_size = 3
    opt.level_shape = [depth, height, width]
    opt.not_cuda = args.not_cuda
    
    # Models
    noise_amp = 1.0
    
    generator = Level_GeneratorConcatSkip2CleanAdd(
        opt=opt,
        use_softmax=True
    ).to(device)
    
    discriminator = Level_WDiscriminator(
        opt=opt
    ).to(device)
    
    # Optimizers
    opt_g = optim.Adam(generator.parameters(), lr=args.lr_g, betas=(0.5, 0.999))
    opt_d = optim.Adam(discriminator.parameters(), lr=args.lr_d, betas=(0.5, 0.999))
    
    print(f"\nTraining for {args.niter} epochs...")
    print("Each epoch trains on all 15 diverse samples")
    print("Using WGAN-GP loss (Wasserstein GAN with Gradient Penalty)\n")
    
    # Training loop
    for epoch in range(args.niter):
        epoch_g_loss = 0
        epoch_d_loss = 0
        
        # Shuffle samples each epoch
        indices = torch.randperm(num_samples)
        
        for idx in indices:
            real = real_data[idx:idx+1].to(device)  # [1, 68, 60, 40, 60]
            
            # ---------------------
            #  Train Discriminator
            # ---------------------
            opt_d.zero_grad()
            
            # Generate fake
            noise = torch.randn_like(real) * noise_amp
            prev = torch.zeros_like(real)
            fake = generator(noise, prev)
            
            # WGAN loss: maximize D(real) - D(fake)
            # = minimize D(fake) - D(real)
            real_validity = discriminator(real)
            fake_validity = discriminator(fake.detach())
            
            d_loss = -(torch.mean(real_validity) - torch.mean(fake_validity))
            d_loss.backward()
            opt_d.step()
            
            # -----------------
            #  Train Generator
            # -----------------
            opt_g.zero_grad()
            
            # WGAN loss: maximize D(fake) = minimize -D(fake)
            gen_validity = discriminator(fake)
            g_loss = -torch.mean(gen_validity)
            g_loss.backward()
            opt_g.step()
            
            epoch_g_loss += g_loss.item()
            epoch_d_loss += d_loss.item()
        
        # Print progress
        if (epoch + 1) % 50 == 0 or epoch == 0:
            avg_g_loss = epoch_g_loss / num_samples
            avg_d_loss = epoch_d_loss / num_samples
            print(f"Epoch [{epoch+1}/{args.niter}] | G Loss: {avg_g_loss:.4f} | D Loss: {avg_d_loss:.4f}")
    
    print("\n" + "=" * 70)
    print("Training Complete!")
    print("=" * 70)
    
    # Save models
    output_dir = repo_root / "output" / "diverse_dataset"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    torch.save({
        'generator': generator.state_dict(),
        'discriminator': discriminator.state_dict(),
        'noise_amp': noise_amp,
        'num_channels': num_channels
    }, output_dir / "models.pth")
    
    torch.save(token_list, output_dir / "token_list.pt")
    
    print(f"\n✓ Models saved to: {output_dir}")
    print("\nNext: Generate samples with generate_diverse_samples.py")

if __name__ == "__main__":
    args = parse_args()
    train_diverse_gan(args)
