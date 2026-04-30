import pickle
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'
with open(p, 'rb') as f:
    d = pickle.load(f)
import pprint
pprint.pprint(d)
print('\n--- ruins coords ---')
print(d.get('ruins'))
