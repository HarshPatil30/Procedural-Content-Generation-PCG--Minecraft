#!/usr/bin/env python3
"""Test manual NBT save for region."""
from pathlib import Path
import sys
import shutil
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

import anvil
from nbt import nbt

WORLD = 'Gen_FixedTest'
WORLD_ROOT = repo / 'input' / 'minecraft'

world_path = Path(WORLD_ROOT) / WORLD
region_path = world_path / 'region'
region_file = region_path / 'r.0.0.mca'

# Backup
backup_file = region_path / 'r.0.0.mca.backup'
if not backup_file.exists():
    shutil.copy(region_file, backup_file)
    print(f'Created backup: {backup_file}')

print(f'Opening region: {region_file}')
reg = anvil.Region.from_file(str(region_file))

chunk = reg.get_chunk(0, 0)
print(f'Got chunk (0, 0)')

# Modify a section - add Section Y=4
sections_tag = chunk.data['Sections']
print(f'Current sections: {len(sections_tag)}')

# Create section Y=4
new_section = nbt.TAG_Compound()
new_section['Y'] = nbt.TAG_Byte(4)
new_section['Palette'] = nbt.TAG_List(name='Palette', type=nbt.TAG_Compound)
new_section['BlockStates'] = nbt.TAG_Long_Array(name='BlockStates')

# Add stone to palette
stone_entry = nbt.TAG_Compound()
stone_entry['Name'] = nbt.TAG_String('minecraft:stone')
new_section['Palette'].append(stone_entry)

# Initialize BlockStates (all zeros = all palette index 0)
new_section['BlockStates'].value = [0] * 256  # 4096 * 4 bits / 64

sections_tag.append(new_section)
print(f'Added section Y=4, sections now: {len(sections_tag)}')

# Try to write the region back
# anvil-parser doesn't have save(), so we need to manually write the chunk NBT
print('\nAttempting to write region file...')

# The Region object stores chunk data - we need to update it
try:
    # Get chunk coordinates in region (0-31, 0-31)
    chunk_x = chunk.x % 32
    chunk_z = chunk.z % 32
    print(f'Chunk region coords: ({chunk_x}, {chunk_z})')
    
    # Write chunk NBT back to region data
    # This is hacky but anvil-parser doesn't expose a save API
    import struct
    import gzip
    from io import BytesIO
    
    # Serialize chunk NBT
    out = BytesIO()
    chunk_nbt = nbt.NBTFile()
    chunk_nbt.tags.append(chunk.data)
    chunk_nbt.write_file(buffer=out)
    chunk_data = out.getvalue()
    
    # Compress with gzip
    compressed = BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb') as gz:
        gz.write(chunk_data)
    compressed_data = compressed.getvalue()
    
    # Calculate location (chunks in region file)
    print(f'Compressed chunk size: {len(compressed_data)} bytes')
    
    # Write to region file manually
    # This requires understanding the MCA format
    print('Writing to region file requires low-level MCA manipulation')
    print('anvil-parser is read-only!')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
