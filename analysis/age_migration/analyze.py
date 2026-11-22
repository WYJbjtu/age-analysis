"""Preplanned country-specific descriptive associations; no significance/causal claim."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from acquire import MODULE, json_write
from prepare import csv_write
from model import YEARS, ANALYSIS_AGES, correlation


def association(group, country, year, age, variant, x='net_per_1000_same_age', y='age65_share_pct', eligible=None):
    pearson,spearman,n=correlation(group,x,y)
    return dict(country=country,year=year,age_group=age,variant=variant,
        analysis_role='primary_question' if age in ('20-24','65+') else 'supporting_question',
        migration_variable=x,population_structure_variable=y,
        eligible=eligible if eligible is not None else len(group),sample_rows=len(group),included=n,missing=len(group)-n,
        excluded_by_sensitivity_rule=(eligible-len(group)) if eligible is not None else 0,
        pearson=pearson,spearman=spearman,weighting='equal regions',
        rate_denominator='same-age current residents' if x=='net_per_1000_same_age' else 'all-age current residents',
        member_ids=';'.join(sorted(group.dropna(subset=[x,y]).region_id)),
        uncertainty_note='point-estimate correlation; no survey, spatial or measurement-error inference' if country=='USA' else 'descriptive; registration and population-estimation error not modeled')


def run(module=MODULE,output=None):
    module=Path(module).resolve();out=Path(output).resolve() if output else module
    root=MODULE.parents[1]
    if out!=module and not out.is_relative_to(root/'data/cache'):raise ValueError('Output outside extension/cache')
    data=pd.read_csv(module/'data/population_structure_join.csv',encoding='utf-8')
    native=pd.read_csv(module/'data/native_migration.csv',encoding='utf-8')
    results,loo,influence,year_comparison=[],[],[],[]
    for country in ('JPN','USA'):
        expected=47 if country=='JPN' else 51
        special='JP-13' if country=='JPN' else 'US-DC'
        for age in ANALYSIS_AGES:
            full=data.loc[(data.country==country)&(data.age_group==age)]
            common=set.intersection(*(set(full.loc[full.year==y].dropna(subset=['age65_share_pct','net_per_1000_same_age']).region_id) for y in YEARS))
            if len(common)!=expected:raise ValueError('Preplanned common sample is incomplete; investigate')
            for year in YEARS:
                g=full[full.year==year]
                base=association(g,country,year,age,'primary',eligible=expected);results.append(base)
                results.append(association(g[g.region_id!=special],country,year,age,'without_Tokyo' if country=='JPN' else 'without_DC',eligible=expected))
                results.append(association(g[g.region_id.isin(common)],country,year,age,'common_regions_both_years',eligible=expected))
                results.append(association(g,country,year,age,'alternative_total_denominator',x='net_per_1000_total',eligible=expected))
                if country=='USA':results.append(association(g,country,year,age,'ACS_aging_outcome',y='acs_age65_share_pct',eligible=expected))
                checks=[]
                for omitted in sorted(g.region_id):
                    reduced=g[g.region_id!=omitted]
                    r=association(reduced,country,year,age,'leave_one_out',eligible=expected)
                    r.update(omitted_region=omitted,pearson_delta=r['pearson']-base['pearson'],spearman_delta=r['spearman']-base['spearman'])
                    loo.append(r);checks.append(r)
                checks=pd.DataFrame(checks)
                influential=checks.iloc[checks.pearson_delta.abs().argmax()]
                influence.append(dict(country=country,year=year,age_group=age,full_pearson=base['pearson'],full_spearman=base['spearman'],
                    loo_pearson_min=checks.pearson.min(),loo_pearson_max=checks.pearson.max(),
                    loo_spearman_min=checks.spearman.min(),loo_spearman_max=checks.spearman.max(),
                    most_influential_region=influential.omitted_region,max_absolute_pearson_change=abs(influential.pearson_delta),
                    pearson_sign_changes=int((np.sign(checks.pearson)!=np.sign(base['pearson'])).sum()),
                    spearman_sign_changes=int((np.sign(checks.spearman)!=np.sign(base['spearman'])).sum())))
            paired=full.pivot(index='region_id',columns='year',values='net_per_1000_same_age').loc[sorted(common)]
            r,s,n=correlation(paired,2019,2022)
            year_comparison.append(dict(country=country,age_group=age,common_regions=n,rate_2019_2022_pearson=r,
                rate_2019_2022_spearman=s,note='two annual snapshots; not cumulative migration or a cohort change'))
    associations=pd.DataFrame(results)
    if len(associations)!=54 or associations.missing.sum()!=0:raise ValueError('Planned comparison inventory changed')
    cases=[]
    us=data[(data.country=='USA')&(data.year==2022)&(data.age_group=='20-24')].sort_values(['net_per_1000_same_age','region_id'])
    for position,rule in [(0,'minimum'),(-1,'maximum')]:
        selected=us.iloc[position]
        for year in YEARS:
            row=data[(data.region_id==selected.region_id)&(data.year==year)&(data.age_group=='20-24')].iloc[0]
            cases.append(dict(country='USA',region_id=row.region_id,region_name=row.region_name,year=year,
                selection_rule=f'{rule} 2022 ages20-24 same-age net-rate point estimate among all51; tie by region_id; retained in2019',
                selection_year=2022,selection_sample=51,age_group='20-24',net_migration=row.net_migration,net_moe90=row.net_moe90,
                net_per_1000_same_age=row.net_per_1000_same_age,net_rate_moe90_approx=row.net_per_1000_same_age_moe90_approx,
                uncertainty_status=row.rate_direction_status,age65_share_pct=row.age65_share_pct))
    for year in YEARS:
        row=data[(data.region_id=='JP-13')&(data.year==year)&(data.age_group=='20-24')].iloc[0]
        cases.append(dict(country='JPN',region_id='JP-13',region_name='Tokyo',year=year,selection_rule='pre-specified Tokyo prefecture JP-13',
            selection_year=2022,selection_sample=47,age_group='20-24',net_migration=row.net_migration,
            net_per_1000_same_age=row.net_per_1000_same_age,age65_share_pct=row.age65_share_pct,uncertainty_status='registration counts; no sampling MOE'))
    tokyo=[]
    for year in YEARS:
        g=native[(native.region_id=='JP-13')&(native.year==year)].set_index('age_group')
        total=g.loc['total_all_ages','net_migration'];a=g.loc['15-19','net_migration'];b=g.loc['20-24','net_migration']
        old=g.loc[g.age_lower.ge(65),'net_migration'].sum()
        tokyo.append(dict(year=year,total_net=total,age15_19_net=a,age20_24_net=b,
            all_other_ages_net=total-a-b,age65plus_net=old,unknown_age_net=g.loc['unknown','net_migration']))
    tokyo=pd.DataFrame(tokyo)
    reference={'age15_19_net':13795,'age20_24_net':57153,'all_other_ages_net':-32925,'total_net':38023}
    checkpoints=[dict(check=key,year=2022,actual=float(tokyo.loc[tokyo.year==2022,key].iloc[0]),reference=value,
        difference=float(tokyo.loc[tokyo.year==2022,key].iloc[0])-value) for key,value in reference.items()]
    positive=data[(data.country=='JPN')&(data.year==2022)&(data.age_group=='20-24')&(data.net_migration>0)]
    positives=sorted(positive.region_id)
    expected=['JP-11','JP-13','JP-14','JP-23','JP-27']
    if any(r['difference']!=0 for r in checkpoints) or positives!=expected:
        raise ValueError('Tokyo/positive-prefecture checkpoint discrepancy: inspect definitions; do not force source values')
    uncertainty=[]
    selected_ids={row['region_id'] for row in cases}
    case_totals=native.loc[native.region_id.isin(selected_ids)&native.row_type.eq('published_total'),
        ['country','region_id','region_name','year','age_group','net_migration','net_moe90','uncertainty_status']].copy()
    case_totals['net_interval_low90_approx']=case_totals.net_migration-case_totals.net_moe90
    case_totals['net_interval_high90_approx']=case_totals.net_migration+case_totals.net_moe90
    for (year,age),g in data[data.country=='USA'].groupby(['year','age_group']):
        uncertainty.append(dict(country='USA',year=year,age_group=age,n=len(g),
            positive_points=int(g.net_migration.gt(0).sum()),negative_points=int(g.net_migration.lt(0).sum()),
            positive_approx_intervals=int(g.rate_direction_status.eq('positive_under_approximation').sum()),
            negative_approx_intervals=int(g.rate_direction_status.eq('negative_under_approximation').sum()),
            intervals_including_zero=int(g.rate_direction_status.eq('interval_includes_zero').sum()),
            missing_interval=int(g.net_per_1000_same_age_moe90_approx.isna().sum())))
    for name,frame in [('associations',associations),('leave_one_out',pd.DataFrame(loo)),('influence_summary',pd.DataFrame(influence)),
        ('year_comparison',pd.DataFrame(year_comparison)),('case_selection',pd.DataFrame(cases)),('case_totals',case_totals),('tokyo_decomposition',tokyo),
        ('reference_checkpoints',pd.DataFrame(checkpoints)),('us_uncertainty_summary',pd.DataFrame(uncertainty)),
        ('japan2022_positive20_24',positive[['region_id','region_name','net_migration','net_per_1000_same_age']])]:
        csv_write(frame,out/'results'/f'{name}.csv')
    json_write(out/'results/analysis_summary.json',dict(planned_associations=len(associations),full_sample_same_age_associations=12,
        primary_associations=8,supporting_associations=4,
        leave_one_out_runs=len(loo),countries_separate=True,ordinary_p_values='not calculated',
        primary_weighting='equal regions',canonical_population='read-only Member1',tokyo_checkpoint_match=True,
        japan2022_positive20_24=positives,case_rule='pre-specified Tokyo; US 2022 young-rate minimum and maximum point estimates',
        scope='READY WITH LIMITATIONS; descriptive associations only; Japan exact age-reference day not independently verified'))
    print(associations[associations.variant=='primary'][['country','year','age_group','included','pearson','spearman']].to_string(index=False))
    return associations


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();run(output=args.output)
