"""
Scan try2 world to find what region files exist and sample diverse locations.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyAnvilEditor.fix_anvil import *
from anvil import Region
import random

print("Scanning try2 world region files...\n")

region_dir = Path("input/minecraft/try2/region")
region_files = list(region_dir.glob("r.*.mca"))

print(f"Found {len(region_files)} region files:")
for rf in sorted(region_files):
    size = rf.stat().st_size
    if size > 4096:  # Not empty
        print(f"  {rf.name} ({size:,} bytes)")

# Parse region coords
valid_regions = []
for rf in region_files:
    if rf.stat().st_size > 4096:
        parts = rf.stem.split('.')
        rx, rz = int(parts[1]), int(parts[2])
        valid_regions.append((rx, rz))

print(f"\n{len(valid_regions)} non-empty regions")

# Sample diverse chunks from each region
sample_locations = []
samples_per_region = 3

for rx, rz in valid_regions[:5]:  # Limit to first 5 regions
    region_file = region_dir / f"r.{rx}.{rz}.mca"
    print(f"\nScanning region r.{rx}.{rz}...")
    
    try:
        region = Region.from_file(str(region_file))
        
        # Try random chunks
        for attempt in range(samples_per_region * 3):
            local_x = random.randint(0, 31)
            local_z = random.randint(0, 31)
            
            try:
                chunk = region.get_chunk(local_x, local_z)
                if chunk:
                    # Convert to world coords
                    chunk_x = rx * 32 + local_x
                    chunk_z = rz * 32 + local_z
                    world_x = chunk_x * 16 + 8
                    world_z = chunk_z * 16 + 8
                    
                    # Check if chunk has blocks
                    test_block = chunk.get_block(8, 70, 8)
                    block_name = str(test_block)
                    
                    if 'air' not in block_name.lower():
                        sample_locations.append({
                            'x': world_x,
                            'y': 70,
                            'z': world_z,
                            'region': f"r.{rx}.{rz}",
                            'sample_block': block_name
                        })
                        print(f"  ✓ Chunk ({chunk_x}, {chunk_z}) -> World ({world_x}, 70, {world_z}) - {block_name}")
                        
                        if len([s for s in sample_locations if s['region'] == f"r.{rx}.{rz}"]) >= samples_per_region:
                            break
            except:
                continue
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n{'='*70}")
print(f"FOUND {len(sample_locations)} VALID SAMPLE LOCATIONS")
print(f"{'='*70}\n")

for i, loc in enumerate(sample_locations):
    print(f"{i+1:2}. ({loc['x']:5}, {loc['y']:3}, {loc['z']:5}) - Region: {loc['region']:10} - Sample: {loc['sample_block']}")

# Save to file for extraction script
output = []
for i, loc in enumerate(sample_locations):
    output.append(f"    ({loc['x']}, {loc['y']}, {loc['z']})")

print(f"\n{'='*70}")
print("COORDINATES FOR EXTRACTION SCRIPT:")
print(f"{'='*70}")
print("sample_centers = [")
for line in output[:20]:  # Limit to 20 samples
    print(line + ",")
print("]")
