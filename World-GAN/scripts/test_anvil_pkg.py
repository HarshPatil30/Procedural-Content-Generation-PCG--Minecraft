#!/usr/bin/env python3
"""Test the 'anvil' package (not anvil-parser) for writing."""
from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

# Try both packages
try:
    import anvil as anvil_pkg
    print(f'anvil package: {anvil_pkg}')
    print(f'anvil package file: {anvil_pkg.__file__}')
    print(f'anvil package dir: {[x for x in dir(anvil_pkg) if not x.startswith("_")]}')
    
    # Check for Block, Region, etc.
    if hasattr(anvil_pkg, 'Anvil'):
        print('\nanvil.Anvil found')
        print(f'  attributes: {[x for x in dir(anvil_pkg.Anvil) if not x.startswith("_")]}')
        
        # Try to instantiate
        from pathlib import Path
        WORLD_ROOT = Path(__file__).resolve().parents[1] / 'input' / 'minecraft'
        WORLD = 'Gen_FixedTest'
        try:
            w = anvil_pkg.Anvil(str(WORLD_ROOT / WORLD))
            print(f'  Anvil world created: {w}')
            print(f'  Anvil world methods: {[x for x in dir(w) if not x.startswith("_") and callable(getattr(w, x))]}')
        except Exception as e:
            print(f'  Could not create Anvil world: {e}')
    
    if hasattr(anvil_pkg, 'Region'):
        print('\nanvil.Region found')
        print(f'  attributes: {[x for x in dir(anvil_pkg.Region) if not x.startswith("_")]}')
    if hasattr(anvil_pkg, 'EmptyRegion'):
        print('anvil.EmptyRegion found')
    if hasattr(anvil_pkg, 'Block'):
        print('anvil.Block found')
        
except ImportError as e:
    print(f'Could not import anvil: {e}')
