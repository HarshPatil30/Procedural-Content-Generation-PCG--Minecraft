import os, sys
# ensure repo root is on sys.path when running from the scripts folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from loguru import logger
import sys
import wandb

from minecraft.level_utils import read_level as mc_read_level
from train import train
from generate_samples import generate_samples


def run_quick():
    logger.remove()
    logger.add(sys.stdout, colorize=True,
               format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                      + "<level>{level}</level> | "
                      + "<light-black>{file.path}:{line}</light-black> | "
                      + "{message}")

    opt = Config()
    # set inputs to try1 world
    opt.input_dir = 'input/minecraft'
    opt.input_name = 'try1'
    opt.input_area_name = 'try1'
    # small number of iterations for quick smoke-test
    opt.niter = 5
    # process defaults
    opt.process_args()

    # disable wandb to avoid network/file issues during quick test
    run = wandb.init(project="world-gan", config=opt, dir=opt.out, mode='disabled')
    opt.out_ = run.dir

    # Read level and run training
    real = mc_read_level(opt)
    real = real.to(opt.device)
    opt.level_shape = real.shape[2:]

    generators, noise_maps, reals, noise_amplitudes = train(real, opt)

    # generate a few samples
    generate_samples(generators, noise_maps, reals, noise_amplitudes, opt, render_images=False, num_samples=4)


if __name__ == '__main__':
    run_quick()
