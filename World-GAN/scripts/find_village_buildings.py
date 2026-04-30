"""
Find where the actual village buildings are in the try2 world.
This scans for building blocks like planks, logs, cobblestone, etc.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyAnvilEditor.fix_anvil import *
from anvil import Region
from collections import Counter

# Building-related blocks
BUILDING_BLOCKS = {
    'oak_planks', 'oak_log', 'cobblestone', 'stone_bricks', 'spruce_planks',
    'spruce_log', 'dark_oak_planks', 'dark_oak_log', 'torch', 'oak_door',
    'glass', 'glass_pane', 'oak_fence', 'cobblestone_stairs', 'oak_stairs',
    'crafting_table', 'furnace', 'bed', 'chest', 'oak_slab', 'stone_brick_stairs',
    'stone_brick_slab', 'ladder', 'hay_block', 'wheat', 'composter', 'barrel'
}

print("Scanning try2 world for village buildings...")
print("Center coordinates from user: (-340, 62, 1056)")

# Calculate which region file
cx, cz = -340 >> 4, 1056 >> 4  # Chunk coords
rx, rz = cx >> 5, cz >> 5  # Region coords
print(f"\nRegion file: r.{rx}.{rz}.mca")

region_path = Path('input/minecraft/try2/region') / f'r.{rx}.{rz}.mca'
if not region_path.exists():
    print(f"ERROR: Region file not found: {region_path}")
    sys.exit(1)

region = Region.from_file(str(region_path))

# Scan a 5x5 chunk area around the center
center_cx, center_cz = -340 >> 4, 1056 >> 4
chunk_range = 5

print(f"\nScanning {chunk_range*2+1}x{chunk_range*2+1} chunks around center...")
print("Looking for building blocks...\n")

building_blocks_found = Counter()
chunk_building_counts = {}

for dx in range(-chunk_range, chunk_range + 1):
    for dz in range(-chunk_range, chunk_range + 1):
        cx = center_cx + dx
        cz = center_cz + dz
        
        # Convert to region-local coords
        local_x = cx & 31
        local_z = cz & 31
        
        try:
            chunk = region.get_chunk(local_x, local_z)
            if chunk is None:
                continue
            
            # Count building blocks in this chunk
            chunk_building_count = 0
            
            # Scan Y levels 60-100 for buildings
            for y in range(60, 100):
                for x in range(16):
                    for z in range(16):
                        block = chunk.get_block(x, y, z)
                        block_name = str(block).replace('Block(minecraft:', '').replace(')', '')
                        
                        if block_name in BUILDING_BLOCKS:
                            building_blocks_found[block_name] += 1
                            chunk_building_count += 1
            
            if chunk_building_count > 0:
                # Calculate world coordinates for this chunk
                world_x = cx * 16
                world_z = cz * 16
                chunk_building_counts[(cx, cz, world_x, world_z)] = chunk_building_count
        
        except Exception as e:
            pass

# Sort chunks by building block count
sorted_chunks = sorted(chunk_building_counts.items(), key=lambda x: x[1], reverse=True)

print("=" * 70)
print("CHUNKS WITH BUILDING BLOCKS (sorted by count):")
print("=" * 70)

for (cx, cz, wx, wz), count in sorted_chunks[:20]:
    print(f"Chunk ({cx:3}, {cz:3}) | World coords: ({wx:5}, {wz:5}) | Building blocks: {count:5}")

print("\n" + "=" * 70)
print("BUILDING BLOCKS FOUND:")
print("=" * 70)
for block, count in building_blocks_found.most_common(30):
    print(f"  {block:25} : {count:6}")

if sorted_chunks:
    best_cx, best_cz, best_wx, best_wz = sorted_chunks[0][0]
    best_count = sorted_chunks[0][1]
    
    # Calculate center of best chunk
    center_x = best_wx + 8
    center_z = best_wz + 8
    
    print("\n" + "=" * 70)
    print("RECOMMENDED EXTRACTION COORDINATES:")
    print("=" * 70)
    print(f"Center: ({center_x}, 70, {center_z})")
    print(f"This chunk has {best_count} building blocks")
    print(f"\nFor a 60x40x60 extraction, use:")
    print(f"  python scripts/extract_village_region.py")
    print(f"  (Then update CENTER_X={center_x}, CENTER_Z={center_z} in the script)")
else:
    print("\n⚠ WARNING: No building blocks found in the scanned area!")
    print("The village might be at different coordinates.")
