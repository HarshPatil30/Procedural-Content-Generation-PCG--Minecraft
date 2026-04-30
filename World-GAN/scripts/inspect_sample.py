import torch
from pathlib import Path

p = Path('output/try1_examples/torch_blockdata/0.pt')
print('Inspecting', p)
if not p.exists():
    print('File not found')
    raise SystemExit(1)

data = torch.load(p)
print('Top-level type:', type(data))
if isinstance(data, tuple) or isinstance(data, list):
    print('Tuple/list length:', len(data))
    for i, el in enumerate(data):
        print(f' Element {i}: type={type(el)}, shape={getattr(el,"shape",None)}')
else:
    print('Shape:', getattr(data, 'shape', None))

# If it's a tensor with channel-first one-hot, attempt to print token count
if isinstance(data, (tuple, list)):
    # try to detect where the one-hot tensor and token list may be
    for el in data:
        if hasattr(el, 'shape') and len(el.shape) >= 3:
            c = el.shape[0]
            vol = 1
            for s in el.shape[1:]:
                vol *= s
            print('Detected tensor-like element: channels', c, 'voxels per channel', vol)
        elif isinstance(el, (list, tuple)):
            print('Detected list-like element length', len(el))
        else:
            print('Other element repr:', repr(el)[:200])
