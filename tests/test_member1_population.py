from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1]
M=R/'member1_demographics'
def test_panel_coverage_and_keys():
 d=pd.read_csv(R/'data/processed/demographics.csv');lookup=pd.read_csv(R/'data/reference/region_lookup.csv')
 for year in range(2011,2023):
  g=d[d.year==year]
  assert len(g)==98 and set(zip(g.country,g.region_id))==set(zip(lookup.country,lookup.region_id))
 assert not d.duplicated(['country','region_id','year']).any()
def test_age_counts_and_rounding():
 d=pd.read_csv(M/'population_detail_2011_2022.csv')
 assert len(d)==1176 and not d.isna().any().any()
 residual=d.population_0_14+d.population_15_64+d.population_65plus-d.population_total
 assert (abs(residual)<=2*d.count_precision_persons).all()
 us=d[d.country=='USA'];assert (residual.loc[us.index]==0).all()
 assert (abs(d.population_65plus/d.population_total*100-d.age65_share_pct)<.2).all()
def test_national_series_separate_and_complete():
 d=pd.read_csv(M/'national_trends_wpp2024_2000_2022.csv')
 assert len(d)==46 and set(d.country)=={'USA','JPN'}
 for _,g in d.groupby('country'):assert set(g.year)==set(range(2000,2023))
 assert set(d.source_version)=={'UN WPP2024'} and set(d.variant)=={'Estimates'}
 assert np.allclose(d.age65_share_pct+d.working_age_share_pct+d.age0_14_share_pct,100,atol=1e-5)
def test_released_2022_population_rates_preserved():
 core=pd.read_csv(R/'data/processed/demographics.csv').query('year==2022')
 detail=pd.read_csv(M/'population_2022.csv')
 x=core.merge(detail,on=['country','region_id','year'],validate='one_to_one',suffixes=('_core','_detail'))
 assert len(x)==98
 assert np.allclose(x.age65_share_pct_core,x.age65_share_pct_detail,atol=1e-7,rtol=0)
 assert (x.total_population==x.population_total).all()
 assert set(pd.read_csv(M/'population_2019.csv').region_id)==set(core.region_id)
