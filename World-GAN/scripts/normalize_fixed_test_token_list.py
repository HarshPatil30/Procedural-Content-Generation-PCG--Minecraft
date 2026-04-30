from pathlib import Path
import sys
import torch

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

p = repo / 'input' / 'minecraft' / 'fixed_test'
fn = p / 'token_list.pt'
print('Loading', fn)
tokens = torch.load(str(fn))
print('Original tokens:')
for i, t in enumerate(tokens):
    print(i, repr(t))

new_tokens = []
replaced = 0
for t in tokens:
    if not isinstance(t, str):
        new_tokens.append('minecraft:air')
        replaced += 1
        continue
    s = t
    # detect the PyAnvil Air reprs
    if 'PyAnvilEditor.pyanvil.Air' in s or s.startswith('<PyAnvilEditor.pyanvil.Air'):
        new_tokens.append('minecraft:air')
        replaced += 1
    else:
        new_tokens.append(s)

if replaced > 0:
    torch.save(new_tokens, str(fn))
    print(f'Saved normalized token_list.pt, replaced {replaced} entries')
else:
    print('No replacements necessary')

print('Final tokens:')
for i, t in enumerate(new_tokens):
    print(i, repr(t))
