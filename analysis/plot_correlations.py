"""M4: Plot pooled and country-specific region-level correlations for one selected year.

Do not interpret ecological correlations causally. Each region is one unweighted observation.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from aging_economies.comparability import require_comparable_pool
DATA = ROOT / 'data/processed/merged_analysis.csv'
OUT = ROOT / 'analysis/figures'
LABELS = {'USA':'United States', 'JPN':'Japan'}


def correlation_summary(frame, x, y, label):
    require_comparable_pool(frame,[x,y])
    valid = frame[[x,y]].dropna().copy()
    n = len(valid)
    if n < 3 or valid[x].nunique() < 2 or valid[y].nunique() < 2:
        return f'{label}: insufficient nonconstant observations (n={n})', None
    r = valid[x].corr(valid[y], method='pearson')
    rho = valid[x].corr(valid[y], method='spearman')
    return f'{label}: n={n}; Pearson r={r:.3f}; Spearman rho={rho:.3f}', (valid, r)


def main(year, response, country=None):
    if not DATA.exists():
        raise SystemExit('Run `python scripts/merge_core.py` after Members 1 and 2 submit data.')
    df = pd.read_csv(DATA)
    x='age65_share_pct'; y=response
    if any(col not in df.columns for col in [x,y,'population_industry_match']):
        raise SystemExit('Required columns missing from merged table.')
    df = df.loc[(df['year']==year)&(df['population_industry_match']=='both')].copy()
    if country:
        df=df.loc[df.country==country].copy()
    require_comparable_pool(df,[x,y])
    if df.empty:
        raise SystemExit(f'No matched rows for {year}.')
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'repaired-shared-correlation','svg.fonttype':'none'})
    countries = [(LABELS[country],df)] if country else [('Combined',df),('United States',df.loc[df.country=='USA']),('Japan',df.loc[df.country=='JPN'])]
    OUT.mkdir(parents=True,exist_ok=True)
    fig, axes=plt.subplots(1,len(countries),figsize=(13 if not country else 6,4.8),sharex=True,sharey=True,layout='constrained',squeeze=False)
    axes=axes.ravel()
    for ax,(title,frame) in zip(axes,countries):
        text,fit = correlation_summary(frame,x,y,title)
        print(text)
        for c,sub in frame.groupby('country'):
            ax.scatter(sub[x],sub[y],alpha=.75,label=LABELS.get(c,c),s=30,color={'USA':'#2788ae','JPN':'#8551a6'}.get(c))
        if fit is not None:
            valid,r=fit
            coefficients=np.polyfit(valid[x],valid[y],1)
            for _,support in frame.dropna(subset=[x,y]).groupby('country'):
                fit_x=np.linspace(support[x].min(),support[x].max(),100)
                ax.plot(fit_x,np.polyval(coefficients,fit_x),linewidth=1.6,linestyle='--',color='#455565')
            ax.set_title(f'{title} | n={len(valid)}, r={r:.2f}')
        else:
            ax.set_title(title+' | insufficient data')
        ax.set_xlabel('Population aged 65+ (%)')
        ax.grid(alpha=.16)
    axes[0].set_ylabel('Manufacturing GDP share (%)' if y=='manufacturing_share_pct' else 'Service GDP share (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    if handles:
        axes[0].legend(handles,labels,loc='upper left')
    fig.suptitle(f'Regional aging and industrial composition, {year}\nUnweighted regional associations',fontsize=13)
    fig.supxlabel(f'Sources: Census July {year}; Japan October {year}; BEA CY{year}; Cabinet Office FY{year}.\nNominal value added/GDP, not employment share. Services are country-specific.', fontsize=8)
    filename=f'correlation_{y}_{year}'+(f'_{country}' if country else '')
    fig.savefig(OUT/f'{filename}.svg',bbox_inches='tight',metadata={'Date':None})
    fig.savefig(OUT/f'{filename}.png',dpi=300,bbox_inches='tight')
    print('Charts saved:',OUT / f'{filename}.svg')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--year',type=int,default=2022)
    parser.add_argument('--metric',choices=['manufacturing_share_pct','services_share_pct'],default='manufacturing_share_pct')
    parser.add_argument('--country',choices=['USA','JPN'],help='Required for non-comparable service shares')
    args=parser.parse_args()
    main(args.year,args.metric,args.country)
