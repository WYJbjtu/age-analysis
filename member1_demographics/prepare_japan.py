"""Integrate official October 1, 2022 Japanese prefectural population estimates."""
from pathlib import Path
import hashlib,json,csv,argparse
import requests
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/member1_jpn'
TABLES={11:'000040045497',12:'000040045498',13:'000040045499'}
def main(download=False):
 RAW.mkdir(parents=True,exist_ok=True)
 manifest=[];frames={}
 for n,ident in TABLES.items():
  path=RAW/f'population_table{n}.xlsx'
  url=f'https://www.e-stat.go.jp/stat-search/file-download?statInfId={ident}&fileKind=0'
  if not path.exists():
   if not download:raise FileNotFoundError(f'{path}; run --download')
   response=requests.get(url,timeout=90);response.raise_for_status();path.write_bytes(response.content)
  manifest.append({'file':path.name,'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'retrieved_date':'2026-11-06','reference_date':'2022-10-01','release_date':'2023-04-12'})
  sheet=pd.read_excel(path,header=None)
  # First block is total residents of both nationalities, both sexes; second is Japanese nationals only.
  block=sheet.iloc[8:56].copy()
  assert block[10].astype(str).str.strip().tolist()==[f'{i:02d}000' for i in range(48)]
  assert block[9].eq('総人口').all()
  frames[n]=block.reset_index(drop=True)
 counts,shares,indices=(frames[n] for n in [11,12,13])
 old=pd.to_numeric(counts[17]);working=pd.to_numeric(counts[16]);total=pd.to_numeric(counts[14]);young=pd.to_numeric(counts[15])
 official_old=pd.to_numeric(shares[17]);official_work=pd.to_numeric(shares[16]);dependency=pd.to_numeric(indices[14])
 # Published counts are rounded to thousands; official percentages/indices retain their published one decimal.
 assert np.max(np.abs(old/total*100-official_old))<.2
 assert np.max(np.abs(working/total*100-official_work))<.2
 assert np.max(np.abs(old/working*100-dependency))<.3
 assert np.max(np.abs(young+working+old-total))<=1
 national={'total_population':int(total.iloc[0]*1000),'population_65plus':int(old.iloc[0]*1000),'age65_share_pct':float(official_old.iloc[0])}
 assert national=={'total_population':124947000,'population_65plus':36236000,'age65_share_pct':29.0}
 ids=[f'JP-{i:02d}' for i in range(1,48)]
 jp=pd.DataFrame({'country':'JPN','region_id':ids,'year':2022,'age65_share_pct':official_old.iloc[1:].values,'total_population':(total.iloc[1:]*1000).astype(int).values,'working_age_share_pct':official_work.iloc[1:].values,'old_age_dependency_ratio':dependency.iloc[1:].values})
 path=ROOT/'data/processed/demographics.csv';existing=pd.read_csv(path)
 retained=existing[~((existing.country=='JPN')&(existing.year==2022))]
 pd.concat([retained,jp],ignore_index=True).sort_values(['country','region_id','year']).to_csv(path,index=False,float_format='%.8f')
 detail=jp.copy();detail['population_65plus']=(old.iloc[1:]*1000).astype(int).values;detail['population_15_64']=(working.iloc[1:]*1000).astype(int).values;detail['population_reference_date']='2022-10-01';detail['count_precision']='rounded to nearest 1000 persons'
 detail.to_csv(ROOT/'member1_demographics/jpn_population_detail_2022.csv',index=False)
 module=ROOT/'member1_demographics'
 (module/'jpn_source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 (module/'jpn_validation.json').write_text(json.dumps({'regions':47,'national_crosscheck':national,'unique_keys':not jp.duplicated(['country','region_id','year']).any(),'missing_required':int(jp.isna().sum().sum()),'published_rates_verified_against_rounded_counts':True,'usa_rows_preserved':len(retained),'migration_not_supplied':True},indent=2),encoding='utf-8')
 print('JPN: 47 prefectures integrated; national values and rounded-count consistency verified.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--download',action='store_true');main(parser.parse_args().download)
