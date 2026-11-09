"""Rebuild Member 3 from pinned official sources and traceable BLS page snapshots.

No existing processed CSV is used as an input. Legacy net_migration is retained
with explicit definitions; domestic, international and total fields are separate.
Japanese-only 2011-2017 domestic counts never fill the all-nationality series.
"""
from pathlib import Path
import argparse, csv, json, re, sys
import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]
MEMBER_DIR=ROOT/'member3_labor_migration'
RAW=ROOT/'data/raw/member3'
YEARS=tuple(range(2011,2023))
KEY=['country','region_id','year']
sys.path.insert(0,str(MEMBER_DIR))
sys.path.insert(0,str(ROOT/'src'))
from aging_economies.source_io import digest
from bls_sources import load_archives
from labor_validation import validate_labor_counts,validate_panel


def read_labour(path):
    """Official annual sheets 2/3/4/6, thousand-person counts converted to persons."""
    book=load_workbook(path,data_only=True,read_only=True)
    result={year:{} for year in YEARS}
    try:
        for keyword,field,scale in [('第２表','labor_force',1000),('第３表','employment',1000),
                                    ('第４表','unemployment',1000),('第６表','unemployment_rate_pct',1)]:
            sheet=book[next(n for n in book.sheetnames if keyword in n)]
            rows=list(sheet.iter_rows(values_only=True))
            for year in YEARS:
                matches=[r for r in rows if len(r)>1 and str(r[1]).strip() in (str(year),f'{year}.0')]
                if len(matches)!=1:raise ValueError(f'LFS annual year row missing/duplicated: {year}')
                for code,value in enumerate(matches[0][2:49],1):
                    if not isinstance(value,(int,float)):raise ValueError('Missing LFS prefectural estimate')
                    result[year].setdefault(f'JP-{code:02d}',{})[field]=float(value)*scale
    finally:book.close()
    return result


def prefecture_rows(frame):
    rows=frame.loc[frame[8].map(lambda v:isinstance(v,str) and bool(re.fullmatch(r'\d{2}',v.strip())))]
    rows=rows.loc[rows[8].astype(int).between(1,47)]
    if len(rows)!=47 or rows[8].nunique()!=47:raise ValueError('Expected all 47 prefectures')
    return rows


def read_net_migration(path):
    frame=pd.read_excel(path,header=None)
    if 'All nationalities' not in str(frame.iloc[:18].values):raise ValueError('Expected all-nationality migration header')
    rows=prefecture_rows(frame);result={}
    for _,r in rows.iterrows():
        net,inward,outward=int(r[20]),int(r[14]),int(r[17])
        if net!=inward-outward:raise ValueError('Japanese migration inflow/outflow identity failed')
        result[f'JP-{int(r[8]):02d}']=net
    if sum(result.values())!=0:raise ValueError('Inter-prefectural net migration must sum to zero')
    return result


def read_annual_trend(path,years=tuple(range(2011,2018))):
    frame=pd.read_excel(path,header=None)
    if 'Japanese' not in str(frame.iloc[6].values):raise ValueError('Expected Japanese-only header')
    rows=prefecture_rows(frame);result={}
    for year in years:
        cols=[i for i,v in frame.iloc[13].items() if v==year]
        if len(cols)!=3:raise ValueError('Three year blocks required in historical migration source')
        result[year]={f'JP-{int(r[8]):02d}':int(r[cols[2]]) for _,r in rows.iterrows()}
        if sum(result[year].values())!=0:raise ValueError('Japanese-only domestic totals must sum to zero')
    return result


def read_census_migration(path,years,lookup):
    names=lookup.loc[lookup.country=='USA'].set_index('region_name').region_id.to_dict()
    frame=pd.read_csv(path,encoding='utf-8-sig')
    frame=frame.loc[(frame.SUMLEV==40)&frame.NAME.isin(names)]
    if len(frame)!=51 or frame.NAME.nunique()!=51:raise ValueError('Census must include 50 states and DC')
    rows=[]
    for _,r in frame.iterrows():
        for year in years:
            domestic,international,total=[int(r[f'{field}{year}']) for field in ['DOMESTICMIG','INTERNATIONALMIG','NETMIG']]
            if domestic+international!=total:raise ValueError('Census migration components do not reconcile')
            rows.append(dict(country='USA',region_id=names[r.NAME],year=year,
                net_migration=total,domestic_net_migration=domestic,
                international_net_migration=international,total_net_migration=total,
                japanese_only_domestic_net_migration=np.nan,migration_population='all residents',
                migration_period_type='July-to-July',migration_start_date=f'{year-1}-07-01',
                migration_end_date=f'{year}-07-01',migration_source_file=path.name,
                migration_original_definition='total domestic plus international',
                migration_source_version='Census Vintage 2020' if year<=2020 else 'Census Vintage 2022'))
    return pd.DataFrame(rows)


def verify_raw(raw):
    records=json.loads((ROOT/'docs/remediation/acquisition.json').read_text(encoding='utf-8'))
    verified=[]
    for r in records:
        if r['owner']!='member3' or r['file'].startswith('bls_'):continue
        path=raw/r['file']
        if r['status']=='unavailable' or not path.exists():raise FileNotFoundError(f'Official source unavailable: {r["file"]}')
        if digest(path)!=r['sha256']:raise ValueError(f'Pinned source changed: {r["file"]}')
        verified.append(r)
    if len(verified)!=9:raise ValueError('Nine Japan/Census files required')
    return verified


def build(raw=RAW,output_root=ROOT):
    destination=Path(output_root).resolve()
    if destination!=ROOT and not destination.is_relative_to(ROOT/'data/cache'):
        raise ValueError('Output root must be the project root or an isolated data/cache directory')
    raw=Path(raw)
    source_records=verify_raw(raw)
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv')
    us_labor,prior,bls_evidence=load_archives(raw,MEMBER_DIR/'source_snapshots',lookup)
    japanese=read_labour(raw/'jpn_lfs.xlsx')
    jp_labor=pd.DataFrame([dict(country='JPN',region_id=rid,year=year,**values)
                          for year,regions in japanese.items() for rid,values in regions.items()])
    early=read_annual_trend(raw/'jpn_migration_trend.xls')
    jp_migration=[]
    for year in YEARS:
        suffix='xlsx' if year==2022 else 'xls'
        all_residents=year>=2018
        values=read_net_migration(raw/f'jpn_migration_{year}.{suffix}') if all_residents else early[year]
        for rid,value in values.items():
            jp_migration.append(dict(country='JPN',region_id=rid,year=year,net_migration=value,
                domestic_net_migration=value if all_residents else np.nan,
                international_net_migration=np.nan,total_net_migration=np.nan,
                japanese_only_domestic_net_migration=np.nan if all_residents else value,
                migration_population='all nationalities' if all_residents else 'Japanese nationals only',
                migration_period_type='calendar year',migration_start_date=f'{year}-01-01',
                migration_end_date=f'{year}-12-31',migration_source_file=f'jpn_migration_{year}.{suffix}' if all_residents else 'jpn_migration_trend.xls',
                migration_original_definition='inter-prefectural domestic; '+('all nationalities' if all_residents else 'Japanese nationals only'),
                migration_source_version=f'Basic Resident Registration annual {year}' if all_residents else 'Basic Resident Registration 2017 trend table 3'))
    us_migration=pd.concat([read_census_migration(raw/'us_migration_2020.csv',range(2011,2021),lookup),
                            read_census_migration(raw/'us_migration_2022.csv',[2021,2022],lookup)],ignore_index=True)
    labor=pd.concat([us_labor,jp_labor],ignore_index=True)
    migration=pd.concat([us_migration,pd.DataFrame(jp_migration)],ignore_index=True)
    frame=labor.merge(migration,on=KEY,validate='one_to_one')
    frame['labor_population']=np.where(frame.country=='USA','civilian noninstitutional ages 16+','LFS ages 15+')
    frame['labor_period']='calendar-year annual average; annual non-seasonally-adjusted series'
    frame['labor_source']=np.where(frame.country=='USA',frame.source_release,'Japan LFS tables 2/3/4/6; pinned retrieved workbook')
    frame['labor_reproduction_status']=np.where(frame.country=='USA','reproduced from traceable official-page text snapshots','reproduced from pinned official workbook')
    frame['labor_count_precision_persons']=1000
    frame['labor_estimation_note']=np.where(frame.country=='USA','LAUS residence-based persons; annual releases contain revisions',
        'LFS prefectural model/ratio estimates; 2011 disaster and 2016 Kumamoto notes; benchmark revisions')
    frame=frame.drop(columns=['source_release','civilian_population_16plus','employment_population_ratio_pct']).sort_values(KEY).reset_index(drop=True)
    first=KEY+['employment','unemployment_rate_pct','net_migration']
    frame=frame[first+[c for c in frame if c not in first]]
    validate_panel(frame,lookup)
    rounding=[]
    for country,d in [('USA',us_labor),('JPN',jp_labor)]:
        rounding.append(validate_labor_counts(d).assign(country=country))
    # Check against the independent Member 4 adapter, without using it to create values.
    reference=pd.read_csv(ROOT/'analysis/member4/audit/verified_domestic_migration.csv')
    comparison=reference.merge(frame[KEY+['domestic_net_migration']],on=KEY,validate='one_to_one',
                               suffixes=('_member4','_rebuilt'))
    comparison['difference']=comparison.domestic_net_migration_rebuilt-comparison.domestic_net_migration_member4
    if len(comparison)!=196 or not comparison.difference.eq(0).all():raise ValueError('Independent domestic migration comparison failed')
    out=destination/'member3_labor_migration';out.mkdir(parents=True,exist_ok=True)
    processed=destination/'data/processed';processed.mkdir(parents=True,exist_ok=True)
    frame.to_csv(processed/'labor_migration.csv',index=False,float_format='%.10f')
    detail=['region_id','year','labor_force','employment','unemployment','unemployment_rate_pct']
    jp_labor[detail].sort_values(['region_id','year']).to_csv(out/'jpn_labor_detail.csv',index=False,float_format='%.10f')
    us_labor.sort_values(['region_id','year']).to_csv(out/'us_labor_detail.csv',index=False,float_format='%.10f')
    pd.concat(rounding,ignore_index=True).to_csv(out/'rounding_validation.csv',index=False,float_format='%.10f')
    comparison.to_csv(out/'domestic_migration_comparison.csv',index=False,float_format='%.10f')
    coverage=[]
    for (country,year),group in frame.groupby(['country','year']):
        for indicator in ['employment','unemployment_rate_pct','net_migration','domestic_net_migration',
                          'international_net_migration','total_net_migration','japanese_only_domestic_net_migration']:
            coverage.append(dict(country=country,year=int(year),indicator=indicator,rows=len(group),
                                 valid=int(group[indicator].notna().sum()),missing=int(group[indicator].isna().sum())))
    pd.DataFrame(coverage).to_csv(out/'coverage.csv',index=False)
    header=['owner','dataset','source_organization','source_title','source_url','original_table','coverage','reference_period','download_date','notes']
    sources=[]
    for r in source_records:
        japan=r['file'].startswith('jpn')
        sources.append(dict(zip(header,['member3_labor_migration','labor_migration',
            'Statistics Bureau of Japan / e-Stat' if japan else 'U.S. Census Bureau',r['file'],r['url'],
            'LFS 2/3/4/6' if 'lfs' in r['file'] else ('Table 3: Japanese nationals only' if 'trend' in r['file'] else ('Table 1: all nationalities' if japan else 'DOMESTICMIG, INTERNATIONALMIG, NETMIG annual fields')),
            '47 prefectures' if japan else '50 states plus DC',
            'calendar years; see row-level dates' if japan else 'July-to-July; Vintage2020 through 2020 and Vintage2022 for 2021-22',
            '2026-11-09','SHA-256 '+r['sha256']+'; canonical row metadata records scope and period; raw cache '+r['file']])))
    for r in bls_evidence:
        r['path']=Path(r['path']).relative_to(ROOT).as_posix()
        sources.append(dict(zip(header,['member3_labor_migration','labor_employment_usa','U.S. Bureau of Labor Statistics',
            'LAUS annual averages '+str(r['year']),r['url'],'Table 1; current-year annual column','50 states plus DC',
            f'CY{r["year"]} annual average','2026-11-09','Counts in thousands multiplied by 1000; '+r['input_type']+'; SHA-256 '+r['sha256']])))
    with (out/'sources.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=header);writer.writeheader();writer.writerows(sources)
    summary=dict(rows=len(frame),years=list(YEARS),regions={'USA':51,'JPN':47},unique_keys=True,
        domestic_migration_main_year_comparisons=196,domestic_comparison_max_difference=0,
        historical_all_nationality_Japan='BLOCKED before 2018; separate Japanese-only field retained',
        us_labor='All 612 source rows independently read from official archive text; cached parsing reproducible; direct HTML HTTP403',
        labor_rounding_checks=len(labor),labor_rounding_failures=0,
        source_files=source_records,bls_evidence=bls_evidence)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(f'Rebuilt {len(frame)} rows from official inputs; 196 independent domestic comparisons passed.')
    print('Japan all-nationality domestic migration: 2018-2022 only; 2011-2017 remains a separate series.')
    return frame


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--raw-dir',type=Path,default=RAW)
    parser.add_argument('--output-root',type=Path,default=ROOT)
    args=parser.parse_args()
    if args.download:
        sys.path.insert(0,str(ROOT/'scripts'))
        from fetch_remediation_sources import main as fetch
        fetch('member3')
    build(args.raw_dir,args.output_root)


