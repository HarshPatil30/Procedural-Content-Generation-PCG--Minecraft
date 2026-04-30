from pathlib import Path
import torch

p = Path(__file__).resolve().parents[1] / 'input' / 'minecraft' / 'fixed_test'
print('Loading', p / 'real_bdata.pt')
obj = torch.load(str(p / 'real_bdata.pt'))
print('Current dtype:', obj.dtype)
obj_f = obj.float()
print('Converted dtype:', obj_f.dtype)
torch.save(obj_f, str(p / 'real_bdata.pt'))
print('Overwrote with float32 tensor at', p / 'real_bdata.pt')
