#!/usr/bin/env python3
"""
Generate village samples from trained GAN model.
Simplified version that works with pre-tokenized village data.
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

import os
import torch
from config import Config
import wandb
from models import load_trained_pyramid
from generate_samples import generate_samples


def main():
    dataset_name = "village_dataset"
    model_dir = repo_root / "output" / dataset_name
    output_dir = repo_root / "output" / f"{dataset_name}_examples"
    
    print("="*60)
    print("World-GAN: Generate Village Samples")
    print("="*60)
    
    # Check if trained model exists
    required_files = ["generators.pth", "reals.pth", "noise_maps.pth", "noise_amplitudes.pth"]
    missing = [f for f in required_files if not (model_dir / f).exists()]
    
    if missing:
        print(f"\nERROR: Trained model files not found!")
        print(f"Missing: {', '.join(missing)}")
        print(f"Expected location: {model_dir}")
        print(f"\nPlease run train_village_gan.py first!")
        return 1
    
    print(f"\n✓ Model found: {model_dir}")
    
    # Disable wandb
    os.environ['WANDB_MODE'] = 'disabled'
    
    # Parse config
    cfg = Config().parse_args()
    cfg.input_name = dataset_name
    cfg.input_area_name = dataset_name
    cfg.out = str(model_dir)
    cfg.out_ = str(model_dir)  # Load models from here
    
    # Initialize device and other config (but skip coord loading which will fail)
    cfg.device = torch.device("cpu" if cfg.not_cuda else "cuda:0")
    cfg.manualSeed = 42
    cfg.block2repr = None
    cfg.repr_type = None
    
    # Create output directory for generated samples
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        cfg.process_args()
    except Exception:
        pass
    
    # Load token list from saved model
    token_list = torch.load(str(model_dir / "token_list.pth"))
    cfg.token_list = token_list
    cfg.props = [{} for _ in token_list]
    
    print(f"\nGeneration configuration:")
    print(f"  Model: {model_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Tokens: {len(token_list)}")
    print(f"  Number of samples: {cfg.gen_start_scale if hasattr(cfg, 'gen_start_scale') else 'default'}")
    
    # Initialize wandb (disabled)
    try:
        wandb.init(project='world-gan', mode='disabled', config=cfg, dir=str(output_dir))
    except Exception:
        pass
    
    print(f"\n{'='*60}")
    print("Generating samples...")
    print(f"{'='*60}\n")
    
    # Load trained models (weights_only=False since we trust our own model files)
    generators = torch.load(str(model_dir / "generators.pth"), weights_only=False)
    noise_maps = torch.load(str(model_dir / "noise_maps.pth"), weights_only=False)
    reals = torch.load(str(model_dir / "reals.pth"), weights_only=False)
    noise_amplitudes = torch.load(str(model_dir / "noise_amplitudes.pth"), weights_only=False)
    
    # Now set output for generation
    cfg.out_ = str(output_dir)
    
    # Generate!
    in_s = generate_samples(
        generators, noise_maps, reals, noise_amplitudes, cfg,
        in_s=None,
        gen_start_scale=0,
        num_samples=10,
        render_images=False,
        save_tensors=True,
        save_dir="torch_blockdata"
    )
    
    print(f"\n{'='*60}")
    print("Generation complete!")
    print(f"{'='*60}")
    print(f"\nSamples saved to: {output_dir}")
    
    # Check what was created
    torch_dir = output_dir / "torch_blockdata"
    if torch_dir.exists():
        samples = list(torch_dir.glob("*.pt"))
        print(f"Created {len(samples)} samples in {torch_dir}")
    
    print(f"\nNext step:")
    print(f"  Run write_village_world.py to create playable Minecraft worlds")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
