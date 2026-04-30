from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from anvil import Region

region_file = repo = str(repo / 'input' / 'minecraft' / 'Gen_FixedTest' / 'region' / 'r.0.0.mca')
print('Region file:', region_file)
reg = Region.from_file(region_file)
print('Region object type:', type(reg))
print('\nRegion attrs/methods (sample):')
print([a for a in dir(reg) if not a.startswith('_')][:60])

# pick a chunk that exists
try:
    chunk = reg.get_chunk(0, 0)
    print('\nChunk object type:', type(chunk))
    print('Chunk attrs/methods (sample):')
    print([a for a in dir(chunk) if not a.startswith('_')][:200])
    # if set_block exists, show signature via inspect
    import inspect
    if hasattr(chunk, 'set_block'):
        print('\nset_block signature:')
        print(inspect.signature(chunk.set_block))
    else:
        print('\nNo set_block method on chunk')
    print('\nchunk __dict__ keys:')
    print(list(chunk.__dict__.keys()))
    try:
        import pprint
        print('\nchunk.data type:', type(chunk.data))
        pprint.pprint(chunk.data, width=120)
    except Exception as e:
        print('error printing chunk.data:', e)
except Exception as e:
    print('Error getting chunk:', e)

# print a sample block read
try:
    b = chunk.get_block(0, 64, 0)
    print('\nSample get_block type:', type(b))
    print('repr:', b)
    if hasattr(b, 'namespaced'):
        print('namespaced:', b.namespaced)
    if hasattr(b, 'id'):
        print('id:', b.id)
    if hasattr(b, 'state'):
        print('state keys:', list(b.state.keys())[:10])
except Exception as e:
    print('Error reading sample block:', e)

print('\nDone.')
