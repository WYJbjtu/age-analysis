"""M4: Plot pooled and country-specific region-level correlations for one selected year.

Do not interpret ecological correlations causally. Each region is one unweighted observation.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/merged_analysis.csv'
OUT = ROOT / 'analysis/figures'
LABELS = {'USA':'United States', 'JPN':'Japan'}


def correlation_summary(frame, x, y, label):
    valid = frame[[x,y]].dropna().copy()
    n = len(valid)
    if n < 3 or valid[x].nunique() < 2 or valid[y].nunique() < 2:
        return f'{label}: insufficient nonconstant observations (n={n})', None
    r = valid[x].corr(valid[y], method='pearson')
    rho = valid[x].corr(valid[y], method='spearman')
    return f'{label}: n={n}; Pearson r={r:.3f}; Spearman rho={rho:.3f}', (valid, r)


def main(year, response):
    if not DATA.exists():
        raise SystemExit('Run `python scripts/merge_core.py` after Members 1 and 2 submit data.')
    df = pd.read_csv(DATA)
    x='age65_share_pct'; y=response
    if any(col not in df.columns for col in [x,y,'population_industry_match']):
        raise SystemExit('Required columns missing from merged table.')
    df = df.loc[(df['year']==year)&(df['population_industry_match']=='both')].copy()
    if df.empty:
        raise SystemExit(f'No matched rows for {year}.')
    countries = [('Combined',df),('United States',df.loc[df.country=='USA']),('Japan',df.loc[df.country=='JPN'])]
    OUT.mkdir(parents=True,exist_ok=True)
    fig, axes=plt.subplots(1,3,figsize=(13,4.3),sharex=True,sharey=True,layout='constrained')
    for ax,(title,frame) in zip(axes,countries):
        text,fit = correlation_summary(frame,x,y,title)
        print(text)
        for c,sub in frame.groupby('country'):
            ax.scatter(sub[x],sub[y],alpha=.75,label=LABELS.get(c,c),s=30)
        if fit is not None:
            valid,r=fit
            fit_x=np.linspace(valid[x].min(),valid[x].max(),100)
            fit_y=np.polyval(np.polyfit(valid[x],valid[y],1),fit_x)
            ax.plot(fit_x,fit_y,linewidth=1.6,linestyle='--')
            ax.set_title(f'{title} | n={len(valid)}, r={r:.2f}')
        else:
            ax.set_title(title+' | insufficient data')
        ax.set_xlabel('Population aged 65+ (%)')
        ax.grid(alpha=.16)
    axes[0].set_ylabel('Manufacturing GDP share (%)' if y=='manufacturing_share_pct' else 'Service GDP share (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles,labels,loc='outside upper center',ncol=2)
    fig.suptitle(f'Regional aging and industrial composition, {year}\nUnweighted regional associations; synthetic data prohibited',y=1.10)
    filename=f'correlation_{y}_{year}'
    fig.savefig(OUT/f'{filename}.svg',bbox_inches='tight')
    fig.savefig(OUT/f'{filename}.png',dpi=200,bbox_inches='tight')
    print('Charts saved:',OUT / f'{filename}.svg')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--year',type=int,default=2022)
    parser.add_argument('--metric',choices=['manufacturing_share_pct','services_share_pct'],default='manufacturing_share_pct')
    args=parser.parse_args()
    main(args.year,args.metric)
