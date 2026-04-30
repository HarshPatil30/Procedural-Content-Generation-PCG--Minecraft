import sys
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

import os
import torch
from config import Config
import wandb
from train import train

# disable wandb
os.environ['WANDB_MODE'] = 'disabled'

cfg = Config().parse_args()
# override to use fixed_test
cfg.input_area_name = 'fixed_test'
try:
    cfg.process_args()
except Exception:
    pass

# load saved one-hot and token list
p = repo / 'input' / 'minecraft' / 'fixed_test'
real = torch.load(str(p / 'real_bdata.pt'))
tokens = torch.load(str(p / 'token_list.pt'))
print('Loaded real_bdata shape:', real.shape)
print('Loaded token_list length:', len(tokens))
print('Tokens:', tokens)

# configure cfg to use these tokens
cfg.token_list = tokens
cfg.props = [{} for _ in tokens]

# ensure real is on device and shape expected by train (train expects real with batch dim?)
# In repo, train() expects `real` to be torch tensor where shape[0]=1 and shape[1]=n_tokens
# Our saved shape is (1, n_tokens, y, z, x) which matches expectations for block2vec/one-hot

real = real.to(cfg.device)
cfg.level_shape = real.shape[2:]

# init disabled wandb so train's wandb.log won't error
try:
    wandb.init(project='world-gan', mode='disabled', config=cfg)
except Exception:
    pass

# Run short training
gens, maps, reals, amps = train(real, cfg)
print('Finished training on fixed_test')
