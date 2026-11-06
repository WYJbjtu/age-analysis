from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
d=pd.read_csv(R/'data/processed/demographics.csv');d=d[d.country=='JPN'].merge(pd.read_csv(R/'data/reference/region_lookup.csv')[['region_id','region_name']],on='region_id').sort_values('age65_share_pct')
fig,ax=plt.subplots(figsize=(9,12));ax.scatter(d.age65_share_pct,d.region_name,color='#7052a3',s=25);ax.set_xlabel('Population aged 65+ (%)');ax.grid(axis='x',alpha=.2);ax.set_title('Japan: prefectural population aging in 2022');fig.subplots_adjust(left=.22,bottom=.09,top=.93);fig.text(.22,.025,'Source: Statistics Bureau / e-Stat, table 12; October 1, 2022.\n47 prefectures; official percentages published to one decimal.',fontsize=9)
for ext in ['png','svg']:fig.savefig(R/'member1_demographics/figures'/f'jpn_aging_ranked_2022.{ext}',dpi=180)
plt.close(fig)
