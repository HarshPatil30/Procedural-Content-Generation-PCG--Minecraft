import pickle
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
P = repo / 'input' / 'minecraft' / 'primordial_coords_dict.pkl'
print('Pickle:', P)
with open(P,'rb') as f:
    d = pickle.load(f)
print('Before try2:', d.get('try2'))
if 'try2' in d:
    # assume stored as ((x0,x1),(y0,y1),(z0,z1)) -> need ((y0,y1),(z0,z1),(x0,x1))
    (x0,x1),(y0,y1),(z0,z1) = d['try2']
    new = ((y0,y1),(z0,z1),(x0,x1))
    d['try2'] = new
    with open(P,'wb') as f:
        pickle.dump(d,f)
    print('Updated try2 to:', new)
else:
    print('No try2 key found')
