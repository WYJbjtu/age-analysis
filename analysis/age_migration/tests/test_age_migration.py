"""Regression tests for the actual definitions, accounting and uncertainty failure modes."""
from pathlib import Path
import copy
import json
import math
import numpy as np
import pandas as pd
import pytest
from acquire import MODULE, checked_url, validate_payload, digest
from prepare import Sources, us_mapping, us_table, jp_count_table, harmonize
from model import (SENTINELS, KEY, COUNTS, PROFILE, GROUPS, acs_value, covered_bins,
    ratio_moe90, rss, direction, rounded_rate_check, validate_flows, validate_regions, safe_join, correlation)

ROOT=MODULE.parents[1]


def test_acs_sentinels_annotations_and_real_negative_net():
    for sentinel,(symbol,reason) in SENTINELS.items():
        for raw in (str(sentinel),symbol):
            value,annotation,status=acs_value(raw,moe=True)
            assert math.isnan(value) and annotation==symbol and status==reason
        assert math.isnan(acs_value('123',symbol)[0])
    assert math.isnan(acs_value('')[0])
    with pytest.raises(ValueError):acs_value('-42')
    with pytest.raises(ValueError):acs_value('100','unrecognized')
    f=pd.DataFrame({'in_migration':[3],'out_migration':[9],'net_migration':[-6]})
    validate_flows(f)
    f.loc[0,'net_migration']=6
    with pytest.raises(ValueError):validate_flows(f)


def test_uncertainty_includes_denominator_and_preserves_missing():
    # Isolated arithmetic fixture, never used for formal observations.
    fixed=1000*5/100
    result=ratio_moe90(-20,100,5,10)
    assert result==pytest.approx(10*math.sqrt(25+4)) and result>fixed
    assert math.isnan(ratio_moe90(20,100,5,np.nan))
    assert math.isnan(rss([4,np.nan]))
    assert rss([3,4])==5
    with pytest.raises(ValueError):ratio_moe90(1,0,2,3)
    assert direction(-1,2)=='interval_includes_zero'
    assert direction(-5,2)=='negative_under_approximation'
    assert direction(1,np.nan)=='no_sampling_interval'


def test_exact_age_aggregation_rejects_overlap_gaps_and_partial_bins():
    frame=pd.DataFrame({'age_lower':[18,20,25,30,35,65], 'age_upper':[19,24,29,34,64,np.nan]})
    assert len(covered_bins(frame,20,34))==3
    assert len(covered_bins(frame,65,None))==1
    for wrong in (frame.drop(index=2),pd.concat([frame,frame.iloc[[2]]])):
        with pytest.raises(ValueError):covered_bins(wrong,20,34)
    with pytest.raises(ValueError):covered_bins(frame,15,24)
    with pytest.raises(ValueError):covered_bins(frame,21,24)
    assert PROFILE==['20-24','25-29','30-34','35-64','65+']
    assert '20-34' not in PROFILE


def test_rate_rounding_intervals_have_a_documented_bound():
    assert rounded_rate_check(-2488,45000,-5.55)['passed']
    assert not rounded_rate_check(-2488,45000,-5.80)['passed']
    assert rounded_rate_check(100,10000,1.0)['passed']
    assert rounded_rate_check(0,10000,0)['passed']
    with pytest.raises(ValueError):rounded_rate_check(1,400,.1)


def test_verified_metadata_mapping_does_not_guess_column_offsets():
    source=Sources()
    for year in (2019,2022):
        for table,role in [('B07001','in'),('B07401','out'),('B07001','age_population')]:
            meta=json.loads(source.path(f'acs{year}_{table}_metadata',year).read_text(encoding='utf-8'))['variables']
            mapped=us_mapping(meta,table,role)
            assert len(mapped)==16
            assert {r['age_group'] for r in mapped}>={'1-4','5-17','18-19','20-24','75+','total_1plus'}
            assert all('different state' in r['source_label'].lower() for r in mapped) if role!='age_population' else True
            if role=='in':
                altered=copy.deepcopy(meta)
                key=next(r['variable'] for r in mapped if r['age_group']=='20-24')
                altered[key]['label']=altered[key]['label'].replace('Moved from different state','Moved from abroad')
                with pytest.raises(ValueError):us_mapping(altered,table,role)
        with pytest.raises(ValueError):source.path(f'acs{year}_B07001_summary',2019 if year==2022 else 2022)
    with pytest.raises(ValueError):us_table(source,2020,'B07001')
    with pytest.raises(ValueError):us_mapping({},'B07401','age_population')


def test_raw_sources_are_pinned_and_cannot_hide_html_or_credentials(tmp_path):
    source=Sources()
    for row in source.rows.values():
        assert digest(source.path(row['id']).read_bytes())==row['sha256']
    with pytest.raises(ValueError):validate_payload(b'<html>Missing Key</html>','json','text/html')
    for url in ['https://api.census.gov/data/2022?key=secret','https://example.org/file.csv','file:///etc/passwd']:
        with pytest.raises(ValueError):checked_url(url)
    fake=tmp_path/'sources';(fake/'raw').mkdir(parents=True)
    (fake/'raw/a.dat').write_bytes(b'changed')
    (fake/'manifest.json').write_text(json.dumps([{'id':'a','file':'a.dat','sha256':digest(b'original')}]),encoding='utf-8',newline='\n')
    with pytest.raises(ValueError):Sources(tmp_path)


def test_japan_official_gross_and_net_files_reproduce_all_prefectures(tables):
    source=Sources();native=tables['native_migration']
    for year in (2019,2022):
        for role,col in zip(('in','out','net'),COUNTS):
            values,columns,checks=jp_count_table(source,year,role)
            assert len({k[0] for k in values})==47 and all(c['passed'] for c in checks)
            subset=native[(native.country=='JPN')&(native.year==year)&native.age_group.ne('unknown')]
            for row in subset.itertuples():assert getattr(row,col)==values[row.region_id,row.age_group]
    assert set(native.loc[native.region_id=='JP-05','year'])=={2019,2022}  # Akita retained


def test_actual_nonmissing_coverage_unique_keys_and_join_safety(tables):
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv',encoding='utf-8')
    for name in ('native_migration','harmonized_migration','population_structure_join'):
        f=tables[name];validate_regions(f,lookup);validate_flows(f)
        assert not f[COUNTS].isna().any().any()
    joined=tables['population_structure_join']
    assert len(joined)==196*6 and joined[['age_population','age65_share_pct','net_per_1000_same_age']].notna().all().all()
    assert (joined.age_population>0).all()
    with pytest.raises(ValueError):validate_regions(joined[joined.region_id!='JP-05'],lookup)
    with pytest.raises(ValueError):validate_regions(pd.concat([joined,joined.iloc[[0]]]),lookup)
    left=joined[['country','region_id','year']].drop_duplicates()
    right=left.assign(value=1)
    assert len(safe_join(left,right,list(left)))==196
    with pytest.raises(ValueError):safe_join(left,right.iloc[1:],list(left))
    with pytest.raises(ValueError):safe_join(left,pd.concat([right,right.iloc[[0]]]),list(left))


def test_native_sums_unknown_and_country_balance(tables):
    native=tables['native_migration']
    for key,g in native.groupby(['country','region_id','year']):
        total=g[g.row_type=='published_total'].iloc[0]
        components=g[g.row_type!='published_total']
        assert np.array_equal(components[COUNTS].sum().to_numpy(),total[COUNTS].to_numpy())
        assert len(components)==(20 if key[0]=='JPN' else 15)
    assert (native.groupby(['country','year','age_group']).net_migration.sum()==0).all()
    unknown=native[native.age_group=='unknown']
    assert len(unknown)==94 and unknown[COUNTS].abs().sum().sum()>0
    old=pd.read_csv(ROOT/'data/processed/labor_migration.csv',encoding='utf-8')[['country','region_id','year','domestic_net_migration']]
    jp=native[(native.country=='JPN')&(native.row_type=='published_total')].merge(old,on=['country','region_id','year'],validate='one_to_one')
    assert len(jp)==94 and (jp.net_migration==jp.domestic_net_migration).all()


def test_harmonized_aggregates_are_exact_and_denominators_same_age(tables):
    native=tables['native_migration'];pop=tables['population_denominators']
    actual,den=harmonize(native,pop[pop.age_scheme=='native'])
    expected=tables['harmonized_migration']
    cols=KEY+COUNTS+['in_moe90','out_moe90','net_moe90']
    pd.testing.assert_frame_equal(actual[cols].sort_values(KEY).reset_index(drop=True),expected[cols].sort_values(KEY).reset_index(drop=True),check_dtype=False,rtol=1e-12)
    assert den.age_population.gt(0).all()
    uspop=pop[(pop.country=='USA')&(pop.age_group=='total_1plus')]
    assert (uspop.age_population<uspop.population_total).all()  # no ages1+ as all-age total
    joined=tables['population_structure_join']
    np.testing.assert_allclose(joined.net_per_1000_same_age,1000*joined.net_migration/joined.age_population,rtol=1e-12)
    np.testing.assert_allclose(joined.net_per_1000_total,1000*joined.net_migration/joined.population_total,rtol=1e-12)


def test_moe_annotations_remain_distinct_from_zero_uncertainty(tables):
    cells=tables['acs_source_cells'];data=tables['population_structure_join']
    controlled=cells[cells.moe_status=='controlled_estimate_moe_not_applicable']
    assert len(controlled)>0 and controlled.moe90.isna().all() and controlled.moe_annotation.eq('*****').all()
    us=data[data.country=='USA'];jp=data[data.country=='JPN']
    assert us.net_moe90.gt(0).all() and us.net_per_1000_same_age_moe90_approx.gt(0).all()
    assert us.net_per_1000_total_moe90_approx.isna().all()
    assert jp[['in_moe90','out_moe90','net_moe90']].isna().all().all()
    assert us.rate_direction_status.eq('interval_includes_zero').any()


def test_full_preplanned_results_cases_and_recomputed_correlations(tables):
    results=pd.read_csv(MODULE/'results/associations.csv',encoding='utf-8')
    data=tables['population_structure_join']
    assert len(results)==54 and results.missing.sum()==0 and set(results.country)=={'JPN','USA'}
    assert not results.duplicated(['country','year','age_group','variant']).any()
    primary=results[results.variant=='primary']
    assert len(primary)==12
    for r in primary.itertuples():
        g=data[(data.country==r.country)&(data.year==r.year)&(data.age_group==r.age_group)]
        p,s,n=correlation(g,r.migration_variable,r.population_structure_variable)
        assert p==pytest.approx(r.pearson,abs=1e-12) and s==pytest.approx(r.spearman,abs=1e-12) and n==r.included
    loo=pd.read_csv(MODULE/'results/leave_one_out.csv',encoding='utf-8')
    assert len(loo)==588 and not loo.duplicated(['country','year','age_group','omitted_region']).any()
    cases=pd.read_csv(MODULE/'results/case_selection.csv',encoding='utf-8')
    eligible=data[(data.country=='USA')&(data.year==2022)&(data.age_group=='20-24')].sort_values(['net_per_1000_same_age','region_id'])
    assert set(cases.loc[cases.country=='USA','region_id'])=={eligible.iloc[0].region_id,eligible.iloc[-1].region_id}
    assert cases.groupby('region_id').year.nunique().eq(2).all()
    totals=pd.read_csv(MODULE/'results/case_totals.csv',encoding='utf-8')
    assert len(totals)==6
    total_us=totals[totals.country=='USA']
    assert total_us.net_moe90.gt(0).all()
    np.testing.assert_allclose(total_us.net_interval_low90_approx,total_us.net_migration-total_us.net_moe90,rtol=1e-12)
    np.testing.assert_allclose(total_us.net_interval_high90_approx,total_us.net_migration+total_us.net_moe90,rtol=1e-12)
    checkpoints=pd.read_csv(MODULE/'results/reference_checkpoints.csv',encoding='utf-8')
    assert checkpoints.difference.eq(0).all()


def test_generators_have_no_unguarded_acquisition_or_execution():
    import ast
    # Import-time calls may define constants, never invoke data acquisition or builders.
    for filename in ('acquire.py','prepare.py','analyze.py','model.py'):
        tree=ast.parse((MODULE/filename).read_text(encoding='utf-8'))
        for stmt in tree.body:
            if isinstance(stmt,(ast.FunctionDef,ast.ClassDef,ast.If)):continue
            for node in ast.walk(stmt):
                if isinstance(node,ast.Call):
                    name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                    assert name not in {'acquire','fetch_one','build','run','write_text','write_bytes','open','urlopen','system','Popen'}


def test_portable_representation_preserves_raw_bytes_and_rejects_path_escape(tmp_path):
    from verify_extension import represented,safe_relative
    p=tmp_path/'example.txt'
    p.write_bytes('年齢\r\n2019\r\n'.encode('utf-8'))
    assert represented(p,'utf8-lf')=='年齢\n2019\n'.encode('utf-8')
    assert represented(p,'bytes')==p.read_bytes()
    before=digest(represented(p,'utf8-lf'))
    p.write_bytes('年齢\n2022\n'.encode('utf-8'))
    assert digest(represented(p,'utf8-lf'))!=before
    p.write_bytes(b'bad\rline')
    with pytest.raises(ValueError):represented(p,'utf8-lf')
    p.write_bytes(b'\xff')
    with pytest.raises(UnicodeDecodeError):represented(p,'utf8-lf')
    for name in ('../outside','/absolute','C:/outside','a\\b'):
        with pytest.raises(ValueError):safe_relative(name)
