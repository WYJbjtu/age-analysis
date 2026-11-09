"""Offline Member 4 validation, integration, descriptive analysis and figure entry point."""
from pathlib import Path
import argparse, hashlib, itertools, json, platform, sys
from importlib.metadata import version
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from aging_economies.contracts import read_lookup
from aging_economies.comparability import require_comparable_pool
from descriptive import summarize,decomposition,classify
from freeze_inputs import main as protect
KEY=['country','region_id','year'];X='age65_share_pct';Y='manufacturing_share_pct'

def save(frame,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(path,index=False,float_format='%.10f',lineterminator='\n')

def validate(frame,lookup,label):
    if frame.duplicated(KEY).any(): raise ValueError(f'{label}: duplicate keys')
    if frame[KEY].isna().any().any(): raise ValueError(f'{label}: missing key')
    if not frame.year.between(1950,2050).all() or not (frame.year%1==0).all(): raise ValueError('Invalid year')
    for r in frame[['country','region_id']].itertuples(index=False):
        if lookup.get(r.region_id)!=r.country: raise ValueError(f'{label}: invalid region {r.region_id}')
    for c in frame.select_dtypes(include='number').columns:
        v=frame[c].dropna()
        if not np.isfinite(v).all(): raise ValueError(f'{label}: non-finite {c}')
        if c.endswith('_pct') and not v.between(0,100).all(): raise ValueError(f'{label}: share out of range')
    for c in ['total_population','nominal_gdp_local']:
        if c in frame and (frame[c].dropna()<=0).any(): raise ValueError(f'{label}: non-positive denominator')
    for c in ['employment','manufacturing_va_local','services_va_local']:
        if c in frame and (frame[c].dropna()<0).any(): raise ValueError(f'{label}: negative {c}')
    if 'nominal_gdp_local' in frame:
        for field in ['manufacturing','services']:
            if not np.allclose(frame[f'{field}_share_pct'],100*frame[f'{field}_va_local']/frame.nominal_gdp_local,atol=1e-7,rtol=0,equal_nan=True):
                raise ValueError(f'{label}: nominal share mismatch')
        expected=np.where(frame.country=='JPN','FY','CY')+frame.year.astype(str)
        if not (frame.gdp_reference_period==expected).all(): raise ValueError('GDP period mismatch')

def merge_inputs(dem,ind,labor,lookup):
    for label,f in [('demographics',dem),('industry',ind),('labor',labor)]: validate(f,lookup,label)
    merged=dem.merge(ind,on=KEY,how='outer',validate='one_to_one',indicator='population_industry_match')
    return merged.merge(labor,on=KEY,how='left',validate='one_to_one',indicator='labor_match').sort_values(KEY).reset_index(drop=True)

def main(out=None,figures=True):
    protect()
    if out is None:
        out=ROOT/'data/cache/remediation/current_member4' if (ROOT/'docs/remediation/prechange_manifest.json').exists() else HERE
    out=Path(out).resolve()
    if (ROOT/'docs/remediation/prechange_manifest.json').exists() and not out.is_relative_to(ROOT/'data/cache'):
        raise ValueError('Remediation reruns must use data/cache to preserve historical Member4 artifacts')
    # Core source gates are scoped to the analytical years and variables.
    source_checks=pd.read_csv(HERE/'audit/source_record_checks.csv')
    audited=source_checks.loc[source_checks.year.isin([2019,2022]) & source_checks.field.isin([X,Y])]
    if (audited.status!='PASS').any(): raise ValueError('Core official-source check failed')
    actual={(r.country,r.region_id,int(r.year),r.field) for r in audited.itertuples()}
    lookup=read_lookup(ROOT/'data/reference/region_lookup.csv')
    expected={(country,rid,year,field) for rid,country in lookup.items() for year in [2019,2022] for field in [X,Y]}
    if actual!=expected: raise ValueError('Core official-source checks incomplete')
    dem=pd.read_csv(ROOT/'data/processed/demographics.csv');ind=pd.read_csv(ROOT/'data/processed/industry.csv');lab=pd.read_csv(ROOT/'data/processed/labor_migration.csv')
    frame=merge_inputs(dem,ind,lab,lookup)
    detail=pd.read_csv(ROOT/'member1_demographics/population_detail_2011_2022.csv')
    metadata=[c for c in detail if c not in frame or c in KEY]
    frame=frame.merge(detail[metadata],on=KEY,how='left',validate='one_to_one')
    frame['industry_source_id']=np.where(frame.country=='USA','BEA SAGDP2 September 30 2026','CAO FY2011-FY2022 2008SNA 2015 benchmark')
    frame['industry_amount_unit']=np.where(frame.country=='USA','million current USD','million current JPY')
    frame['services_definition']=np.where(frame.country=='USA','private services including utilities; excludes government','published tertiary aggregate including public services')
    frame['labor_population']=np.where(frame.country=='USA','civilian noninstitutional 16+','LFS 15+')
    frame['labor_period']='calendar-year annual average; not seasonally adjusted annual series'
    if 'labor_reproduction_status' in frame:
        frame['labor_verification']=frame.labor_reproduction_status
    else:
        frame['labor_verification']=np.where(frame.country=='JPN','all records verified to retrieved LFS workbook',np.where(frame.year.isin([2019,2022]),'sample verified: 6 of 51 regions per year','provenance supplied; not independently verified'))
    if 'migration_original_definition' not in frame:
        frame['migration_original_definition']=np.where(frame.country=='USA','total domestic plus international; July-to-July',np.where(frame.year<=2017,'domestic; Japanese nationals only','domestic; all nationalities (2019/2022 verified)'))
    frame['population_verification']='all regional records verified to pinned official sources'
    domestic=pd.read_csv(HERE/'audit/verified_domestic_migration.csv')
    if 'domestic_net_migration' in frame:
        comparison=domestic[KEY+['domestic_net_migration']].merge(frame[KEY+['domestic_net_migration']],on=KEY,validate='one_to_one',suffixes=('_audit','_owner'))
        if len(comparison)!=196 or not comparison.domestic_net_migration_audit.eq(comparison.domestic_net_migration_owner).all():
            raise ValueError('Repaired owner domestic migration differs from the independent historical adapter')
        frame['migration_reference_period']=frame.migration_start_date+' to '+frame.migration_end_date
        frame['migration_source']=frame.migration_source_file
    else:
        frame=frame.merge(domestic,on=KEY,how='left',validate='one_to_one').sort_values(KEY)
    frame['core_eligible']=frame[[X,Y]].notna().all(axis=1)&frame.population_industry_match.eq('both')
    save(frame,out/'data/integrated_context_panel.csv')
    # Flow and exclusion records are explicit even when the primary sample is complete.
    flows=[];exclusions=[];missing=[];joins=[]
    for year in sorted(frame.year.unique()):
        for country in ['USA','JPN']:
            g=frame[(frame.year==year)&(frame.country==country)];n=sum(c==country for c in lookup.values())
            valid_dem=dem[(dem.year==year)&(dem.country==country)&dem[X].notna()]
            valid_ind=ind[(ind.year==year)&(ind.country==country)&ind[Y].notna()]
            flows.append(dict(country=country,year=year,expected_regions=n,valid_population=len(valid_dem),valid_industry=len(valid_ind),matched_core=int(g.core_eligible.sum()),primary_analysis=int(g.core_eligible.sum()) if year in [2019,2022] else 0))
            for match,count in g.population_industry_match.value_counts().items(): joins.append(dict(country=country,year=year,match=match,n=int(count)))
            for field in [X,Y,'employment','unemployment_rate_pct','net_migration','domestic_net_migration']:
                missing.append(dict(country=country,year=year,field=field,n=len(g),missing=int(g[field].isna().sum())))
            for rid in sorted(rid for rid,c in lookup.items() if c==country):
                row=g.loc[g.region_id==rid]
                if row.empty: reason='region-year absent from both core inputs'
                elif row.iloc[0].core_eligible: continue
                else: reason='; '.join(c+' missing' for c in [X,Y] if pd.isna(row.iloc[0][c]))
                exclusions.append(dict(country=country,region_id=rid,year=year,analysis='core',reason=reason))
    save(pd.DataFrame(flows),out/'audit/sample_flow.csv');save(pd.DataFrame(joins),out/'audit/join_coverage.csv');save(pd.DataFrame(missing),out/'audit/missingness.csv')
    save(pd.DataFrame(exclusions,columns=KEY+['analysis','reason']),out/'audit/exclusions.csv')
    results=[];loo=[];decomp_rows=[];decomp_summary=[];support=[];ledger=[];analysis_samples=[]
    core=frame.loc[frame.core_eligible]
    common=set(core.loc[core.year==2019,'region_id']) & set(core.loc[core.year==2022,'region_id'])
    def record(g,year,group,variant,x=X,y=Y,weight=None):
        require_comparable_pool(g,[x,y])
        s=summarize(g,x,y,weight)
        row=dict(year=year,group=group,variant=variant,x=x,y=y,**s)
        results.append(row)
        ledger.append(dict(analysis_id=f'{year}_{group}_{variant}_{y}',year=year,group=group,variant=variant,x=x,y=y,n=s['n'],weighting=s['weighting'],purpose='primary/sensitivity' if y==Y else 'optional descriptive context',limitation='CY/FY and regional scale differences; no causal interpretation' if y==Y else 'within-country only; definitions and source verification vary'))
        cols=[x,y]+([weight] if weight else [])
        for r in g.itertuples():
            use=all(pd.notna(getattr(r,c)) for c in cols)
            analysis_samples.append(dict(analysis_id=ledger[-1]['analysis_id'],country=r.country,region_id=r.region_id,year=year,included=use,reason='' if use else 'missing '+','.join(c for c in cols if pd.isna(getattr(r,c)))))
        return row
    for year in [2019,2022]:
        d=core.loc[core.year==year].copy();save(d,out/f'data/core_{year}.csv')
        for group,g in [('Pooled',d),('USA',d[d.country=='USA']),('JPN',d[d.country=='JPN'])]:
            record(g,year,group,'available')
            record(g[g.region_id.isin(common)],year,group,'common_regions')
            record(g,year,group,'population_weighted',weight='total_population')
            if group in ['Pooled','USA']: record(g[g.region_id!='US-DC'],year,group,'without_DC')
            for r in g.itertuples():
                stats=summarize(g[g.region_id!=r.region_id],X,Y)
                loo.append(dict(year=year,group=group,omitted=r.region_id,**stats))
        parts,total,adjusted=decomposition(d,X,Y)
        decomp_rows.extend(dict(year=year,**r) for r in parts)
        base=[r for r in results if r['year']==year and r['variant']=='available' and r['y']==Y]
        vals={r['group']:r['pearson'] for r in base}
        ranks={r['group']:r['spearman'] for r in base}
        total.update(year=year,classification_method='Pearson',classification=classify(vals['Pooled'],[vals['USA'],vals['JPN']]),
                     spearman_classification=classify(ranks['Pooled'],[ranks['USA'],ranks['JPN']]))
        decomp_summary.append(total)
        results.append(dict(year=year,group='Country-demeaned',variant='country_adjusted',x=X,y=Y,**adjusted))
        ledger.append(dict(analysis_id=f'{year}_country_adjusted',year=year,group='Country-demeaned',variant='country_adjusted',x=X,y=Y,n=len(d),weighting='equal regions',purpose='additive country-mean adjustment',limitation='not all confounding; not common-slope evidence; no causal identification'))
        for r in d.itertuples(): analysis_samples.append(dict(analysis_id=f'{year}_country_adjusted',country=r.country,region_id=r.region_id,year=year,included=True,reason=''))
        for variable in [X,Y]:
            ranges=d.groupby('country')[variable].agg(['min','max'])
            lo=ranges['min'].max();hi=ranges['max'].min()
            support.append(dict(year=year,variable=variable,USA_min=ranges.loc['USA','min'],USA_max=ranges.loc['USA','max'],JPN_min=ranges.loc['JPN','min'],JPN_max=ranges.loc['JPN','max'],overlap_min=lo if lo<=hi else np.nan,overlap_max=hi if lo<=hi else np.nan,gap_if_disjoint=max(0,lo-hi)))
        for country,g in d.groupby('country'):
            for y in ['services_share_pct','unemployment_rate_pct','domestic_net_migration']:
                record(g,year,country,'within_country_context',y=y)
    # Changes: one observation per region, 2019 to 2022, never all region-years pooled.
    a=core[core.year==2019][['country','region_id',X,Y]];b=core[core.year==2022][['country','region_id',X,Y]]
    changes=a.merge(b,on=['country','region_id'],validate='one_to_one',suffixes=('_2019','_2022'))
    for v in [X,Y]: changes[v+'_change_pp']=changes[v+'_2022']-changes[v+'_2019']
    save(changes,out/'data/changes_2019_2022.csv')
    change_results=[]
    for country,g in changes.groupby('country'):
        s=summarize(g,X+'_change_pp',Y+'_change_pp');change_results.append(dict(group=country,period='2019 to 2022',**s))
        ledger.append(dict(analysis_id=f'change_{country}',year='2019-2022',group=country,variant='endpoint_change',x=X+'_change_pp',y=Y+'_change_pp',n=s['n'],weighting='equal regions',purpose='limited longitudinal sensitivity',limitation='Census benchmark/release changes; nominal price changes; no causal inference'))
        for r in g.itertuples(): analysis_samples.append(dict(analysis_id=f'change_{country}',country=r.country,region_id=r.region_id,year='2019-2022',included=True,reason=''))
    save(pd.DataFrame(change_results),out/'results/change_associations.csv')
    save(pd.DataFrame(results),out/'results/associations.csv');save(pd.DataFrame(loo),out/'results/leave_one_out.csv')
    save(pd.DataFrame(decomp_rows),out/'results/covariance_components.csv');save(pd.DataFrame(decomp_summary),out/'results/covariance_summary.csv')
    save(pd.DataFrame(support),out/'results/overlap.csv');save(pd.DataFrame(ledger),out/'results/analysis_ledger.csv')
    save(pd.DataFrame(analysis_samples),out/'data/analysis_samples.csv')
    l=pd.DataFrame(loo);ls=l.groupby(['year','group'],as_index=False).agg(pearson_min=('pearson','min'),pearson_max=('pearson','max'),spearman_min=('spearman','min'),spearman_max=('spearman','max'),slope_min=('slope','min'),slope_max=('slope','max'),positive=('pearson',lambda x:int((x>0).sum())),negative=('pearson',lambda x:int((x<0).sum())))
    save(ls,out/'results/influence_summary.csv')
    # Transparent contrast selection from all eligible pairs, without labor-driven cherry picking.
    pairs=[];selected=[];d=core[core.year==2022]
    for country,g in d.groupby('country'):
        for a,b in itertools.combinations(g.sort_values('region_id').itertuples(),2):
            gap=abs(getattr(a,X)-getattr(b,X))
            if gap<=.5:
                pairs.append(dict(country=country,region_a=a.region_id,region_b=b.region_id,aging_gap_pp=gap,manufacturing_gap_pp=abs(getattr(a,Y)-getattr(b,Y))))
        candidates=sorted([r for r in pairs if r['country']==country],key=lambda r:(r['manufacturing_gap_pp'],r['region_a'],r['region_b']))
        for role,p in [('smallest industry gap',candidates[0]),('largest industry gap',candidates[-1])]:
            for rid in [p['region_a'],p['region_b']]:
                r=d.loc[d.region_id==rid].iloc[0].to_dict();r.update(selection=role,pair=f"{p['region_a']} / {p['region_b']}",aging_gap_pp=p['aging_gap_pp'],manufacturing_gap_pp=p['manufacturing_gap_pp']);selected.append(r)
    save(pd.DataFrame(pairs),out/'results/case_candidate_pairs.csv');save(pd.DataFrame(selected),out/'results/selected_cases.csv')
    # Numerical findings digest for report/figure consistency.
    main_results=pd.DataFrame(results).query("variant=='available' and y==@Y")
    save(main_results,out/'results/primary_summary.csv')
    if figures:
        from plot_figures import make_figures
        make_figures(out)
    environment={'python':platform.python_version(),'platform':platform.platform()}
    environment.update({package:version(package) for package in ['pandas','numpy','matplotlib','openpyxl','xlrd','pytest']})
    (out/'audit/environment.json').write_text(json.dumps(environment,indent=2)+'\n',encoding='utf-8')
    protect()
    print(main_results[['year','group','n','pearson','spearman','slope']].to_string(index=False))
    print(pd.DataFrame(decomp_summary).to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path);p.add_argument('--no-figures',action='store_true');args=p.parse_args();main(args.output_dir,not args.no_figures)
