import sys
from pathlib import Path
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
from PyAnvilEditor.pyanvil import World

def quick_scan():
    world = 'try2'
    wroot = repo / 'input' / 'minecraft'
    with World(world, str(wroot)) as w:
        # coarse bbox written earlier by compute_refine_update: ((-512,1023),(0,256),(-512,1023))
        x0, x1 = -512, 1023
        z0, z1 = -512, 1023
        # sample around typical surface Y levels first
        y_samples = list(range(60, 80, 4))
        stride = 32
        found_any = False
        for y in y_samples:
            for x in range(x0, x1+1, stride):
                for z in range(z0, z1+1, stride):
                    b = w.get_block((y, z, x))
                    try:
                        name = b.get_state().name
                    except Exception:
                        name = str(b)
                    if 'air' not in str(name).lower():
                        print('Found non-air at', (x,y,z), 'block:', name)
                        found_any = True
                        return
        if not found_any:
            print('No non-air found in quick surface scan (stride=32, y 60-76).')

if __name__ == '__main__':
    quick_scan()
