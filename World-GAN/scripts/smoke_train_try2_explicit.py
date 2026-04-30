import sys
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))

from config import Config
from minecraft.level_utils import read_level as mc_read_level
from train import train
import os
import wandb

# disable wandb
os.environ['WANDB_MODE'] = 'disabled'

cfg = Config().parse_args()
# override CLI values
cfg.input_area_name = 'try2'
cfg.niter = 5
try:
    cfg.process_args()
except Exception:
    pass

# Explicit small bbox around a known non-air point (-320,60,-288)
# shape = (45,20,45): y-range [50,70), z-range [-310,-265), x-range [-342,-297)
explicit_coords = ((50, 70), (-310, -265), (-342, -297))
print('Forcing explicit coords (y,z,x):', explicit_coords)

# set cfg.coords to these tuples (int)
cfg.coords = [(int(a), int(b)) for (a, b) in explicit_coords]

# initialize wandb disabled to avoid errors
try:
    wandb.init(project='world-gan', mode='disabled', config=cfg)
except Exception:
    pass

# read level and show token list
real = mc_read_level(cfg)
print('cfg.token_list (tokens in level):', cfg.token_list)
real = real.to(cfg.device)
cfg.level_shape = real.shape[2:]

# run a short train
gens, maps, reals, amps = train(real, cfg)
print('Training completed (explicit coords)')
