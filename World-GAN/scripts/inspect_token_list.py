from pathlib import Path
import sys
import torch
from collections import Counter

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

p = repo / 'input' / 'minecraft' / 'fixed_test'

tokens = torch.load(str(p / 'token_list.pt'))
print('Loaded token_list of length', len(tokens))

# show first 40 entries
for i, t in enumerate(tokens[:40]):
    print(i, type(t), repr(t))

non_strings = [(i, t) for i, t in enumerate(tokens) if not isinstance(t, str)]
print('\nNon-string token count:', len(non_strings))
if non_strings:
    print('Samples:')
    for i, t in non_strings[:10]:
        print(i, repr(t))

# histogram by string name (use str() for non-strings)
names = [t if isinstance(t, str) else str(t) for t in tokens]
cnt = Counter(names)
print('\nTop tokens:')
for name, c in cnt.most_common(20):
    print(f"{name}: {c}")
