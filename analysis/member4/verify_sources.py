"""Offline exhaustive and sampled checks against separately retrieved official sources.

Run download_sources.py first. Reuses Member 2's inspected read-only parsers.
No teammate production entry point is executed.
"""
from pathlib import Path
import csv, hashlib, importlib.util, io, json, re, sys
from zipfile import ZipFile
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RAW=ROOT/'data/raw/member4'
KEY=['country','region_id','year']

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def main(output_dir=None):
    from freeze_inputs import main as protect
    protect()
    if output_dir is None and (ROOT/'docs/remediation/prechange_manifest.json').exists():
        output_dir=ROOT/'data/cache/remediation/current_member4'
    if (ROOT/'docs/remediation/prechange_manifest.json').exists() and not Path(output_dir).resolve().is_relative_to(ROOT/'data/cache'):
        raise ValueError('Remediation verification must preserve historical audit files; use data/cache')
    audit=(Path(output_dir) if output_dir is not None else HERE)/'audit';audit.mkdir(parents=True,exist_ok=True)
    manifest={r['file']:r for r in json.loads((HERE/'audit/download_manifest.json').read_text())}
    for name,r in manifest.items():
        if r['status']=='retrieved':
            assert hashlib.sha256((RAW/name).read_bytes()).hexdigest()==r['sha256']
            if r['expected_sha256']: assert r['matches_pinned_hash'],f'Unreviewed vintage: {name}'
    dem=pd.read_csv(ROOT/'data/processed/demographics.csv').set_index(KEY)
    detail=pd.read_csv(ROOT/'member1_demographics/population_detail_2011_2022.csv').set_index(KEY)
    ind=pd.read_csv(ROOT/'data/processed/industry.csv').set_index(KEY)
    lab=pd.read_csv(ROOT/'data/processed/labor_migration.csv').set_index(KEY)
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv')
    names=lookup.set_index('region_name').region_id.to_dict()
    checks=[]
    def check(source,key,field,official,actual,tolerance=1e-7,scope='exhaustive',location=''):
        country,rid,year=key
        checks.append(dict(source_file=source,country=country,region_id=rid,year=year,field=field,
                           official_value=official,delivered_value=actual,difference=float(actual)-float(official),
                           tolerance=tolerance,status='PASS' if abs(float(actual)-float(official))<=tolerance else 'BLOCKED',
                           scope=scope,source_location=location))
    # Independent population aggregation, not a rerun of the owner's writer.
    for name,years in [('us_2010_2020.csv',range(2011,2020)),('us_2020_2022.csv',range(2020,2023))]:
        f=pd.read_csv(RAW/name)
        f=f[(f.SUMLEV==40)&(f.SEX==0)&(f.ORIGIN==0)]
        assert set(f.RACE)==set(range(1,7)) and set(f.AGE)==set(range(86))
        assert not f.duplicated(['STATE','RACE','AGE']).any()
        for year in years:
            col=f'POPESTIMATE{year}'
            for region,g in f.groupby('NAME'):
                key=('USA',names[region],year)
                total=g[col].sum();older=g.loc[g.AGE>=65,col].sum();working=g.loc[g.AGE.between(15,64),col].sum()
                for field,value in [('total_population',total),('age65_share_pct',100*older/total),('working_age_share_pct',100*working/total),('old_age_dependency_ratio',100*older/working)]:
                    check(name,key,field,value,dem.loc[key,field],location=f'{region}; {col}; SEX=0 ORIGIN=0 RACE=1..6 AGE=0..85')
    for sheet,years,step,base in [(0,range(2011,2015),4,2000),(3,range(2015,2021),6,2015)]:
        f=pd.read_excel(RAW/'jp_long.xlsx',sheet_name=sheet,header=None)
        regions=f.loc[pd.to_numeric(f[1],errors='coerce').between(1,47)]
        assert len(regions)==47
        for year in years:
            col=4+(year-base)*step
            for idx,r in regions.iterrows():
                key=('JPN',f'JP-{int(r[1]):02d}',year)
                total,young,working,older=[float(r[col+i])*1000 for i in range(4)]
                for field,value in [('total_population',total),('age65_share_pct',100*older/total),('working_age_share_pct',100*working/total),('old_age_dependency_ratio',100*older/working)]:
                    check('jp_long.xlsx',key,field,value,dem.loc[key,field],location=f'sheet {sheet}; row {idx+1}; zero-based column {col}')
    for year in [2021,2022]:
        tables={n:pd.read_excel(RAW/f'jp{year}_table{n}.xlsx',header=None) for n in [11,12,13]}
        for code in range(1,48):
            row=8+code; key=('JPN',f'JP-{code:02d}',year)
            assert str(tables[11].iloc[row,10]).strip()==f'{code:02d}000'
            for n,col,field,scale in [(11,14,'total_population',1000),(12,17,'age65_share_pct',1),(12,16,'working_age_share_pct',1),(13,14,'old_age_dependency_ratio',1)]:
                check(f'jp{year}_table{n}.xlsx',key,field,float(tables[n].iloc[row,col])*scale,dem.loc[key,field],location=f'row {row+1}; column {col+1}; total residents')
    # Full industry's 12 years, plus independent GDP reconciliation through owner's pure functions.
    m2=load_module('member2_source_reader',ROOT/'member2_industry/prepare_industry.py')
    with ZipFile(RAW/'SAGDP.zip') as z:
        records=list(csv.DictReader(io.StringIO(z.read(m2.BEA_TABLE).decode('utf-8-sig'))))
    generated=m2.usa_rows(records,lookup.to_dict('records'))
    summary=m2.xlsx_cells(RAW/'soukatu1.xlsx','実数');jp_audit=[]
    with pd.ExcelFile(RAW/'syuyo1.xlsx') as x:
        sheet_names=x.sheet_names
    for year in m2.YEARS:
        sheet=next(s for s in sheet_names if s.startswith(f'{year}（'))
        rows,tests=m2.japan_rows(m2.xlsx_cells(RAW/'syuyo1.xlsx',sheet),summary,year)
        generated.extend(rows);jp_audit.extend(tests)
    for r in generated:
        key=(r['country'],r['region_id'],int(r['year']))
        source='SAGDP.zip' if r['country']=='USA' else 'syuyo1.xlsx'
        for field in ['nominal_gdp_local','manufacturing_va_local','services_va_local','manufacturing_share_pct','services_share_pct']:
            check(source,key,field,float(r[field]),ind.loc[key,field],location='SAGDP2 lines 1/12/92' if r['country']=='USA' else f"FY{r['year']}; I/BL/BO and soukatu1 GDP cross-check")
    pd.DataFrame(jp_audit).to_csv(audit/'japan_gdp_reconciliation.csv',index=False)
    # Labour file's workbook contains a rolling release, now identified by local SHA.
    m3=load_module('member3_source_reader',ROOT/'member3_labor_migration/prepare_labor.py')
    jplab=m3.read_labour(RAW/'jpn_lfs.xlsx')
    jdetail=pd.read_csv(ROOT/'member3_labor_migration/jpn_labor_detail.csv').set_index(['region_id','year'])
    for year,regions in jplab.items():
        assert len(regions)==47
        for rid,r in regions.items():
            for field,value in r.items():
                check('jpn_lfs.xlsx',('JPN',rid,year),field,value,jdetail.loc[(rid,year),field],tolerance=1e-7,location='annual time-series sheets 2/3/4/6; C:AW')
            for field in ['employment','unemployment_rate_pct']:
                check('jpn_lfs.xlsx',('JPN',rid,year),field,jplab[year][rid][field],lab.loc[('JPN',rid,year),field],location='canonical table comparison')
    # All 47 migration records in both analytical years; no external conversion needed.
    domestic=[]
    for year,suffix in [(2019,'xls'),(2022,'xlsx')]:
        name=f'jpn_migration_{year}.{suffix}';f=pd.read_excel(RAW/name,header=None)
        assert 'All nationalities' in str(f.iloc[:18].values)
        rows=f.loc[f[8].map(lambda v:isinstance(v,str) and bool(re.fullmatch(r'\d{2}',v.strip())))]
        rows=rows.loc[rows[8].astype(int).between(1,47)]
        assert len(rows)==47
        for idx,r in rows.iterrows():
            rid=f'JP-{int(r[8]):02d}';value=int(r[20])
            assert value==int(r[14])-int(r[17])
            check(name,('JPN',rid,year),'net_migration',value,lab.loc[('JPN',rid,year),'net_migration'],tolerance=0,location=f'row {idx+1}, U; all nationalities')
            domestic.append(dict(country='JPN',region_id=rid,year=year,domestic_net_migration=value,
                                 migration_reference_period=f'CY{year}',migration_population='registered residents; all nationalities',migration_source=name))
    # The older table is explicitly Japanese-only; compare values without harmonizing scope.
    f=pd.read_excel(RAW/'jpn_migration_trend.xls',header=None)
    assert 'Japanese' in str(f.iloc[6].values)
    for year in range(2011,2018):
        columns=[i for i,v in f.iloc[13].items() if v==year];assert len(columns)==3
        col=columns[2]
        rows=f.loc[f[8].map(lambda v:isinstance(v,str) and bool(re.fullmatch(r'\d{2}',v.strip())))]
        rows=rows.loc[rows[8].astype(int).between(1,47)]
        assert len(rows)==47
        for idx,r in rows.iterrows():
            rid=f'JP-{int(r[8]):02d}'
            check('jpn_migration_trend.xls',('JPN',rid,year),'net_migration',int(r[col]),lab.loc[('JPN',rid,year),'net_migration'],0,location=f'row {idx+1}, column {col+1}; Japanese-only header row 7')
    # Preserve original total net migration; derive a separately named domestic series.
    f=pd.read_csv(RAW/'us_migration_2022.csv',encoding='utf-8-sig')
    f=f.loc[(f.SUMLEV==40)&f.NAME.isin(names)];assert len(f)==51
    for _,r in f.iterrows():
        rid=names[r.NAME]
        for year in [2021,2022]:
            check('us_migration_2022.csv',('USA',rid,year),'net_migration',r[f'NETMIG{year}'],lab.loc[('USA',rid,year),'net_migration'],0,location=f'{r.NAME}; NETMIG{year}; domestic plus international')
        domestic.append(dict(country='USA',region_id=rid,year=2022,domestic_net_migration=r.DOMESTICMIG2022,
                             migration_reference_period='2021-07-01 to 2022-07-01',migration_population='resident population; domestic moves',migration_source='us_migration_2022.csv'))
    f=pd.read_csv(RAW/'us_migration_2020.csv',encoding='utf-8-sig')
    f=f.loc[(f.SUMLEV==40)&f.NAME.isin(names)];assert len(f)==51
    for _,r in f.iterrows():
        rid=names[r.NAME]
        for year in range(2011,2021):
            check('us_migration_2020.csv',('USA',rid,year),'net_migration',r[f'NETMIG{year}'],lab.loc[('USA',rid,year),'net_migration'],0,location=f'{r.NAME}; NETMIG{year}; domestic plus international')
        domestic.append(dict(country='USA',region_id=rid,year=2019,domestic_net_migration=r.DOMESTICMIG2019,
                             migration_reference_period='2018-07-01 to 2019-07-01',migration_population='resident population; domestic moves',migration_source='us_migration_2020.csv'))
    # Sample transcribed from original BLS table 1 via web access (raw HTTP returns 403).
    # Columns: state, year, LF thousand, employed thousand, unemployed thousand, rate %.
    samples=[('US-CA',2022,19252,18441,811,4.2),('US-NV',2022,1550,1466,84,5.4),
             ('US-IN',2022,3404,3303,102,3.0),('US-DC',2022,388,370,18,4.7),
             ('US-ME',2022,675,655,20,3.0),('US-ND',2022,414,406,9,2.1),
             ('US-CA',2019,19412,18627,784,4.0),('US-NV',2019,1542,1482,60,3.9),
             ('US-IN',2019,3387,3275,112,3.3),('US-DC',2019,410,387,22,5.5),
             ('US-ME',2019,693,672,21,3.0),('US-ND',2019,404,394,10,2.4)]
    pd.DataFrame(samples,columns=['region_id','year','labor_force_thousands','employment_thousands','unemployment_thousands','unemployment_rate_pct']).to_csv(audit/'bls_primary_table_sample.csv',index=False)
    for rid,year,lf,em,un,rate in samples:
        key=('USA',rid,year);source='BLS srgune_03012023 table 1' if year==2022 else 'BLS srgune_03042020 table 1'
        for field,value in [('employment',em*1000),('unemployment_rate_pct',rate)]:
            check(source,key,field,value,lab.loc[key,field],0,scope='sampled 6 of 51 regions per year',location='Original BLS page inspected 2026-11-09; derived snapshot, not raw HTML')
    # Rounded counts imply a feasible interval, not exact equality to a one-decimal rate.
    rounding=[]
    for country,name in [('USA','us_labor_detail.csv'),('JPN','jpn_labor_detail.csv')]:
        d=pd.read_csv(ROOT/'member3_labor_migration'/name)
        for r in d.itertuples():
            lower=100*max(0,r.unemployment-500)/(r.labor_force+500)
            upper=100*(r.unemployment+500)/(r.labor_force-500)
            ok=(r.unemployment_rate_pct+.05>=lower-1e-9 and r.unemployment_rate_pct-.05<=upper+1e-9)
            rounding.append(dict(country=country,region_id=r.region_id,year=r.year,rate=r.unemployment_rate_pct,
                                 feasible_rate_min=lower,feasible_rate_max=upper,rounding_consistent=ok,
                                 identity_gap_persons=r.labor_force-r.employment-r.unemployment))
    pd.DataFrame(rounding).to_csv(audit/'labor_count_rounding.csv',index=False)
    pd.DataFrame(domestic).sort_values(KEY).to_csv(audit/'verified_domestic_migration.csv',index=False)
    df=pd.DataFrame(checks).sort_values(['source_file']+KEY+['field','source_location'])
    df.to_csv(audit/'source_record_checks.csv',index=False,float_format='%.10f')
    sums=df.groupby(['source_file','scope'],as_index=False).agg(checks=('status','size'),failed=('status',lambda s:(s!='PASS').sum()),max_absolute_difference=('difference',lambda s:s.abs().max()))
    sums.to_csv(audit/'source_check_summary.csv',index=False)
    print(sums.to_string(index=False))
    print('Labor rounding failures:',sum(not r['rounding_consistent'] for r in rounding))
    if (df.status!='PASS').any() or any(not r['rounding_consistent'] for r in rounding):
        raise AssertionError('Source or rounding differences require review; see current source_record_checks.csv')
    protect()

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path)
    main(parser.parse_args().output_dir)
