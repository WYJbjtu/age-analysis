"""Populate repository-owned USA 2022 rows from reviewed handover inputs; preserve other rows."""
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
H=ROOT/'handover/us_2022'
def main():
 d=pd.read_csv(H/'processed/us_2022_contract_mapping.csv')
 ages=pd.read_csv(H/'processed/us_age_distribution_2022.csv')
 working=ages.query('15 <= AGE <= 64').groupby('NAME').POPESTIMATE2022.sum()
 ind=pd.read_csv(H/'processed/us_industries_2022_long.csv')
 services=ind[ind.LineCode==92].set_index('GeoName').value_2022
 goods=ind[ind.LineCode==91].set_index('GeoName').value_2022
 private=ind[ind.LineCode==2].set_index('GeoName').value_2022
 assert len(services)==51 and services.notna().all()
 assert np.allclose(services+goods,private,atol=.21)
 key=d[['country','region_id','year']].copy()
 dem=key.assign(age65_share_pct=d.age65_share_pct,total_population=d.population_total,working_age_share_pct=d.region_name.map(working)/d.population_total*100,old_age_dependency_ratio=d.population_65plus/d.region_name.map(working)*100)
 industry=key.assign(manufacturing_share_pct=d.manufacturing_share_pct,services_share_pct=d.region_name.map(services)/d.gdp_nominal_usd_million*100,nominal_gdp_local=d.gdp_nominal_usd_million,manufacturing_va_local=d.manufacturing_va_nominal_usd_million,services_va_local=d.region_name.map(services),gdp_reference_period='CY2022')
 labor=key.assign(employment=np.nan,unemployment_rate_pct=np.nan,net_migration=d.net_migration_2021_2022)
 for name,frame in [('demographics',dem),('industry',industry),('labor_migration',labor)]:
  path=ROOT/'data/processed'/f'{name}.csv'
  existing=pd.read_csv(path)
  keep=existing[~((existing.country=='USA')&(existing.year==2022))]
  out=pd.concat([keep,frame],ignore_index=True).sort_values(['country','region_id','year'])
  assert not out.duplicated(['country','region_id','year']).any()
  out.to_csv(path,index=False,float_format='%.8f')
  print(name,len(frame),'USA 2022 rows')
if __name__=='__main__':main()
