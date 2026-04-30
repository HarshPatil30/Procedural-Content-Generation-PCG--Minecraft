import sys
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from config import Config
from minecraft.level_utils import read_level as mc_read_level
from train import train
import torch
import os
import wandb

# disable wandb via env
os.environ['WANDB_MODE'] = 'disabled'

cfg = Config().parse_args()
# override CLI values
cfg.input_area_name = 'try2'
cfg.niter = 5
try:
    cfg.process_args()
except Exception:
    pass

# compute a small centered cube inside coords
coords = cfg.coords  # already computed from pickle
# coords is list of (start,end) tuples for y,z,x
(y0,y1),(z0,z1),(x0,x1) = coords
shape = (45,20,45)
# center
cx = (x0 + x1)//2
cz = (z0 + z1)//2
cy = max(y0, min(63, (y0+y1)//2))
# build small bbox
sx0 = cx - shape[0]//2
sx1 = sx0 + shape[0]
sy0 = cy
sy1 = sy0 + shape[1]
sz0 = cz - shape[2]//2
sz1 = sz0 + shape[2]

small_coords = ((sy0, sy1), (sz0, sz1), (sx0, sx1))
print('Using small coords:', small_coords)

# override
cfg.coords = [ (int(a), int(b)) for (a,b) in small_coords ]

# read level (read_level sets cfg.token_list and cfg.props)
real = mc_read_level(cfg)
uniques = cfg.token_list
props = cfg.props
print('Tokens in small level:', uniques)
real = real.to(cfg.device)
cfg.level_shape = real.shape[2:]

# run train (short) - train() expects (real,opt) and returns models
try:
    # initialize wandb in disabled mode so train can call wandb.log/save safely
    wandb.init(project="world-gan", mode="disabled", config=cfg)
except Exception:
    pass

gens, maps, reals, amps = train(real, cfg)
print('Training finished')
