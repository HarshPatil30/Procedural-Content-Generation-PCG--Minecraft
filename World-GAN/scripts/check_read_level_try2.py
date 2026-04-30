from pathlib import Path
import sys
import pickle

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
from minecraft.level_utils import read_level_from_file


def main():
    PICKLE = repo / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'
    with open(PICKLE, 'rb') as f:
        d = pickle.load(f)
    print('pickle try2:', d.get('try2'))

    bbox = d.get('try2')
    coords = bbox
    print('Using coords:', coords)

    oh_level, uniques, props = read_level_from_file(str(repo / 'input' / 'minecraft'), 'try2', coords, None, None, debug=True)
    print('uniques:', uniques)

    # summarize counts if one-hot returned
    try:
        lvl = oh_level
        if isinstance(lvl, tuple):
            lvl = lvl[0]
        if getattr(lvl, 'dim', lambda: 0)() == 5:
            arr = lvl[0]
            counts = {}
            for i, u in enumerate(uniques):
                c = int(arr[i].sum().item())
                if c > 0:
                    counts[u] = c
            print('nonzero token counts:', counts)
    except Exception as e:
        print('Could not summarize level:', e)


if __name__ == '__main__':
    main()
