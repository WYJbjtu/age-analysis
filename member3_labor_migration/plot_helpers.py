"""Validated inputs and deterministic exports for Member 3's actual figure entry points."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
MEMBER=ROOT/'member3_labor_migration'
OUT=MEMBER/'figures'
KEY=['country','region_id','year']
COLORS={'USA':'#2788ae','JPN':'#8551a6'}


def load_panel():
    frames={name:pd.read_csv(ROOT/f'data/processed/{name}.csv',dtype={'region_id':str})
            for name in ['demographics','industry','labor_migration']}
    for name,frame in frames.items():
        if frame.duplicated(KEY).any():raise ValueError(f'{name}: duplicate keys')
    frame=frames['demographics'].merge(frames['industry'],on=KEY,how='outer',validate='one_to_one')
    frame=frame.merge(frames['labor_migration'],on=KEY,how='left',validate='one_to_one')
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv')
    frame=frame.merge(lookup[['country','region_id','region_name']],on=KEY[:2],how='left',validate='many_to_one')
    if frame.region_name.isna().any():raise ValueError('Unknown region before plotting')
    return frame


def setup():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none',
                         'svg.hashsalt':'member3-repaired','axes.spines.top':False,'axes.spines.right':False})


def cross_section(frame,year=2022):
    sample=frame[frame.year==year].copy()
    if sample.groupby('country').size().to_dict()!={'JPN':47,'USA':51}:raise ValueError('Incomplete cross-section')
    if sample[['age65_share_pct','unemployment_rate_pct']].isna().any().any():raise ValueError('Missing plotted observation')
    return sample


def save(fig,stem,samples,note):
    OUT.mkdir(parents=True,exist_ok=True)
    for extension in ['png','svg']:
        path=OUT/f'{stem}.{extension}'
        kwargs={'metadata':{'Date':None}} if extension=='svg' else {}
        fig.savefig(path,dpi=300,facecolor='white',**kwargs)
        # Historical root aliases now contain the repaired pixels as well.
        alias=MEMBER/path.name
        if alias.exists():shutil.copyfile(path,alias)
    plt.close(fig)
    record={'figure':stem,'note':note,'samples':samples,
            'input_sha256':{name:hashlib.sha256((ROOT/f'data/processed/{name}.csv').read_bytes()).hexdigest()
                            for name in ['demographics','industry','labor_migration']}}
    (OUT/f'{stem}.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('Exported',stem)


def check_bounds(ax,x,y):
    xmin,xmax=ax.get_xlim();ymin,ymax=ax.get_ylim()
    if not (np.isfinite(x).all() and np.isfinite(y).all() and
            ((x>=xmin)&(x<=xmax)&(y>=ymin)&(y<=ymax)).all()):
        raise ValueError('A plotted observation falls outside the visible axes')
