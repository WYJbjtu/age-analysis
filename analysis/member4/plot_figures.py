"""Poster-ready static research figures, with deterministic SVG and PNG export."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
COLORS={'USA':'#2788ae','JPN':'#8551a6','Pooled':'#344455'}
LABELS={'USA':'United States','JPN':'Japan','Pooled':'Pooled'}
X='age65_share_pct';Y='manufacturing_share_pct'

def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.labelcolor':'#273747','text.color':'#273747','axes.titleweight':'bold',
                         'svg.fonttype':'none','svg.hashsalt':'member4-2026-11-09','savefig.facecolor':'white'})

def save(fig,out,name):
    out.mkdir(parents=True,exist_ok=True)
    fig.savefig(out/f'{name}.png',dpi=300)
    fig.savefig(out/f'{name}.svg',metadata={'Date':None})
    plt.close(fig)

def make_figures(base):
    style();out=base/'figures'
    d=pd.read_csv(base/'data/core_2022.csv');res=pd.read_csv(base/'results/associations.csv')
    fig,axes=plt.subplots(1,3,figsize=(14.4,6.1),sharex=True,sharey=True)
    fig.subplots_adjust(left=.065,right=.98,bottom=.24,top=.72,wspace=.13)
    for ax,group in zip(axes,['Pooled','USA','JPN']):
        sub=d if group=='Pooled' else d[d.country==group]
        s=res[(res.year==2022)&(res.group==group)&(res.variant=='available')&(res.y==Y)].iloc[0]
        for country,g in sub.groupby('country'):
            ax.scatter(g[X],g[Y],s=34,alpha=.83,color=COLORS[country],edgecolor='white',linewidth=.4)
            # Fit evaluated only on the observed support. No line across the country gap.
            xx=np.array([g[X].min(),g[X].max()])
            ax.plot(xx,s.intercept+s.slope*xx,color=COLORS[group],lw=2)
        ax.set(xlim=(10,40),ylim=(0,45),xlabel='Population aged 65+ (%)',xticks=[10,20,30,40])
        ax.set_title(f'{LABELS[group]}  |  n = {int(s.n)}',fontsize=13,pad=42)
        ax.text(.5,1.06,f'Pearson r = {s.pearson:.3f}\nSpearman ρ = {s.spearman:.3f}',transform=ax.transAxes,ha='center',fontsize=11)
        ax.grid(alpha=.16);ax.set_axisbelow(True)
    axes[0].set_ylabel('Manufacturing share of nominal GDP (%)')
    fig.suptitle('A pooled association nearly disappears within countries',x=.065,ha='left',y=.97,fontsize=20,weight='bold')
    fig.text(.065,.897,'2022 regional cross-section',fontsize=13)
    fig.legend(handles=[Line2D([],[],marker='o',linestyle='',color=COLORS[c],label=LABELS[c]) for c in ['USA','JPN']],loc='upper right',bbox_to_anchor=(.98,.922),ncol=2,frameon=False)
    fig.text(.065,.11,'Each region has equal weight. Lines summarize observed ranges; no robust direction-reversal headline is supported.',fontsize=10.5)
    fig.text(.065,.045,'Sources: Census Vintage 2022; Japan Population Estimates 2022; BEA SAGDP2 (September 2026); Cabinet Office FY2022.\nUS: July population / calendar-year GDP. Japan: October population / April 2022–March 2023 GDP. Association is descriptive.',fontsize=9,color='#56636e')
    save(fig,out,'01_pooled_within_2022')

    fig,(ax,bx)=plt.subplots(1,2,figsize=(13.2,6.4),gridspec_kw={'width_ratios':[1.25,1]})
    fig.subplots_adjust(left=.11,right=.97,bottom=.32,top=.75,wspace=.38)
    offsets={(2019,'pearson'):-.21,(2019,'spearman'):-.07,(2022,'pearson'):.07,(2022,'spearman'):.21}
    for i,group in enumerate(['Pooled','USA','JPN']):
        for (year,method),offset in offsets.items():
            s=res[(res.year==year)&(res.group==group)&(res.variant=='available')&(res.y==Y)].iloc[0]
            ax.scatter(s[method],i+offset,color=COLORS[group],marker='o' if method=='pearson' else 's',s=58,
                       facecolors='none' if year==2019 else COLORS[group],linewidths=1.5)
    ax.axvline(0,color='#87929b',lw=1);ax.set(xlim=(-.25,.8),ylim=(2.6,-.6),yticks=[0,1,2],yticklabels=['Pooled (n=98)','USA (n=51)','Japan (n=47)'],xlabel='Correlation coefficient')
    ax.grid(axis='x',alpha=.15);ax.set_title('Same conclusion in 2019 and 2022',fontsize=12,pad=12)
    handles=[Line2D([],[],color='#556575',marker=m,linestyle='',markerfacecolor='none' if y==2019 else '#556575',label=f'{y} {method}') for y,method,m in [(2019,'Pearson','o'),(2019,'Spearman','s'),(2022,'Pearson','o'),(2022,'Spearman','s')]]
    ax.legend(handles=handles,loc='upper left',bbox_to_anchor=(-.03,-.25),ncol=2,frameon=False,fontsize=9)
    s=pd.read_csv(base/'results/covariance_summary.csv').query('year==2022').iloc[0]
    vals=[s.within_covariance,s.between_covariance,s.pooled_covariance]
    bx.barh([2,1,0],vals,color=['#9cabb4','#b99acd','#344455'],height=.5)
    bx.set(yticks=[2,1,0],yticklabels=['Within countries','Between countries','Pooled total'],xlim=(0,55),xlabel='Covariance (percentage points²)')
    for yy,v in zip([2,1,0],vals): bx.text(v+.7,yy,f'{v:.3f}',va='center',fontsize=11)
    bx.set_title('99.1% of pooled covariance\nis between countries in 2022',fontsize=12,pad=12)
    bx.grid(axis='x',alpha=.15);bx.set_axisbelow(True)
    fig.suptitle('The pooled pattern reflects differences between country means',x=.055,ha='left',y=.96,fontsize=18,weight='bold')
    fig.text(.055,.86,'Equal region weights. Identical 98-region samples in both years.',fontsize=12)
    fig.text(.055,.035,'Covariance uses denominator N throughout, with country contributions weighted by their 51/98 and 47/98 shares.\nBetween-country share is an accounting decomposition, not a causal attribution or explained-variance statistic.',fontsize=9,color='#56636e')
    save(fig,out,'02_robustness_and_covariance')

    cases=pd.read_csv(base/'results/selected_cases.csv')
    fig,axes=plt.subplots(2,2,figsize=(12.8,7.7),sharex=True)
    fig.subplots_adjust(left=.08,right=.96,bottom=.23,top=.78,wspace=.30,hspace=.65)
    for col,country in enumerate(['USA','JPN']):
        g=cases[cases.country==country]
        for row,selection in enumerate(['largest industry gap','smallest industry gap']):
            ax=axes[row,col];y=.5
            p=g[g.selection==selection].sort_values(Y)
            ax.plot(p[Y],[y,y],color=COLORS[country],lw=3,alpha=.6)
            ax.scatter(p[Y],[y,y],s=62,color=COLORS[country],zorder=3)
            for j,r in enumerate(p.itertuples()):
                ax.annotate(f'{r.region_name}: {getattr(r,Y):.2f}% manufacturing\n{getattr(r,X):.2f}% aged 65+',
                            (getattr(r,Y),y),xytext=(0,16 if j==0 else -36),textcoords='offset points',ha='center',fontsize=10)
            ax.set(xlim=(-1,45),ylim=(-.35,1.35),yticks=[])
            ax.set_title(f'{LABELS[country]} — {selection}',fontsize=12,pad=9);ax.grid(axis='x',alpha=.15)
            if row==1: ax.set_xlabel('Manufacturing share of nominal GDP (%)')
    fig.suptitle('Similar aging can accompany contrasting industry shares',x=.06,ha='left',y=.96,fontsize=19,weight='bold')
    fig.text(.06,.86,'2022 within-country pairs: largest gap (top) and smallest gap (bottom)',fontsize=12)
    fig.text(.06,.11,'Selection: enumerate all pairs within 0.5 percentage points in aging, then choose the largest and smallest industry gaps.',fontsize=10)
    fig.text(.06,.045,'All eligible pairs are retained in the results table. These examples illustrate heterogeneity; they do not isolate a causal effect.\nPopulation and industry sources and US calendar-year / Japan fiscal-year definitions are the same as Figure 1.',fontsize=9,color='#56636e')
    save(fig,out,'03_within_country_cases')
