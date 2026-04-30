from pathlib import Path
import sys
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
from PyAnvilEditor.pyanvil import World

coords_to_test = [(-320,60,-288), (-320,60,-288), (-328,60,-296), (-166,60,694)]
# note: World.get_block expects (y,z,x) per wrapper but accepts (x,y,z) fallback

with World('try2', str(repo / 'input' / 'minecraft'), debug=True) as w:
    for (x,y,z) in coords_to_test:
        b = w.get_block((y,z,x))
        try:
            s = b.get_state().name
        except Exception:
            s = str(b)
        print(f'Probe ({x},{y},{z}) -> {s}')
