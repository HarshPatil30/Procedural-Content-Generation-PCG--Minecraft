#!/usr/bin/env python3
"""
Generate village samples using the trained GAN.
Wrapper around generate_samples.py for village dataset.
"""
import sys
import subprocess
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]


def main():
    print("="*60)
    print("World-GAN: Generate Village Samples")
    print("="*60)
    
    # Check if model exists
    model_dir = repo_root / "output" / "village_dataset"
    required_files = [
        "generators.pth",
        "reals.pth",
        "noise_maps.pth",
        "noise_amplitudes.pth"
    ]
    
    missing = []
    for fname in required_files:
        if not (model_dir / fname).exists():
            missing.append(fname)
    
    if missing:
        print("\nERROR: Trained model files not found!")
        print(f"Missing: {', '.join(missing)}")
        print(f"Expected location: {model_dir}")
        print("\nPlease run train_village_gan.py first!")
        return 1
    
    print(f"\n✓ Model found: {model_dir}")
    
    # Generation configuration
    num_samples = 10
    
    print(f"\nGeneration configuration:")
    print(f"  input_name  = village_dataset")
    print(f"  num_samples = {num_samples}")
    print(f"  out_dir     = output/village_dataset_examples")
    
    # Build command
    python_exe = repo_root / ".venv" / "Scripts" / "python.exe"
    gen_script = repo_root / "generate_samples.py"
    
    cmd = [
        str(python_exe),
        str(gen_script),
        "--input_name", "village_dataset",
        "--out_", "output/village_dataset_examples",
        "--num_samples", str(num_samples),
        "--save_tensors"
    ]
    
    print(f"\nExecuting: {' '.join(cmd[:3])} ...")
    print("\nGenerating samples...")
    print("="*60)
    
    # Run generation
    try:
        result = subprocess.run(cmd, cwd=str(repo_root))
        
        if result.returncode == 0:
            output_dir = repo_root / "output" / "village_dataset_examples" / "torch_blockdata"
            print("\n" + "="*60)
            print("Sample generation complete!")
            print("="*60)
            print(f"\nGenerated {num_samples} samples in:")
            print(f"  {output_dir}")
            print(f"\nFiles:")
            if output_dir.exists():
                samples = sorted(output_dir.glob("*.pt"))
                for sample in samples:
                    size = sample.stat().st_size / 1024
                    print(f"  - {sample.name:15s} ({size:6.1f} KB)")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\nGeneration interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
