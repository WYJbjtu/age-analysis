"""Offline parsers and exact age harmonization; reads only declared deliverables."""
from pathlib import Path
import argparse
import json
import re
import numpy as np
import pandas as pd
from acquire import MODULE, digest, json_read, json_write
from model import (YEARS, KEY, COUNTS, GROUPS, acs_value, rss, ratio_moe90,
                   direction, age_bounds, covered_bins, validate_regions,
                   validate_flows, safe_join, rounded_rate_check)

ROOT = MODULE.parents[1]


def csv_write(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding='utf-8', lineterminator='\n', float_format='%.15g')


class Sources:
    def __init__(self, module=MODULE):
        self.module = Path(module)
        rows = json_read(self.module / 'sources/manifest.json')
        self.rows = {r['id']: r for r in rows}
        if len(rows) != len(self.rows):
            raise ValueError('Duplicate source ID')
        for row in rows:
            path = self.module / 'sources/raw' / row['file']
            if Path(row['file']).name != row['file'] or digest(path.read_bytes()) != row['sha256']:
                raise ValueError('Raw official source missing or checksum changed: ' + row['id'])

    def path(self, sid, year=None):
        row = self.rows[sid]
        if year is not None and row['year'] != year:
            raise ValueError('Source year mismatch')
        return self.module / 'sources/raw' / row['file']


def us_table(source, year, table):
    if year not in YEARS or table not in ('B07001', 'B07401', 'B01001'):
        raise ValueError('Unsupported ACS year/table/product')
    path = source.path(f'acs{year}_{table}_summary', year)
    if path.name != f'acsdt1y{year}-{table.lower()}.dat':
        raise ValueError('Source file year/table cannot be swapped')
    frame = pd.read_csv(path, sep='|', dtype=str, keep_default_na=False, encoding='utf-8-sig')
    if frame.GEO_ID.duplicated().any():
        raise ValueError('Duplicate ACS geography')
    meta = json_read(source.path(f'acs{year}_{table}_metadata', year))['variables']
    renamed = {}
    for col in frame.columns:
        if col == 'GEO_ID':
            continue
        match = re.fullmatch(fr'{table}_([EM])(\d{{3}})', col)
        if not match:
            raise ValueError('Unexpected table-based ACS column')
        key = f'{table}_{match[2]}{match[1]}'
        if key not in meta or meta[key]['group'] != table:
            raise ValueError('ACS column missing from official metadata')
        renamed[col] = key
    return frame.rename(columns=renamed), meta


def us_mapping(meta, table, role):
    """Select using official meanings, never an assumed index offset."""
    if (table,role) not in {('B07001','in'),('B07401','out'),('B07001','age_population')}:
        raise ValueError('Incompatible ACS residence base or migration role')
    selected = []
    flow = {'in': 'moved from different state', 'out': 'moved to different state'}
    for key, variable in sorted(meta.items()):
        if not re.fullmatch(fr'{table}_\d{{3}}E', key):
            continue
        parts = [p.rstrip(':').strip().lower() for p in variable['label'].split('!!')]
        if role in flow:
            if len(parts) not in (3, 4) or parts[2] != flow[role]:
                continue
            label = 'total_1plus' if len(parts) == 3 else variable['label'].split('!!')[-1]
        elif role == 'age_population':
            if len(parts) not in (2, 3) or parts[1] != 'total':
                continue
            if len(parts) == 3 and parts[2].startswith(('moved ', 'same house')):
                continue
            label = 'total_1plus' if len(parts) == 2 else variable['label'].split('!!')[-1]
        else:
            raise ValueError('Unknown mapping role')
        bounds = (None, None) if label == 'total_1plus' else age_bounds(label)
        name = label if label == 'total_1plus' else f'{bounds[0]}+' if bounds[1] is None else f'{bounds[0]}-{bounds[1]}'
        selected.append(dict(role=role, variable=key, moe_variable=key[:-1] + 'M',
                             estimate_annotation_variable=key + 'A', moe_annotation_variable=key[:-1] + 'MA',
                             source_label=variable['label'], age_group=name,
                             age_lower=bounds[0], age_upper=bounds[1]))
    if len(selected) != 16 or len({r['age_group'] for r in selected}) != 16:
        raise ValueError('Expected 15 native ACS age groups plus total')
    return selected


def parse_usa(source, lookup, fips):
    native, denominator, mapping, cells, checks, structure = [], [], [], [], [], []
    for year in YEARS:
        tables = {t: us_table(source, year, t) for t in ('B07001', 'B07401', 'B01001')}
        values = {}
        for role, table in [('in', 'B07001'), ('out', 'B07401'), ('age_population', 'B07001')]:
            frame, meta = tables[table]
            rows = us_mapping(meta, table, role)
            for row in rows:
                mapping.append(dict(country='USA', year=year, source_id=f'acs{year}_{table}_summary', **row))
            states = frame.loc[frame.GEO_ID.str.fullmatch(r'0400000US\d{2}')].copy()
            states['fips'] = states.GEO_ID.str[-2:]
            states = states.loc[states.fips.isin(fips)]
            if len(states) != 51 or set(states.fips) != set(fips):
                raise ValueError('Expected exactly 50 US states and DC')
            for _, s in states.iterrows():
                rid = fips[s.fips]
                for spec in rows:
                    est, ann, flag = acs_value(s[spec['variable']])
                    moe, mann, mflag = acs_value(s[spec['moe_variable']], moe=True)
                    values.setdefault((rid, spec['age_group']), {}).update({role: est, role + '_moe': moe,
                        role + '_annotation': ann, role + '_moe_annotation': mann,
                        'age_lower': spec['age_lower'], 'age_upper': spec['age_upper']})
                    cells.append(dict(country='USA', region_id=rid, year=year, role=role,
                        variable=spec['variable'], estimate_raw=s[spec['variable']],
                        moe_raw=s[spec['moe_variable']], estimate=est, moe90=moe,
                        estimate_annotation=ann, moe_annotation=mann,
                        estimate_status=flag, moe_status=mflag,
                        annotation_representation='decoded official numeric sentinel; separate EA/MA not in Summary File'))
            national = frame.loc[frame.GEO_ID == '0100000US']
            if table == 'B07401' and len(national) == 0:
                # Previous-residence B07401 has no published national geography.
                # Its interstate sum is tested against all state inflows below.
                continue
            if len(national) != 1:
                raise ValueError('ACS national row missing/duplicated')
            for spec in rows:
                numbers = [acs_value(v)[0] for v in states[spec['variable']]]
                expected = acs_value(national.iloc[0][spec['variable']])[0]
                actual = np.sum(numbers)
                checks.append(dict(check='ACS sum of states vs published US', country='USA', year=year,
                    age_group=spec['age_group'], indicator=role, actual=actual, expected=expected,
                    difference=actual-expected, passed=actual == expected))
        # B01001 keeps all-age total distinct from B07001's population aged1+.
        b, bm = tables['B01001']
        population_keys = []
        older_keys = []
        for key, spec in sorted(bm.items()):
            if not re.fullmatch(r'B01001_\d{3}E', key):
                continue
            parts = [v.rstrip(':').strip().lower() for v in spec['label'].split('!!')]
            if len(parts) == 4 and parts[2] in ('male', 'female'):
                lo, hi = age_bounds(parts[3])
                population_keys.append(key)
                if lo >= 65:
                    older_keys.append(key)
                mapping.append(dict(country='USA', year=year, source_id=f'acs{year}_B01001_summary',
                    role='age65_sensitivity_numerator' if lo >= 65 else 'population_total_reconciliation',
                    variable=key, moe_variable=key[:-1]+'M', source_label=spec['label'],
                    age_lower=lo, age_upper=hi, age_group=parts[3]))
        if len(older_keys) != 12 or len(population_keys) != 46:
            raise ValueError('B01001 sex/age metadata changed')
        mapping.append(dict(country='USA', year=year, source_id=f'acs{year}_B01001_summary',
            role='all_age_population', variable='B01001_001E', moe_variable='B01001_001M',
            source_label=bm['B01001_001E']['label'], age_group='total_all_ages'))
        totals = {}
        for _, row in b.loc[b.GEO_ID.str.fullmatch(r'0400000US\d{2}')].iterrows():
            if row.GEO_ID[-2:] not in fips:
                continue
            rid = fips[row.GEO_ID[-2:]]
            total, _, flag = acs_value(row.B01001_001E)
            total_moe, total_ann, total_mflag = acs_value(row.B01001_001M, moe=True)
            old = sum(acs_value(row[k])[0] for k in older_keys)
            old_moe = rss(acs_value(row[k[:-1]+'M'], moe=True)[0] for k in older_keys)
            totals[rid] = (total, total_moe, total_ann)
            for key in ['B01001_001E', *population_keys]:
                ev, ea, ef = acs_value(row[key]); mv, ma, mf = acs_value(row[key[:-1]+'M'], moe=True)
                cells.append(dict(country='USA',region_id=rid,year=year,role='B01001_population',variable=key,
                    estimate_raw=row[key],moe_raw=row[key[:-1]+'M'],estimate=ev,moe90=mv,
                    estimate_annotation=ea,moe_annotation=ma,estimate_status=ef,moe_status=mf,
                    annotation_representation='decoded official numeric sentinel'))
            subtotal = sum(acs_value(row[k])[0] for k in population_keys)
            checks.append(dict(check='ACS B01001 sex-age sum vs total',country='USA',region_id=rid,year=year,
                indicator='population_total',actual=subtotal,expected=total,difference=subtotal-total,passed=subtotal==total))
            structure.append(dict(country='USA',region_id=rid,year=year,acs_population_total=total,
                acs_population_65plus=old,acs_population_65plus_moe90_approx=old_moe,
                acs_age65_share_pct=100*old/total,acs_age65_share_moe90=np.nan,
                acs_age65_moe_status='not supplied: all-age denominator is controlled; no zero MOE substituted'))
        for (rid, age), v in sorted(values.items()):
            net = v['in'] - v['out']; nm = rss([v['in_moe'],v['out_moe']])
            base = dict(country='USA',region_id=rid,year=year,age_group=age,age_lower=v['age_lower'],age_upper=v['age_upper'])
            native.append({**base,'age_scheme':'native','row_type':'published_total' if age=='total_1plus' else 'native_age',
                'in_migration':v['in'],'out_migration':v['out'],'net_migration':net,
                'in_moe90':v['in_moe'],'out_moe90':v['out_moe'],'net_moe90':nm,
                'in_annotation':v['in_annotation'],'out_annotation':v['out_annotation'],
                'in_moe_annotation':v['in_moe_annotation'],'out_moe_annotation':v['out_moe_annotation'],
                'migration_source_id':f'acs{year}_B07001_summary;acs{year}_B07401_summary',
                'population_universe':'ACS resident population age1+; US interstate only; all citizenships; includes group quarters',
                'reference_period':f'{year} ACS 1-year; each interview vs residence one year earlier',
                'age_reference':'completed age at interview',
                'uncertainty_method':'90% RSS difference approximation; unknown covariance omitted',
                'uncertainty_status':direction(net,nm),'quality_flag':'survey estimate; not PEP decomposition'})
            total, tm, ta = totals[rid]
            denominator.append({**base,'age_scheme':'native','age_population':v['age_population'],
                'age_population_moe90':v['age_population_moe'],'age_population_moe_annotation':v['age_population_moe_annotation'],
                'population_total':total,'population_total_moe90':tm,'population_total_moe_annotation':ta,
                'population_source_id':f'acs{year}_B07001_summary',
                'total_population_source_id':f'acs{year}_B01001_summary',
                'population_reference_date':f'{year} ACS collection period; current residence at interview',
                'population_universe':'same-age current ACS residents; all-age total separately from B01001',
                'precision_persons':1})
    return native,denominator,mapping,cells,checks,structure


def japanese_age_columns(frame, header_row, start, end):
    result = []
    for col in range(start, end):
        label = str(frame.iloc[header_row,col]).strip()
        if col == start:
            if '総' not in label:
                raise ValueError('Missing Japanese total header')
            age, lo, hi = 'total_all_ages',None,None
        else:
            lo,hi = age_bounds(label)
            age = f'{lo}+' if hi is None else f'{lo}-{hi}'
        result.append((col,age,lo,hi,label))
    return result


def jp_count_table(source, year, flow):
    sheet = '移動者 総数' if year == 2019 else '移動者'
    frame = pd.read_excel(source.path(f'jpn{year}_{flow}',year),sheet_name=sheet,header=None)
    headings=' '.join(frame.iloc[:18].fillna('').astype(str).to_numpy().ravel())
    phrases={'in':'In-migrants from','out':'Out-migrants to','net':'Net-migration'}
    if str(year) not in headings or 'All nationalities' not in headings or phrases[flow] not in headings:
        raise ValueError('Japanese year/nationality/flow header mismatch')
    if year == 2022 and frame.iloc[11,21] != 'Both sexes':
        raise ValueError('Expected both sexes')
    columns=japanese_age_columns(frame,13 if year==2019 else 14,11 if year==2019 else 12,31 if year==2019 else 32)
    regions=frame.loc[frame[8].map(lambda v:isinstance(v,str) and bool(re.fullmatch(r'\d{2}',v.strip())))]
    if set(regions[8]) != {f'{i:02}' for i in range(1,48)} or len(regions)!=47:
        raise ValueError('Japanese prefecture code scope changed')
    result={}
    for _,r in regions.iterrows():
        rid=f'JP-{r[8].strip()}'
        for col,age,lo,hi,label in columns:
            value=r[col]
            if not isinstance(value,(int,float,np.number)) or not np.isfinite(value) or value!=int(value):
                raise ValueError('Missing/noninteger Japanese count; do not silently treat symbols as zero')
            result[rid,age]=int(value)
    national=frame.loc[frame[1].eq(0)]
    if len(national)!=1:raise ValueError('Missing/duplicate Japan total geography')
    checks=[]
    for col,age,lo,hi,label in columns:
        summed=sum(result[rid,age] for rid in {k[0] for k in result})
        expected=int(national.iloc[0][col])
        checks.append(dict(check='Japan sum of prefectures vs published Japan',country='JPN',year=year,
            age_group=age,indicator=flow,actual=summed,expected=expected,difference=summed-expected,passed=summed==expected))
    return result,columns,checks


def parse_japan(source):
    native,denominator,mapping,checks=[],[],[],[]
    for year in YEARS:
        tables={}
        for flow in ('in','out','net'):
            values,columns,check=jp_count_table(source,year,flow);tables[flow]=values;checks+=check
            for col,age,lo,hi,label in columns:
                mapping.append(dict(country='JPN',year=year,source_id=f'jpn{year}_{flow}',role=flow,
                    variable=f'sheet:{"移動者 総数" if year==2019 else "移動者"};column0:{col}',
                    source_label=label,age_group=age,age_lower=lo,age_upper=hi))
        ages={age:(lo,hi) for _,age,lo,hi,_ in columns}
        for rid in sorted({key[0] for key in tables['in']}):
            unknown={flow:values[rid,'total_all_ages']-sum(values[rid,a] for a in ages if a!='total_all_ages') for flow,values in tables.items()}
            if unknown['in']<0 or unknown['out']<0:
                raise ValueError('Age subtotals exceed published total')
            for age,(lo,hi) in {**ages,'unknown':(None,None)}.items():
                vals={flow:unknown[flow] if age=='unknown' else values[rid,age] for flow,values in tables.items()}
                if vals['in']-vals['out']!=vals['net']:
                    raise ValueError('Published Japanese net differs from in-out')
                native.append(dict(country='JPN',region_id=rid,year=year,age_group=age,age_lower=lo,age_upper=hi,
                    age_scheme='native',row_type='unknown_age_residual' if age=='unknown' else 'published_total' if age=='total_all_ages' else 'native_age',
                    in_migration=vals['in'],out_migration=vals['out'],net_migration=vals['net'],
                    in_moe90=np.nan,out_moe90=np.nan,net_moe90=np.nan,
                    migration_source_id=f'jpn{year}_in;jpn{year}_out;jpn{year}_net',
                    population_universe='all nationalities covered by Basic Resident Registration; both sexes',
                    reference_period=f'reports registered {year}-01-01 to {year}-12-31; repeated moves counted',
                    age_reference='registered age derived from birth date; precise day convention not stated in retrieved notes',
                    uncertainty_method='no ACS-style sampling MOE; registration/coverage errors remain',
                    uncertainty_status='no_sampling_interval',
                    quality_flag='unknown age = published total minus all named bins; official total includes unknown age' if age=='unknown' else 'registration events'))
        p=pd.read_excel(source.path(f'jpn{year}_population',year),header=None)
        if year==2019:
            if 'Total population' not in str(p.iloc[10,25]) or 'Both sexes' not in str(p.iloc[10,25]) or '2019' not in str(p.iloc[4,20]):
                raise ValueError('2019 population header mismatch')
            rows=p.loc[p[2].eq(1)&p[3].eq(1)&pd.to_numeric(p[8],errors='coerce').between(1,47)]
            columns=japanese_age_columns(p,13,12,31)
            codes=[f'JP-{int(r[8]):02}' for _,r in rows.iterrows()]
        else:
            rows=p.loc[p[9].eq('総人口')&p[12].eq('男女計')&p[10].astype(str).str.fullmatch(r'\d{2}000')&p[10].ne('00000')]
            if set(rows[8])!={'2022年10月1日現在'} or set(rows[14])!={'千人'}:raise ValueError('Population date/unit mismatch')
            columns=japanese_age_columns(p,6,15,34)
            codes=[f'JP-{str(r[10])[:2]}' for _,r in rows.iterrows()]
        if len(rows)!=47 or len(set(codes))!=47:raise ValueError('Population requires 47 prefectures')
        for rid,(_,r) in zip(codes,rows.iterrows()):
            total=float(r[columns[0][0]])*1000
            for col,age,lo,hi,label in columns:
                value=float(r[col])*1000
                if not np.isfinite(value) or value<=0:raise ValueError('Nonpositive same-age denominator')
                denominator.append(dict(country='JPN',region_id=rid,year=year,age_group=age,age_lower=lo,age_upper=hi,
                    age_scheme='native',age_population=value,age_population_moe90=np.nan,
                    population_total=total,population_total_moe90=np.nan,
                    population_source_id=f'jpn{year}_population',total_population_source_id=f'jpn{year}_population',
                    population_reference_date=f'{year}-10-01',population_universe='total residents, both sexes; published annual Population Estimates',
                    precision_persons=1000))
        for col,age,lo,hi,label in columns:
            mapping.append(dict(country='JPN',year=year,source_id=f'jpn{year}_population',role='age_population',
                variable=f'column0:{col};total population;both sexes',source_label=label,age_group=age,age_lower=lo,age_upper=hi))
    return native,denominator,mapping,checks


def harmonize(native,denominators):
    rows,pops=[],[]
    for key,group in native.groupby(['country','region_id','year'],sort=True):
        country,rid,year=key
        original=group.loc[group.row_type=='native_age']
        d=denominators.loc[(denominators.country==country)&(denominators.region_id==rid)&(denominators.year==year)&denominators.age_lower.notna()]
        for age,(lo,hi) in GROUPS.items():
            selected=covered_bins(original,lo,hi);pop=covered_bins(d,lo,hi)
            base=dict(country=country,region_id=rid,year=year,age_group=age,age_lower=lo,age_upper=hi,age_scheme='harmonized')
            first=selected.iloc[0]
            record={**first.to_dict(),**base,'row_type':'overlapping_supporting_aggregate' if age=='20-34' else 'ages20plus_profile',
                'native_components':';'.join(selected.age_group)}
            for c in COUNTS:record[c]=selected[c].sum(min_count=len(selected))
            for c in ['in_moe90','out_moe90']:record[c]=rss(selected[c])
            record['net_moe90']=rss([record['in_moe90'],record['out_moe90']])
            record['uncertainty_status']=direction(record['net_migration'],record['net_moe90'])
            rows.append(record)
            poprow={**pop.iloc[0].to_dict(),**base,'age_population':pop.age_population.sum(min_count=len(pop)),
                    'age_population_moe90':rss(pop.age_population_moe90),'population_components':';'.join(pop.age_group)}
            pops.append(poprow)
    return pd.DataFrame(rows),pd.DataFrame(pops)


def build(module=MODULE,root=ROOT,output=None):
    module,root=Path(module).resolve(),Path(root).resolve()
    out=Path(output).resolve() if output else module
    if out!=module and not out.is_relative_to(root/'data/cache'):
        raise ValueError('Outputs restricted to extension or isolated project data/cache')
    source=Sources(module)
    lookup=pd.read_csv(root/'data/reference/region_lookup.csv',encoding='utf-8')
    fips_table=pd.read_csv(root/'member1_demographics/boundary_join_checks.csv',dtype={'fips':str},encoding='utf-8')
    if len(fips_table)!=51 or fips_table.fips.nunique()!=51 or fips_table.region_id.nunique()!=51:
        raise ValueError('Audited FIPS mapping is not one-to-one')
    fips=dict(zip(fips_table.fips,fips_table.region_id))
    us,up,um,cells,uc,structure=parse_usa(source,lookup,fips)
    jp,jp_pop,jm,jc=parse_japan(source)
    native=pd.DataFrame(us+jp).sort_values(KEY).reset_index(drop=True)
    native=safe_join(native,lookup[['country','region_id','region_name']],['country','region_id'])
    pop=pd.DataFrame(up+jp_pop).sort_values(KEY).reset_index(drop=True)
    validate_regions(native,lookup);validate_flows(native)
    derived,dp=harmonize(native,pop)
    validate_regions(derived,lookup);validate_flows(derived)
    denom_cols=['age_population','age_population_moe90','population_total','population_total_moe90',
                'population_source_id','total_population_source_id','population_reference_date','precision_persons']
    joined=safe_join(derived,dp[KEY+denom_cols],KEY)
    canonical=pd.read_csv(root/'member1_demographics/population_detail_2011_2022.csv',encoding='utf-8')
    canonical=canonical.loc[canonical.year.isin(YEARS),['country','region_id','year','age65_share_pct','population_total','population_reference_date','source_version']].rename(
        columns={'population_total':'canonical_population_total','population_reference_date':'aging_reference_date','source_version':'aging_source_version'})
    joined=safe_join(joined,canonical,['country','region_id','year'])
    acs=pd.DataFrame(structure)
    joined=joined.merge(acs,on=['country','region_id','year'],how='left',validate='many_to_one')
    for col,den,dm in [('net_per_1000_same_age','age_population','age_population_moe90'),('net_per_1000_total','population_total','population_total_moe90')]:
        if joined[den].isna().any() or (joined[den]<=0).any():raise ValueError('Missing/nonpositive denominator')
        joined[col]=1000*joined.net_migration/joined[den]
        joined[col+'_moe90_approx']=[ratio_moe90(r.net_migration,getattr(r,den),r.net_moe90,getattr(r,dm)) for r in joined.itertuples()]
    joined['rate_direction_status']=[direction(r.net_per_1000_same_age,r.net_per_1000_same_age_moe90_approx) for r in joined.itertuples()]
    joined['aging_source_id']='member1_demographics/population_detail_2011_2022.csv'
    joined['rate_formula']='1000*(in_migration-out_migration)/named population denominator'
    validate_regions(joined,lookup)
    checks=uc+jc
    # Exact native age accounting, retaining the published unknown-age residual.
    for (country,rid,year),g in native.groupby(['country','region_id','year']):
        total=g[g.row_type=='published_total'].iloc[0]
        components=g[g.row_type!='published_total']
        for col in COUNTS:
            actual=components[col].sum(min_count=len(components));expected=total[col]
            checks.append(dict(check='Native age sum including unknown vs total',country=country,region_id=rid,year=year,
                indicator=col,actual=actual,expected=expected,difference=actual-expected,passed=actual==expected))
    for (country,year,age),g in native.groupby(['country','year','age_group']):
        diff=g.net_migration.sum(min_count=len(g))
        checks.append(dict(check='Countrywide interstate/inter-prefectural balance',country=country,year=year,age_group=age,
            indicator='net_migration',actual=diff,expected=0,difference=diff,passed=diff==0))
    old=pd.read_csv(root/'data/processed/labor_migration.csv',encoding='utf-8')
    old=old.loc[(old.country=='JPN')&old.year.isin(YEARS),['country','region_id','year','domestic_net_migration']]
    compared=safe_join(native.loc[(native.country=='JPN')&(native.row_type=='published_total')],old,['country','region_id','year'])
    for r in compared.itertuples():
        diff=r.net_migration-r.domestic_net_migration
        checks.append(dict(check='Japan vs repaired Member3 domestic total',country='JPN',region_id=r.region_id,year=r.year,
            actual=r.net_migration,expected=r.domestic_net_migration,difference=diff,passed=diff==0))
    # 2022 official percent rates use Oct1 same-age total population; verify rounding.
    rate=pd.read_excel(source.path('jpn2022_official_net_rate',2022),sheet_name='移動者',header=None)
    columns=japanese_age_columns(rate,14,12,31)
    rate_rows=rate.loc[rate[8].map(lambda v:isinstance(v,str) and bool(re.fullmatch(r'\d{2}',v.strip())))]
    if len(rate_rows)!=47 or rate.iloc[11,21]!='Both sexes' or 'All nationalities' not in str(rate.iloc[7].values):raise ValueError('Rate table scope changed')
    for _,r in rate_rows.iterrows():
        rid='JP-'+r[8]
        for col,age,lo,hi,label in columns:
            g=native[(native.region_id==rid)&(native.year==2022)]
            net=g.loc[g.age_group==age,'net_migration'].iloc[0] if age!='85+' else g.loc[g.age_lower.ge(85),'net_migration'].sum()
            denominator=pop.loc[(pop.region_id==rid)&(pop.year==2022)&(pop.age_group==age),'age_population'].iloc[0]
            actual=100*net/denominator;expected=float(r[col])
            checks.append(dict(check='2022 official same-age percentage: population and rate rounding compatibility',country='JPN',year=2022,region_id=rid,
                age_group=age,actual=actual,expected=expected,difference=actual-expected,
                **rounded_rate_check(net,denominator,expected)))
    quality=pd.DataFrame(checks)
    if not quality.passed.all():
        print(quality.loc[~quality.passed].to_string(index=False))
        raise ValueError('Source/accounting validation failed; no analytical files exported')
    coverage=[]
    for label,table in [('native',native),('harmonized',joined)]:
        for (country,year,age),g in table.groupby(['country','year','age_group']):
            for col in [*COUNTS,*(['age_population','net_per_1000_same_age','age65_share_pct','net_moe90'] if label=='harmonized' else [])]:
                coverage.append(dict(dataset=label,country=country,year=year,age_group=age,indicator=col,
                    eligible=47 if country=='JPN' else 51,rows=len(g),valid=int(g[col].notna().sum()),missing=int(g[col].isna().sum())))
    for name,frame in [('native_migration',native),('harmonized_migration',derived),
                       ('population_denominators',pd.concat([pop,dp],ignore_index=True)),('population_structure_join',joined),
                       ('acs_source_cells',pd.DataFrame(cells))]:csv_write(frame,out/'data'/f'{name}.csv')
    csv_write(pd.DataFrame(um+jm),out/'results/variable_mapping.csv')
    csv_write(quality,out/'results/source_checks.csv')
    csv_write(pd.DataFrame(coverage),out/'results/coverage.csv')
    csv_write(pd.DataFrame(structure),out/'data/acs_population_structure.csv')
    csv_write(pop.groupby(['country','region_id','year']).first().reset_index()[['country','region_id','year','population_total']].merge(
        canonical,on=['country','region_id','year'],validate='one_to_one').assign(
        total_difference=lambda d:d.population_total-d.canonical_population_total),out/'results/population_vintage_comparison.csv')
    summary=dict(native_rows=len(native),harmonized_rows=len(joined),region_years=len(joined[['country','region_id','year']].drop_duplicates()),
        source_checks=len(quality),source_checks_failed=0,unknown_age=native.loc[native.age_group=='unknown',KEY+COUNTS].to_dict('records'),
        source_bytes_verified=len(source.rows),primary_missing=int(joined.net_per_1000_same_age.isna().sum()),
        acs_api='data endpoint returned Missing Key; official public Summary File used; metadata JSON retrieved',
        us_moe='approximate 90% RSS difference and ratio, includes denominator MOE; covariances not supplied',
        japan2019_population_vintage='2019 annual release (2015 census base); canonical stock retains later intercensal vintage',
        japan2022_rate_verification='All 893 published cells compatible with nearest-1000 population and 0.01 percentage-point rate rounding; not exact reproduction of unpublished precision',
        japan2019_official_age_rate='NOT EVALUATED: retrieved annual index/summary do not provide a verified prefectural age-rate table; rates constructed from official counts and Table10 population',
        japan_age_day_convention='NOT EVALUATED: sources identify birth-date-derived registered age but do not explicitly state exact age-reference day')
    json_write(out/'results/preparation.json',summary)
    print(f'Prepared {len(native)} native rows, {len(joined)} harmonized rows; {len(quality)} source/accounting checks passed.')
    return joined


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    build(output=args.output)
