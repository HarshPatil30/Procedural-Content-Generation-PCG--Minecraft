from pathlib import Path
import anvil

rf = Path('input') / 'minecraft' / 'Gen_FixedTest' / 'region'
region_file = rf / 'r.0.0.mca'
print('region file exists:', region_file.exists(), region_file)
reg = anvil.Region.from_file(str(region_file))
ch = reg.get_chunk(0,0)
print('chunk attrs:', [a for a in dir(ch) if not a.startswith('_')])
sec_idx = 64//16
print('sec_idx', sec_idx)
sec = None
if hasattr(ch, 'get_section'):
    try:
        sec = ch.get_section(sec_idx)
        print('got via get_section')
    except Exception as e:
        print('get_section failed', e)
if sec is None and hasattr(ch, 'sections'):
    secs = ch.sections
    print('sections type', type(secs))
    try:
        sec = secs[sec_idx]
        print('got via sections index')
    except Exception as e:
        print('sections index failed', e)
if sec is None and hasattr(ch, 'get_palette'):
    try:
        pal = ch.get_palette(sec_idx)
        print('palette via get_palette len', len(pal))
    except Exception as e:
        print('get_palette failed', e)
print('section:', type(sec))
try:
    if sec is None:
        print('no section')
    else:
        if isinstance(sec, dict):
            print('sec dict keys', list(sec.keys()))
            print('Palette len', len(sec.get('Palette',[])))
            print('BlockStates len', len(sec.get('BlockStates',[])))
        else:
            print('sec attrs', [a for a in dir(sec) if not a.startswith('_')])
            if hasattr(sec,'value') and sec.value is not None:
                print('sec.value keys', list(sec.value.keys()))
            if hasattr(sec,'palette'):
                print('sec.palette len', len(sec.palette) if sec.palette is not None else None)
            if hasattr(sec,'block_states'):
                bs = sec.block_states
                print('sec.block_states len', len(bs) if bs is not None else None)
except Exception as e:
    print('inspect failed', e)
# read block via get_block
try:
    b = ch.get_block(1,64,1)
    print('get_block result:', b, getattr(b,'namespaced',None), getattr(b,'id',None))
except Exception as e:
    print('ch.get_block failed', e)
