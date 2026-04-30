#!/usr/bin/env python3
"""Test anvil namespace fix and chunk loading."""
import sys

# Patch anvil namespace BEFORE any anvil imports
import anvil.region
import anvil.chunk
import anvil.block

class AnvilNamespace:
    pass

a = AnvilNamespace()
a.Chunk = anvil.chunk.Chunk
a.Region = anvil.region.Region  
a.Block = anvil.block.Block
a.region = anvil.region
a.chunk = anvil.chunk
a.block = anvil.block

sys.modules['anvil'] = a

# Now test
r = anvil.region.Region.from_file('S:/CEVI/World-GAN/input/minecraft/Gen_FixedTest/region/r.0.0.mca')
print(f'Region loaded: {r}')

c = r.get_chunk(0, 0)
print(f'Chunk (0,0): {c}')
if c:
    print(f'  Chunk coords: x={c.x}, z={c.z}')
    print('SUCCESS!')
else:
    print('FAILED: chunk is None')
