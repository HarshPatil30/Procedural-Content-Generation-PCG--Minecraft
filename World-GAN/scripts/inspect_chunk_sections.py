from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from anvil import Region

reg = Region.from_file(str(repo / 'input' / 'minecraft' / 'Gen_FixedTest' / 'region' / 'r.0.0.mca'))
chunk = reg.get_chunk(0,0)
print('Chunk x,z:', chunk.x, chunk.z)
sections = []
for i in range(16):
    try:
        sec = chunk.get_section(i)
        if sec is None:
            continue
        print('\nSection index:', i)
        print('Section dir sample:', [a for a in dir(sec) if not a.startswith('_')])
        # inspect common properties
        try:
            v = sec.value
            print('  value type:', type(v))
            try:
                print('  value keys sample:', list(v.keys())[:10])
            except Exception:
                pass
        except Exception as e:
            print('  no .value:', e)
        try:
            vals = sec.values()
            print('  values() type:', type(vals))
        except Exception:
            pass
    except Exception as e:
        print('  error accessing section', i, e)

print('\nChunk.get_palette() sample:', chunk.get_palette()[:10] if hasattr(chunk, 'get_palette') else 'no')

print('\nDone')
