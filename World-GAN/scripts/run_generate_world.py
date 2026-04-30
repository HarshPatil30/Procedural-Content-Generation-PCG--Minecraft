#!/usr/bin/env python3
"""Wrapper script to run the complete World-GAN world generation pipeline."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
scripts_dir = repo / 'scripts'

def main():
    print('=' * 70)
    print('World-GAN: Complete World Generation Pipeline')
    print('=' * 70)
    
    # Check for gen_out.pt
    gen_out = repo / 'gen_out.pt'
    if not gen_out.exists():
        print(f'\nWARNING: {gen_out} not found!')
        print('This file should contain the generated blocks from the GAN.')
        print('Continuing anyway with fixed_test data...\n')
    else:
        print(f'\n✓ Found {gen_out.name}')
    
    # Step 1: Run world writer
    print('\n' + '=' * 70)
    print('STEP 1: Writing Generated World')
    print('=' * 70)
    writer_script = scripts_dir / 'write_fixed_test_world.py'
    if not writer_script.exists():
        print(f'ERROR: {writer_script} not found!')
        return 1
    
    result = subprocess.run([sys.executable, str(writer_script)])
    if result.returncode != 0:
        print(f'\nERROR: World writer failed with code {result.returncode}')
        return result.returncode
    
    # Step 2: Run world verifier
    print('\n' + '=' * 70)
    print('STEP 2: Verifying Generated World')
    print('=' * 70)
    verifier_script = scripts_dir / 'verify_gen_fixedtest_world.py'
    if not verifier_script.exists():
        print(f'\nWARNING: {verifier_script} not found!')
        print('Skipping verification step.')
    else:
        result = subprocess.run([sys.executable, str(verifier_script)])
        if result.returncode != 0:
            print(f'\nWARNING: Verifier returned code {result.returncode}')
    
    # Final instructions
    print('\n' + '=' * 70)
    print('PIPELINE COMPLETE')
    print('=' * 70)
    print('\nTo play the generated world in Minecraft:')
    print('  1. Locate your generated world folder:')
    print(f'     {repo / "input" / "minecraft" / "Gen_FixedTest"}')
    print('  2. Copy it to your Minecraft saves folder:')
    print('     Windows: %APPDATA%\\.minecraft\\saves\\')
    print('     Mac: ~/Library/Application Support/minecraft/saves/')
    print('     Linux: ~/.minecraft/saves/')
    print('  3. Launch Minecraft 1.16.x')
    print('  4. Open the "Gen_FixedTest" world')
    print('\nExample Windows command:')
    print(f'  xcopy /E /I "{repo / "input" / "minecraft" / "Gen_FixedTest"}" "%APPDATA%\\.minecraft\\saves\\Gen_FixedTest"')
    print()
    
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
