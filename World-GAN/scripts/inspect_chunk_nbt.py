#!/usr/bin/env python3
import sys
sys.path.insert(0, 'S:/CEVI/World-GAN')
import PyAnvilEditor.fix_anvil
from anvil.region import Region

r = Region.from_file('S:/CEVI/World-GAN/input/minecraft/Gen_FixedTest/region/r.0.0.mca.backup')
c = r.get_chunk(0, 0)
print('Chunk NBT root-level tags:')
for k, v in c.data.items():
    print(f'  {k}: {type(v).__name__}')
