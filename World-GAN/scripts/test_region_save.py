#!/usr/bin/env python3
"""Test region save methods."""
from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

import anvil

WORLD = 'Gen_FixedTest'
WORLD_ROOT = repo / 'input' / 'minecraft'

world_path = Path(WORLD_ROOT) / WORLD
region_path = world_path / 'region'
region_file = region_path / 'r.0.0.mca'

print(f'Opening region: {region_file}')
reg = anvil.Region.from_file(str(region_file))

print(f'Region type: {type(reg)}')
print(f'Region attributes: {[x for x in dir(reg) if not x.startswith("_")]}')

# Check available save methods
if hasattr(reg, 'save'):
    print('reg.save exists')
    print(f'  signature: {reg.save}')
if hasattr(reg, 'write_chunk'):
    print('reg.write_chunk exists')
    print(f'  signature: {reg.write_chunk}')
if hasattr(reg, 'save_in_place'):
    print('reg.save_in_place exists')

chunk = reg.get_chunk(0, 0)
if chunk:
    print(f'\nChunk type: {type(chunk)}')
    print(f'Chunk dir: {[x for x in dir(chunk) if not x.startswith("_")]}')
