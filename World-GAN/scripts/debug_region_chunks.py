#!/usr/bin/env python3
"""
Debug script to inspect which chunks exist in region files around the village coordinates.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Fix anvil namespace before importing
import PyAnvilEditor.fix_anvil  # noqa: F401
import anvil


def check_region_chunks(region_file_path):
    """List all non-empty chunks in a region file."""
    print(f"\nChecking region file: {region_file_path.name}")
    
    try:
        region = anvil.Region.from_file(str(region_file_path))
        chunk_count = 0
        chunks = []
        
        # Check all possible chunk positions (32x32)
        for lcx in range(32):
            for lcz in range(32):
                try:
                    chunk = region.get_chunk(lcx, lcz)
                    if chunk is not None:
                        chunk_count += 1
                        chunks.append((lcx, lcz))
                except Exception:
                    pass
        
        print(f"  Found {chunk_count} chunks")
        if chunks:
            print(f"  First 20 chunks: {chunks[:20]}")
        return chunks
    except Exception as e:
        print(f"  Error reading region: {e}")
        return []


def get_region_and_local_coords(world_x, world_z):
    """Get region file and local chunk coordinates within that region."""
    chunk_x = world_x >> 4
    chunk_z = world_z >> 4
    
    region_x = chunk_x >> 5
    region_z = chunk_z >> 5
    
    local_chunk_x = chunk_x & 31
    local_chunk_z = chunk_z & 31
    
    return region_x, region_z, local_chunk_x, local_chunk_z


if __name__ == "__main__":
    # Village coordinates
    vx, vy, vz = -340, 62, 1056
    
    print("="*60)
    print("World-GAN: Debug Region File Chunks")
    print("="*60)
    print(f"\nVillage coordinates: ({vx}, {vy}, {vz})")
    
    # Calculate expected region
    rx, rz, lcx, lcz = get_region_and_local_coords(vx, vz)
    print(f"\nExpected location:")
    print(f"  Chunk coords: ({vx >> 4}, {vz >> 4})")
    print(f"  Region coords: ({rx}, {rz})")
    print(f"  Local chunk: ({lcx}, {lcz})")
    print(f"  Region file: r.{rx}.{rz}.mca")
    
    # Check region directory
    world_path = repo_root / "input" / "minecraft" / "try2"
    region_dir = world_path / "region"
    
    print(f"\nRegion directory: {region_dir}")
    
    # List all region files
    region_files = sorted(region_dir.glob("r.*.*.mca"))
    print(f"\nFound {len(region_files)} region files:")
    for rf in region_files[:10]:
        print(f"  - {rf.name}")
    if len(region_files) > 10:
        print(f"  ... and {len(region_files) - 10} more")
    
    # Check the expected region file
    expected_region = region_dir / f"r.{rx}.{rz}.mca"
    if expected_region.exists():
        print(f"\n✓ Expected region file exists: {expected_region.name}")
        chunks = check_region_chunks(expected_region)
        
        if (lcx, lcz) in chunks:
            print(f"\n✓ Target chunk ({lcx}, {lcz}) EXISTS in region!")
        else:
            print(f"\n✗ Target chunk ({lcx}, {lcz}) NOT FOUND in region")
            print(f"  The village might be in a different location")
    else:
        print(f"\n✗ Expected region file does NOT exist: {expected_region.name}")
    
    # Check neighboring region files
    print("\nChecking neighboring regions...")
    for drx in range(-1, 2):
        for drz in range(-1, 2):
            neighbor_rx = rx + drx
            neighbor_rz = rz + drz
            neighbor_file = region_dir / f"r.{neighbor_rx}.{neighbor_rz}.mca"
            if neighbor_file.exists():
                check_region_chunks(neighbor_file)
    
    print("\n" + "="*60)
