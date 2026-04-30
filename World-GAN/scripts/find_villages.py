#!/usr/bin/env python3
"""
Scan all region files to find areas with high block diversity (likely villages/structures).
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Fix anvil namespace before importing
import PyAnvilEditor.fix_anvil  # noqa: F401
import anvil


def analyze_chunk(chunk, cx, cz):
    """Analyze a chunk for interesting features."""
    try:
        unique_blocks = set()
        sample_count = 0
        
        # Sample blocks at different heights
        for y in range(60, 80, 5):  # Sample every 5 blocks from y=60 to y=80
            for lx in range(0, 16, 4):  # Sample every 4 blocks
                for lz in range(0, 16, 4):
                    try:
                        block = chunk.get_block(lx, y, lz)
                        if hasattr(block, 'id'):
                            block_name = str(block.id)
                        else:
                            block_name = str(block)
                        unique_blocks.add(block_name)
                        sample_count += 1
                    except:
                        pass
        
        # Calculate world coordinates for this chunk
        world_x = cx * 16
        world_z = cz * 16
        
        return len(unique_blocks), sample_count, world_x, world_z, unique_blocks
    except Exception as e:
        return 0, 0, 0, 0, set()


def scan_region_file(region_file_path):
    """Scan a region file for interesting chunks."""
    try:
        region = anvil.Region.from_file(str(region_file_path))
        
        # Parse region coordinates from filename (r.{rx}.{rz}.mca)
        parts = region_file_path.stem.split('.')
        rx = int(parts[1])
        rz = int(parts[2])
        
        interesting_chunks = []
        
        for lcx in range(32):
            for lcz in range(32):
                try:
                    chunk = region.get_chunk(lcx, lcz)
                    if chunk is not None:
                        # Calculate global chunk coordinates
                        global_cx = rx * 32 + lcx
                        global_cz = rz * 32 + lcz
                        
                        diversity, samples, wx, wz, blocks = analyze_chunk(chunk, global_cx, global_cz)
                        
                        # Consider chunks with >10 unique block types as interesting
                        if diversity > 10:
                            interesting_chunks.append((diversity, global_cx, global_cz, wx, wz, blocks))
                except Exception:
                    pass
        
        return interesting_chunks
    except Exception:
        return []


if __name__ == "__main__":
    print("="*60)
    print("World-GAN: Find Villages/Structures")
    print("="*60)
    
    world_path = repo_root / "input" / "minecraft" / "try2"
    region_dir = world_path / "region"
    
    print(f"\nScanning region files in: {region_dir}")
    
    region_files = sorted(region_dir.glob("r.*.*.mca"))
    print(f"Found {len(region_files)} region files to scan\n")
    
    all_interesting = []
    
    for i, region_file in enumerate(region_files):
        print(f"Scanning {region_file.name}... ({i+1}/{len(region_files)})")
        interesting = scan_region_file(region_file)
        if interesting:
            all_interesting.extend(interesting)
            print(f"  Found {len(interesting)} interesting chunks")
    
    if all_interesting:
        # Sort by diversity (most diverse first)
        all_interesting.sort(reverse=True)
        
        print(f"\n{'='*60}")
        print(f"Top 20 most diverse chunks (likely villages/structures):")
        print(f"{'='*60}\n")
        
        for i, (diversity, cx, cz, wx, wz, blocks) in enumerate(all_interesting[:20]):
            print(f"{i+1}. Chunk ({cx}, {cz}) - World coords (~{wx}, ~{wz})")
            print(f"   Block diversity: {diversity} unique types")
            print(f"   Sample blocks: {', '.join(sorted(list(blocks))[:5])}, ...")
            print()
    else:
        print("\n✗ No interesting chunks found")
    
    print("="*60)
