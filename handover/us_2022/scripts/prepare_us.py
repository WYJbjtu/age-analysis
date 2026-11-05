from pathlib import Path
import pandas as pd, numpy as np, json, zipfile, io, hashlib, datetime, shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
import shapefile
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'deliverables'; FIG=OUT/'figures'
for p in [ROOT/'processed',ROOT/'qa',FIG]:p.mkdir(parents=True,exist_ok=True)
def savecsv(df,path):df.to_csv(path,index=False,encoding='utf-8-sig',float_format='%.8f')
pop=pd.read_csv(ROOT/'raw/census_sc_est2022_alldata6.csv')
base=pop.query('SUMLEV == 40 and SEX == 0 and ORIGIN == 0').copy()
assert not base.duplicated(['STATE','RACE','AGE']).any()
assert base.groupby('STATE').size().eq(6*86).all()
total=base.groupby(['STATE','NAME'])['POPESTIMATE2022'].sum().rename('population_total')
old=base[base.AGE>=65].groupby(['STATE','NAME'])['POPESTIMATE2022'].sum().rename('population_65plus')
df=pd.concat([total,old],axis=1).reset_index().rename(columns={'STATE':'fips_num','NAME':'region_name'})
df['region_code']=df.fips_num.map(lambda x:f'{x:02d}')
df['country']='United States';df['year']=2022;df['population_reference_date']='2022-07-01'
df['aging_rate_pct']=100*df.population_65plus/df.population_total
tot=pd.read_csv(ROOT/'raw/census_nst_est2022_all.csv',encoding='latin1').query('SUMLEV == 40 and STATE != 72').copy()
assert len(tot)==51
check=df.merge(tot[['STATE','POPESTIMATE2022']],left_on='fips_num',right_on='STATE',validate='one_to_one')
assert (check.population_total==check.POPESTIMATE2022).all()
supp=tot[['STATE','POPESTIMATE2021','NPOPCHG_2022','NATURALCHG2022','NETMIG2022','DOMESTICMIG2022','INTERNATIONALMIG2022','RESIDUAL2022','RNETMIG2022']].rename(columns={'STATE':'fips_num','POPESTIMATE2021':'population_2021','NPOPCHG_2022':'population_change_2021_2022','NATURALCHG2022':'natural_change_2021_2022','NETMIG2022':'net_migration_2021_2022','DOMESTICMIG2022':'net_domestic_migration_2021_2022','INTERNATIONALMIG2022':'net_international_migration_2021_2022','RESIDUAL2022':'population_change_residual','RNETMIG2022':'net_migration_rate_per_1000'})
df=df.merge(supp,on='fips_num',validate='one_to_one')
assert (df.population_change_2021_2022==df.natural_change_2021_2022+df.net_migration_2021_2022+df.population_change_residual).all()
assert (df.net_migration_2021_2022==df.net_domestic_migration_2021_2022+df.net_international_migration_2021_2022).all()
df['population_change_pct']=100*df.population_change_2021_2022/df.population_2021
z=zipfile.ZipFile(ROOT/'raw/BEA_SAGDP.zip'); name=next(n for n in z.namelist() if 'SAGDP2_' in n and 'ALL_AREAS' in n)
bea=pd.read_csv(io.BytesIO(z.read(name)),dtype=str,skipinitialspace=True)
bea['GeoFIPS']=bea.GeoFIPS.str.strip().str.replace('"','',regex=False)
bea['LineCode']=pd.to_numeric(bea.LineCode,errors='coerce')
bea['Description']=bea.Description.str.strip(); bea['GeoName']=bea.GeoName.str.strip()
codes=set(df.region_code+'000'); reg=bea[bea.GeoFIPS.isin(codes)].copy()
assert not reg.duplicated(['GeoFIPS','LineCode']).any()
core=reg[reg.LineCode.isin([1,12])].copy();core['value']=pd.to_numeric(core['2022'],errors='coerce')
assert core.value.notna().all() and len(core)==102
assert set(core[core.LineCode==12].IndustryClassification.str.strip())=={'31-33'}
pivot=core.pivot(index='GeoFIPS',columns='LineCode',values='value').rename(columns={1:'gdp_nominal_usd_million',12:'manufacturing_va_nominal_usd_million'}).reset_index()
pivot['region_code']=pivot.GeoFIPS.str[:2]
df=df.merge(pivot.drop(columns='GeoFIPS'),on='region_code',validate='one_to_one')
df['manufacturing_share_pct']=100*df.manufacturing_va_nominal_usd_million/df.gdp_nominal_usd_million
df['economic_period']='CY2022';df['population_vintage']='Vintage 2022 (June 2023 age release)';df['gdp_vintage']='2026-09-30'
df['population_change_period']='2021-07-01 to 2022-07-01'
assert len(df)==51 and df.region_code.nunique()==51
assert df.aging_rate_pct.between(0,100).all() and df.manufacturing_share_pct.between(0,100).all()
assert not df.isna().any().any()
df=df.sort_values('region_code').drop(columns='fips_num')
cols=['country','region_code','region_name','year','population_reference_date','economic_period','population_total','population_65plus','aging_rate_pct','gdp_nominal_usd_million','manufacturing_va_nominal_usd_million','manufacturing_share_pct']
df=df[cols+[c for c in df if c not in cols]]
savecsv(df,ROOT/'processed/us_states_2022_core.csv');savecsv(df,OUT/'US_2022_交接数据.csv')
sector=reg[['GeoFIPS','GeoName','LineCode','IndustryClassification','Description','Unit','2022']].copy()
sector['value_2022']=pd.to_numeric(sector['2022'],errors='coerce');sector['source_value']=sector['2022'];sector=sector.drop(columns='2022')
savecsv(sector,ROOT/'processed/us_industries_2022_long.csv')
age=base.groupby(['STATE','NAME','AGE'])['POPESTIMATE2022'].sum().reset_index();savecsv(age,ROOT/'processed/us_age_distribution_2022.csv')
stats=df[['aging_rate_pct','manufacturing_share_pct']].describe(percentiles=[.25,.5,.75]).reset_index().rename(columns={'index':'statistic'})
savecsv(stats,ROOT/'processed/descriptive_statistics.csv');savecsv(stats,OUT/'描述统计.csv')
national=float(100*df.population_65plus.sum()/df.population_total.sum())
summary={'n_regions':len(df),'population_total':int(df.population_total.sum()),'population_65plus':int(df.population_65plus.sum()),'national_aging_rate_pct':national,'aging_mean_pct':float(df.aging_rate_pct.mean()),'aging_median_pct':float(df.aging_rate_pct.median()),'aging_min':df.loc[df.aging_rate_pct.idxmin(),['region_name','aging_rate_pct']].to_dict(),'aging_max':df.loc[df.aging_rate_pct.idxmax(),['region_name','aging_rate_pct']].to_dict(),'manufacturing_min':df.loc[df.manufacturing_share_pct.idxmin(),['region_name','manufacturing_share_pct']].to_dict(),'manufacturing_max':df.loc[df.manufacturing_share_pct.idxmax(),['region_name','manufacturing_share_pct']].to_dict()}
(ROOT/'processed/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
qa={'status':'PASS','checks':{'51_unique_regions':True,'age_race_cells_complete':True,'population_matches_separate_Census_state_totals_all_51':True,'population_change_identity_all_51':True,'net_migration_identity_all_51':True,'BEA_102_core_cells_numeric':True,'manufacturing_NAICS_31_33':True,'one_to_one_joins':True,'no_missing_core_or_supplementary_fields':True,'rates_in_0_100':True},'excluded_geographies':'US total, multistate aggregates and territories; DC retained','population_age_filter':'SUMLEV=040, SEX=0, ORIGIN=0, sum RACE 1..6; AGE 0..85 total, AGE 65..85 older; 85 means 85+','bea_core_lines':{'1':'All industry total','12':'Manufacturing'},'non_numeric_sector_cells':int(sector.value_2022.isna().sum()),'sector_warning':'Industry rows are hierarchical and overlapping; do not sum all rows. Non-numeric markers retained, not set to zero.'}
(ROOT/'qa/validation.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
def export(fig,stem):
 for ext in ['png','svg','pdf']:fig.savefig(FIG/f'{stem}.{ext}',dpi=220,bbox_inches='tight',facecolor='white')
 plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(13,13),sharey=True)
ranked=df.sort_values('aging_rate_pct')
y=np.arange(51)
for ax,col,color,title in zip(axes,['aging_rate_pct','manufacturing_share_pct'],['#6456a5','#218380'],['Population aged 65+ (%)','Manufacturing value added / GDP (%)']):
 ax.scatter(ranked[col],y,s=26,color=color,zorder=3);ax.set_xlabel(title);ax.set_yticks(y);ax.set_yticklabels(ranked.region_name,fontsize=9);ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
 for v,yy in zip(ranked[col],y):ax.annotate(f'{v:.1f}',(v,yy),xytext=(5,0),textcoords='offset points',va='center',fontsize=8)
 ax.set_xlim(0,float(ranked[col].max())+4)
axes[1].tick_params(labelleft=False)
fig.suptitle('U.S. regional aging and manufacturing structure in 2022',fontsize=18,y=.97)
fig.text(.125,.935,'51 regions, ordered by aging rate in both panels; each region receives equal weight.',fontsize=11,color='#555555')
fig.text(.125,.025,'Sources: Census Vintage 2022 (July 1 population); BEA SAGDP2, CY2022 (September 30, 2026 release).\nManufacturing share measures economic output, not employment. Values rounded to one decimal.',fontsize=9,color='#555555')
fig.subplots_adjust(top=.91,bottom=.075,wspace=.08);export(fig,'01_ranked_dotplots')
geo=ROOT/'raw/boundaries';geo.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT/'raw/census_states_2022.zip') as gz:gz.extractall(geo)
reader=shapefile.Reader(str(geo/'cb_2022_us_state_20m.shp'))
records=list(reader.iterShapeRecords());fields=[f[0] for f in reader.fields[1:]]
def draw_map(col,title,stem,cmap):
 fig=plt.figure(figsize=(12,7.5));main=fig.add_axes([.025,.23,.94,.65]);ak=fig.add_axes([.04,.08,.23,.25]);hi=fig.add_axes([.31,.11,.15,.15]);dc=fig.add_axes([.51,.10,.12,.17]);norm=Normalize(vmin=float(df[col].min()),vmax=float(df[col].max()))
 configs=[(main,None,'EPSG:5070'),(ak,'02','EPSG:3338'),(hi,'15','EPSG:3759'),(dc,'11','EPSG:26918')]
 for ax,code,crs in configs:
  tf=Transformer.from_crs('EPSG:4269',crs,always_xy=True);patches=[];values=[];seen=set()
  for item in records:
   rec=dict(zip(fields,item.record));fips=rec['STATEFP']
   if fips not in set(df.region_code):continue
   if (code is None and fips in ['02','15','11']) or (code is not None and fips!=code):continue
   shape=item.shape;parts=list(shape.parts)+[len(shape.points)]
   for st,en in zip(parts[:-1],parts[1:]):
    pts=np.array(shape.points[st:en]);xs,ys=tf.transform(pts[:,0],pts[:,1]);patches.append(Polygon(np.column_stack([xs,ys]),closed=True));values.append(float(df.loc[df.region_code==fips,col].iloc[0]))
   seen.add(fips)
  collection=PatchCollection(patches,cmap=cmap,norm=norm,edgecolor='white',linewidth=.45);collection.set_array(np.array(values));ax.add_collection(collection);ax.autoscale_view();ax.set_aspect('equal');ax.set_axis_off()
  if code:ax.set_title({'02':'Alaska','15':'Hawaii','11':'Washington, D.C.'}[code],fontsize=10,pad=1)
  if code is None:assert len(seen)==48
  else:assert seen=={code}
 cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.73,.14,.23,.025]),orientation='horizontal');cb.set_label('Percent (%)',fontsize=10)
 fig.text(.04,.94,title,fontsize=19,weight='bold');fig.text(.04,.895,'50 states and Washington, D.C. | Actual geographic boundaries; inset scales differ.',fontsize=10,color='#555555')
 fig.text(.04,.025,'Sources: Census Vintage 2022 and 2022 cartographic boundaries; BEA SAGDP2 (2026-09-30).\nPopulation reference: July 1, 2022. Economic period: CY2022. D.C. shown separately for visibility.',fontsize=9,color='#555555')
 export(fig,stem)
draw_map('aging_rate_pct','Share of residents aged 65 and over in 2022','02_aging_map','Purples')
draw_map('manufacturing_share_pct','Manufacturing share of regional GDP in 2022','03_manufacturing_map','YlGnBu')
print(json.dumps(summary,indent=2));print(stats.to_string(index=False));print('VALIDATION PASS')
