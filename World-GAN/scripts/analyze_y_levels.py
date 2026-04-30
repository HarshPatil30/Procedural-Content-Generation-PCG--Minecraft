"""
Analyze Y-levels to find where village buildings are concentrated.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyAnvilEditor.fix_anvil import *
from anvil import Region

BUILDING_BLOCKS = {
    'oak_planks', 'oak_log', 'cobblestone', 'cobblestone_stairs',
    'oak_fence', 'oak_door', 'glass_pane', 'oak_stairs'
}

print("Analyzing Y-levels for building density...")
print("Center: (-296, 1080)\n")

region = Region.from_file('input/minecraft/try2/region/r.-1.2.mca')

# Get chunks around center
cx, cz = -296 >> 4, 1080 >> 4
local_x, local_z = cx & 31, cz & 31

y_level_stats = {}

# Check 3x3 chunks around center
for dx in range(-1, 2):
    for dz in range(-1, 2):
        try:
            chunk = region.get_chunk((local_x + dx) & 31, (local_z + dz) & 31)
            if not chunk:
                continue
            
            # Count blocks at each Y level
            for y in range(50, 100):
                if y not in y_level_stats:
                    y_level_stats[y] = {'building': 0, 'total': 0}
                
                for x in range(16):
                    for z in range(16):
                        block = str(chunk.get_block(x, y, z))
                        block_name = block.replace('Block(minecraft:', '').replace(')', '')
                        
                        y_level_stats[y]['total'] += 1
                        if any(b in block_name for b in BUILDING_BLOCKS):
                            y_level_stats[y]['building'] += 1
        except:
            pass

print("=" * 70)
print("Y-LEVEL ANALYSIS (building block density)")
print("=" * 70)

for y in sorted(y_level_stats.keys()):
    stats = y_level_stats[y]
    if stats['total'] > 0:
        percent = (stats['building'] / stats['total']) * 100
        if percent > 0:
            print(f"Y={y:3}: {stats['building']:4} building blocks / {stats['total']:5} total ({percent:5.2f}%)")

# Find best range
best_ranges = []
for start_y in range(60, 85):
    end_y = start_y + 40
    total_building = sum(y_level_stats.get(y, {}).get('building', 0) for y in range(start_y, end_y))
    total_all = sum(y_level_stats.get(y, {}).get('total', 0) for y in range(start_y, end_y))
    if total_all > 0:
        percent = (total_building / total_all) * 100
        best_ranges.append((start_y, end_y, total_building, percent))

best_ranges.sort(key=lambda x: -x[2])

print("\n" + "=" * 70)
print("BEST 40-BLOCK HEIGHT RANGES")
print("=" * 70)
for start_y, end_y, count, percent in best_ranges[:5]:
    print(f"Y {start_y}-{end_y}: {count:5} building blocks ({percent:.2f}% density)")
