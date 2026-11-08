"""Build Member1's 2011–2022 panel and UN WPP2024 national background.

Raw input directory is explicit so no machine-specific path is required.
Counts/rates are not harmonized by interpolation across census vintages.
"""
from pathlib import Path
import argparse,json,hashlib,zipfile,xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1];MODULE=ROOT/'member1_demographics'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
URLS={
 'us_2010_2020.csv':'https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/state/asrh/SC-EST2020-ALLDATA6.csv',
 'us_2020_2022.csv':'https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/asrh/sc-est2022-alldata6.csv',
 'jp_long.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000013168610&fileKind=4',
 'jp2021_table11.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032191052&fileKind=0',
 'jp2021_table12.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032191053&fileKind=0',
 'jp2021_table13.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032191054&fileKind=0',
 'jp2022_table11.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040045497&fileKind=0',
 'jp2022_table12.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040045498&fileKind=0',
 'jp2022_table13.xlsx':'https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040045499&fileKind=0',
 'wpp_ages.xlsx':'https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/EXCEL_FILES/2_Population/WPP2024_POP_F06_1_POPULATION_PERCENTAGE_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx'}
def wpp_extract(path):
 # UN worksheet has a stale A1:L18 dimension; read actual XML instead of trusting it.
 z=zipfile.ZipFile(path);strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
 book=ET.fromstring(z.read('xl/workbook.xml'));s=next(x for x in book.find('s:sheets',NS) if x.attrib['name']=='Estimates')
 rid=s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
 rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));target=next(x.attrib['Target'] for x in rel if x.attrib['Id']==rid)
 rows=ET.fromstring(z.read('xl/'+target)).findall('.//s:row',NS)
 def cells(row):
  d={}
  for c in row:
   v=c.find('s:v',NS)
   if v is not None:d[''.join(t for t in c.attrib['r'] if t.isalpha())]=strings[int(v.text)] if c.attrib.get('t')=='s' else v.text
  return d
 header=cells(next(row for row in rows if row.attrib['r']=='17'))
 agecols={value:col for col,value in header.items()}
 result=[]
 for row in rows:
  c=cells(row)
  if c.get('F') not in ['USA','JPN']:continue
  if not c.get('K','').isdigit():continue
  year=int(c['K'])
  if 2000<=year<=2022:
   result.append({'country':c['F'],'year':year,'age65_share_pct':float(c[agecols['65+']]),'working_age_share_pct':float(c[agecols['15-64']]),'age0_14_share_pct':float(c[agecols['0-14']]),'source_version':'UN WPP2024','population_reference_date':f'{year}-07-01','variant':'Estimates'})
 return pd.DataFrame(result)
def main(raw):
 lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv');usnames=lookup.query("country=='USA'").set_index('region_name').region_id
 records=[]
 previous=json.loads((MODULE/'population_source_manifest.json').read_text(encoding='utf-8')) if (MODULE/'population_source_manifest.json').exists() else []
 manifests={x['file']:x for x in previous}
 for name,url in URLS.items():
  p=raw/name
  if p.exists():
   digest=hashlib.sha256(p.read_bytes()).hexdigest()
   if name in manifests:assert digest==manifests[name]['sha256'],f'Pinned source differs: {name}; do not silently change vintages.'
   manifests[name]={'file':name,'url':url,'bytes':p.stat().st_size,'sha256':digest,'retrieved_on':'2026-10-30' if name=='us_2020_2022.csv' else '2026-11-06','note':'Source release versions are documented in README; no silent revision mixing.'}
 manifest=list(manifests.values())
 for name,years,vintage in [('us_2010_2020.csv',range(2011,2020),'Census Vintage2020 evaluation estimates; 2010 census base'),('us_2020_2022.csv',range(2020,2023),'Census Vintage2022; blended2020 base')]:
  f=pd.read_csv(raw/name);f=f.query('SUMLEV==40 and SEX==0 and ORIGIN==0')
  assert not f.duplicated(['STATE','RACE','AGE']).any()
  assert f.groupby('STATE').size().eq(6*86).all()
  for year in years:
   col=f'POPESTIMATE{year}';total=f.groupby('NAME')[col].sum();young=f.query('AGE<15').groupby('NAME')[col].sum();working=f.query('15<=AGE<=64').groupby('NAME')[col].sum();older=f.query('AGE>=65').groupby('NAME')[col].sum()
   for name in total.index:
    records.append({'country':'USA','region_id':usnames[name],'region_name':name,'year':year,'population_total':int(total[name]),'population_0_14':int(young[name]),'population_15_64':int(working[name]),'population_65plus':int(older[name]),'age65_share_pct':100*older[name]/total[name],'working_age_share_pct':100*working[name]/total[name],'old_age_dependency_ratio':100*older[name]/working[name],'population_reference_date':f'{year}-07-01','source_version':vintage,'count_precision_persons':1,'rate_method':'calculated from resident counts'})
 for sheet,years,step,base in [(0,range(2011,2015),4,2000),(3,range(2015,2021),6,2015)]:
  f=pd.read_excel(raw/'jp_long.xlsx',sheet_name=sheet,header=None);codes=pd.to_numeric(f[1],errors='coerce');regions=f.loc[codes.between(1,47)].copy();assert len(regions)==47
  assert pd.to_numeric(regions[1]).astype(int).tolist()==list(range(1,48))
  for year in years:
   col=4+(year-base)*step
   for _,r in regions.iterrows():
    code=f"JP-{int(r[1]):02d}";name=lookup.set_index('region_id').loc[code,'region_name'];t,y,w,o=[int(r[col+i])*1000 for i in range(4)]
    records.append({'country':'JPN','region_id':code,'region_name':name,'year':year,'population_total':t,'population_0_14':y,'population_15_64':w,'population_65plus':o,'age65_share_pct':100*o/t,'working_age_share_pct':100*w/t,'old_age_dependency_ratio':100*o/w,'population_reference_date':f'{year}-10-01','source_version':'Japan long-term table10 released2022-07-20; census/intercensal series','count_precision_persons':1000,'rate_method':'calculated from published thousand-person counts'})
 for year in [2021,2022]:
  tables={n:pd.read_excel(raw/f'jp{year}_table{n}.xlsx',header=None).iloc[8:56].reset_index(drop=True) for n in [11,12,13]}
  for n,f in tables.items():assert f[10].astype(str).str.strip().tolist()==[f'{i:02d}000' for i in range(48)] and f[9].eq('総人口').all()
  for i in range(1,48):
   code=f'JP-{i:02d}';c=tables[11].iloc[i];s=tables[12].iloc[i];ind=tables[13].iloc[i]
   records.append({'country':'JPN','region_id':code,'region_name':lookup.set_index('region_id').loc[code,'region_name'],'year':year,'population_total':int(c[14])*1000,'population_0_14':int(c[15])*1000,'population_15_64':int(c[16])*1000,'population_65plus':int(c[17])*1000,'age65_share_pct':float(s[17]),'working_age_share_pct':float(s[16]),'old_age_dependency_ratio':float(ind[14]),'population_reference_date':f'{year}-10-01','source_version':f'Japan annual population estimates {year}; released{year+1}-04','count_precision_persons':1000,'rate_method':'official published one-decimal share and dependency index'})
 panel=pd.DataFrame(records).sort_values(['country','region_id','year'])
 assert len(panel)==1176 and not panel.duplicated(['country','region_id','year']).any()
 assert not panel.isna().any().any()
 residual=panel.population_0_14+panel.population_15_64+panel.population_65plus-panel.population_total
 assert (abs(residual)<=panel.count_precision_persons*2).all()
 gap=abs(panel.population_65plus/panel.population_total*100-panel.age65_share_pct)
 assert gap.max()<.2
 canonical=pd.read_csv(ROOT/'data/processed/demographics.csv');old=canonical.query('year==2022');new=panel.query('year==2022').merge(old,on=['country','region_id','year'],suffixes=('_new','_old'),validate='one_to_one')
 assert len(new)==98 and np.allclose(new.age65_share_pct_new,new.age65_share_pct_old,atol=1e-7,rtol=0)
 assert (new.population_total==new.total_population).all()
 panel.to_csv(MODULE/'population_detail_2011_2022.csv',index=False,float_format='%.8f')
 core=panel[['country','region_id','year','age65_share_pct','population_total','working_age_share_pct','old_age_dependency_ratio']].rename(columns={'population_total':'total_population'})
 pd.concat([canonical.loc[~canonical.year.between(2011,2022)],core],ignore_index=True).sort_values(['country','region_id','year']).to_csv(ROOT/'data/processed/demographics.csv',index=False,float_format='%.8f')
 panel.query('year==2019').to_csv(MODULE/'population_2019.csv',index=False,float_format='%.8f')
 panel.query('year==2022').to_csv(MODULE/'population_2022.csv',index=False,float_format='%.8f')
 if (raw/'wpp_ages.xlsx').exists():
  trends=wpp_extract(raw/'wpp_ages.xlsx')
 else:
  snapshot=MODULE/'source_snapshots/wpp2024_selected_estimates.csv'
  approved=json.loads((MODULE/'snapshot_manifest.json').read_text(encoding='utf-8'))
  assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==approved['sha256']
  trends=pd.read_csv(snapshot)
 assert len(trends)==46 and not trends.duplicated(['country','year']).any()
 assert np.allclose(trends.age65_share_pct+trends.working_age_share_pct+trends.age0_14_share_pct,100,atol=1e-5)
 trends.sort_values(['country','year']).to_csv(MODULE/'national_trends_wpp2024_2000_2022.csv',index=False,float_format='%.8f')
 (MODULE/'population_source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 (MODULE/'population_validation.json').write_text(json.dumps({'panel_rows':len(panel),'countries':{'USA':612,'JPN':564},'regions_per_year':98,'years':list(range(2011,2023)),'national_trend_rows':46,'missing_cells':0,'duplicate_keys':0,'2022_existing_rates_unchanged':True,'max_age_sum_residual_persons':int(abs(residual).max()),'max_rounded_rate_gap_pp':float(gap.max()),'national_rows_excluded_from_regional_panel':True,'source_vintage_break_USA':2020,'rates_calculated_JPN_history_but_published_JPN_2021_2022':True},indent=2),encoding='utf-8')
 print('Population panel1176 and WPP national46 rows complete; original2022 rates unchanged.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);main(p.parse_args().raw_dir)
