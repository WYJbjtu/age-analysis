"""Publication figures for Member1, sourced only from reviewed population CSVs."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;OUT=R/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
COLORS={'USA':'#2788ae','JPN':'#8551a6'};LABELS={'USA':'United States','JPN':'Japan'}
def save(fig,name):
 for ext in ['png','svg','pdf']:fig.savefig(OUT/f'{name}.{ext}',bbox_inches='tight',dpi=200,facecolor='white')
 plt.close(fig)
t=pd.read_csv(R/'national_trends_wpp2024_2000_2022.csv')
fig,ax=plt.subplots(figsize=(10,5.7));fig.subplots_adjust(left=.10,right=.83,bottom=.20,top=.85)
for country,g in t.groupby('country'):
 g=g.sort_values('year');ax.plot(g.year,g.age65_share_pct,color=COLORS[country],linewidth=2.5)
 for i in [0,-1]:
  row=g.iloc[i];ax.scatter(row.year,row.age65_share_pct,color=COLORS[country],s=30,zorder=4)
  if i==0:ax.annotate(f'{row.age65_share_pct:.1f}%',(row.year,row.age65_share_pct),xytext=(0,9),textcoords='offset points',fontsize=10)
 last=g.iloc[-1];ax.annotate(f'{LABELS[country]}\n{last.age65_share_pct:.1f}%',(last.year,last.age65_share_pct),xytext=(10,0),textcoords='offset points',va='center',color=COLORS[country],fontsize=11)
ax.set(xlim=(1999.5,2022.5),ylim=(0,35),ylabel='Population aged 65+ (%)',xlabel='Year');ax.set_xticks([2000,2005,2010,2015,2020,2022]);ax.grid(axis='y',alpha=.18)
fig.suptitle('National population aging, 2000–2022',fontsize=17,x=.10,ha='left')
fig.text(.10,.035,'Source: United Nations, World Population Prospects 2024, Estimates; both sexes, July 1.\nNational series use a common source/version. They are separate from regional Census / Statistics Bureau estimates.',fontsize=9,color='#555555')
save(fig,'01_national_aging_trends_2000_2022')
p=pd.read_csv(R/'population_2022.csv')
fig,axes=plt.subplots(1,2,figsize=(15,13));fig.subplots_adjust(left=.11,right=.96,bottom=.145,top=.90,wspace=.50)
for ax,country in zip(axes,['USA','JPN']):
 g=p[p.country==country].sort_values('age65_share_pct');y=np.arange(len(g));median=g.age65_share_pct.median()
 ax.scatter(g.age65_share_pct,y,color=COLORS[country],s=22,zorder=3);ax.set_yticks(y,g.region_name,fontsize=8.4);ax.set_xlim(0,45);ax.set_ylim(-1,len(g));ax.grid(axis='x',alpha=.15);ax.set_xlabel('Population aged 65+ (%)');ax.axvline(median,color=COLORS[country],linestyle='--',alpha=.65)
 ax.set_title(f'{LABELS[country]} | n={len(g)}\nRegional median: {median:.1f}%',fontsize=13)
 for row,yy in zip(g.itertuples(),y):ax.annotate(f'{row.age65_share_pct:.1f}',(row.age65_share_pct,yy),xytext=(4,0),textcoords='offset points',fontsize=8,va='center')
fig.suptitle('Regional differences in population aging, 2022',fontsize=19)
fig.text(.11,.04,'Sources: U.S. Census Bureau Vintage 2022 (July 1); Statistics Bureau of Japan / e-Stat (October 1).\nSame percentage scale; one equally weighted observation per state/DC or prefecture. Medians are not national rates.\nJapan rates are officially published to one decimal; U.S. values calculated from resident population counts.',fontsize=10,color='#555555')
save(fig,'02_regional_aging_comparison_2022')
panel=pd.read_csv(R/'population_detail_2011_2022.csv');a=panel[panel.year==2011];b=panel[panel.year==2022];change=a.merge(b,on=['country','region_id'],suffixes=('_2011','_2022'),validate='one_to_one');change['age65_change_pp']=change.age65_share_pct_2022-change.age65_share_pct_2011
change[['country','region_id','region_name_2022','age65_share_pct_2011','age65_share_pct_2022','age65_change_pp']].to_csv(R/'population_change_2011_2022.csv',index=False,float_format='%.8f')
fig,axes=plt.subplots(1,2,figsize=(10,5.5),sharex=True,sharey=True);fig.subplots_adjust(bottom=.25,top=.80)
for ax,country in zip(axes,['USA','JPN']):
 g=change[change.country==country];ax.scatter(g.age65_share_pct_2011,g.age65_share_pct_2022,s=24,color=COLORS[country],alpha=.8);ax.plot([0,45],[0,45],color='#777777',linestyle='--',linewidth=1);ax.set(xlim=(0,45),ylim=(0,45),xlabel='2011 aged 65+ (%)',title=f'{LABELS[country]} | n={len(g)}');ax.grid(alpha=.15)
axes[0].set_ylabel('2022 aged 65+ (%)');fig.suptitle('Regional aging increased between 2011 and 2022',fontsize=16)
fig.text(.10,.035,'Above the diagonal: a higher aged-65+ share in 2022. Descriptive endpoint comparison.\nSources: Census Vintage 2020 evaluation (2011) and Vintage 2022 (2022); Japan official long-term and 2022 tables.\nCensus bases and revisions differ across periods; changes include benchmark effects and are not causal estimates.',fontsize=9,color='#555555')
save(fig,'03_regional_aging_change_2011_2022')
print('Three figure groups exported as PNG/SVG/PDF.')
