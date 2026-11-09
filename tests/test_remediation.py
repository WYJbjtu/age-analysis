"""Regression tests for the repaired scientific/source failure modes; offline only."""
from pathlib import Path
import csv,hashlib,importlib.util,json,sys
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'member3_labor_migration'),str(ROOT/'scripts'),str(ROOT/'analysis/member4')]
from bls_sources import load_archives,parse_annual_table,parse_m13
from labor_validation import validate_labor_counts,validate_panel,require_same_migration_coverage
from aging_economies.comparability import require_comparable_pool,annotate_periods
from aging_economies.source_io import acquire,official_url
from descriptive import summarize,decomposition


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value);return value


@pytest.fixture(scope='module')
def labor():return pd.read_csv(ROOT/'data/processed/labor_migration.csv')


def test_domestic_source_components_and_independent_reference(labor):
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv');validate_panel(labor,lookup)
    us=labor.query("country=='USA'")
    assert len(us)==612 and us.domestic_net_migration.notna().all()
    assert us.net_migration.eq(us.total_net_migration).all()
    assert us.total_net_migration.eq(us.domestic_net_migration+us.international_net_migration).all()
    assert (us.total_net_migration!=us.domestic_net_migration).any()
    ref=pd.read_csv(ROOT/'analysis/member4/audit/verified_domestic_migration.csv')
    pairs=ref.merge(labor,on=['country','region_id','year'],validate='one_to_one',suffixes=('_audit','_owner'))
    assert len(pairs)==196
    assert pairs.domestic_net_migration_audit.eq(pairs.domestic_net_migration_owner).all()
    assert us.migration_start_date.eq((us.year-1).astype(str)+'-07-01').all()
    assert us.migration_end_date.eq(us.year.astype(str)+'-07-01').all()


def test_japanese_nationality_break_is_not_spliced_or_filled(labor):
    jp=labor.query("country=='JPN'")
    early=jp[jp.year<2018];late=jp[jp.year>=2018]
    assert len(early)==329 and early.domestic_net_migration.isna().all()
    assert early.japanese_only_domestic_net_migration.notna().all()
    assert len(late)==235 and late.domestic_net_migration.notna().all()
    assert late.japanese_only_domestic_net_migration.isna().all()
    assert jp.international_net_migration.isna().all() and jp.total_net_migration.isna().all()
    with pytest.raises(ValueError,match='Split migration series'):require_same_migration_coverage(jp,'net_migration')
    assert len(require_same_migration_coverage(jp))==235
    incomplete=late.copy();incomplete.loc[incomplete.index[0],'migration_population']=np.nan
    with pytest.raises(ValueError,match='labels are required'):require_same_migration_coverage(incomplete)
    contaminated=labor.copy();contaminated.loc[early.index[0],'domestic_net_migration']=early.iloc[0].net_migration
    with pytest.raises(ValueError,match='Japanese-only'):validate_panel(contaminated,pd.read_csv(ROOT/'data/reference/region_lookup.csv'))


def test_bls_complete_official_archives_rebuild_all_labor_years(labor):
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv')
    current,prior,evidence=load_archives(ROOT/'data/raw/member3',ROOT/'member3_labor_migration/source_snapshots',lookup)
    assert len(current)==612 and len(prior)==612 and len(evidence)==12
    fields=['country','region_id','year','employment','unemployment_rate_pct','labor_force','unemployment']
    pd.testing.assert_frame_equal(current[fields].sort_values(fields[:3]).reset_index(drop=True),
        labor.query("country=='USA'")[fields].sort_values(fields[:3]).reset_index(drop=True),check_dtype=False,check_exact=True)
    for year in range(2011,2023):assert len(current[current.year==year])==51
    assert current.loc[current.year==2022,'employment_population_ratio_pct'].notna().sum()==51
    assert current.loc[current.year<2022,'employment_population_ratio_pct'].isna().all()
    detail=current.query('year==2022')
    low=100*(detail.employment-500)/(detail.civilian_population_16plus+500)
    high=100*(detail.employment+500)/(detail.civilian_population_16plus-500)
    assert ((detail.employment_population_ratio_pct+.05>=low)&(detail.employment_population_ratio_pct-.05<=high)).all()


def test_bls_parser_rejects_truncated_source_table():
    names=pd.read_csv(ROOT/'data/reference/region_lookup.csv').query("country=='USA'").set_index('region_name').region_id.to_dict()
    text=(ROOT/'member3_labor_migration/source_snapshots/bls_2022_web.txt').read_text(encoding='utf-8')
    # Synthetic source defect stays in this test fixture; formal sources are untouched.
    partial='\n'.join(line for line in text.splitlines() if not ('L667:' in line))
    with pytest.raises(ValueError,match='expected 51'):parse_annual_table(partial,2022,names)


def test_bls_snapshot_read_has_explicit_encoding_in_non_utf8_mode():
    """Catch an omitted encoding even on machines whose locale is UTF-8."""
    import os,subprocess
    code=("import sys; assert sys.flags.utf8_mode == 0; "
          "assert sys.flags.warn_default_encoding; "
          f"sys.path.insert(0, {str(ROOT/'tests')!r}); "
          "from test_remediation import test_bls_parser_rejects_truncated_source_table; "
          "test_bls_parser_rejects_truncated_source_table()")
    result=subprocess.run([sys.executable,'-X','utf8=0','-X','warn_default_encoding',
        '-W','error::EncodingWarning:test_remediation','-c',code],cwd=ROOT,
        env={**os.environ,'PYTHONIOENCODING':'utf-8'},capture_output=True,text=True,encoding='utf-8')
    # PYTHONIOENCODING only makes captured console text predictable; file I/O
    # still runs with UTF-8 mode disabled and project EncodingWarnings as errors.
    assert result.returncode==0,result.stdout+result.stderr


def test_annual_validation_rejects_monthly_substitution():
    fixture={'Results':{'series':[{'seriesID':'TEST','data':[{'year':'2022','period':'M01','value':'4.0'}]}]}}
    with pytest.raises(ValueError,match='M13'):parse_m13(fixture)
    fixture['Results']['series'][0]['data'].append({'year':'2022','period':'M13','value':'3.4'})
    assert parse_m13(fixture)=={'TEST':{2022:3.4}}


def test_repaired_bls_checker_has_no_import_network_or_mutation(monkeypatch):
    import urllib.request,subprocess,bls_sources
    def forbidden(*args,**kwargs):raise AssertionError('Import-time I/O is prohibited')
    monkeypatch.setattr(urllib.request,'urlopen',forbidden)
    monkeypatch.setattr(subprocess,'run',forbidden)
    monkeypatch.setattr(Path,'write_text',forbidden)
    monkeypatch.setattr(pd,'read_csv',forbidden)
    monkeypatch.setattr(bls_sources,'load_archives',forbidden)
    checker=load_module('checked_bls_import',ROOT/'member3_labor_migration/check_bls_revision.py')
    assert callable(checker.main)


def test_source_acquisition_rejects_credentials_escape_and_replaces_no_cache(tmp_path):
    for url in ['http://www.bls.gov/a','https://example.org/a','https://user:secret@www.bls.gov/a','https://api.bls.gov/a?registrationkey=secret']:
        with pytest.raises(ValueError):official_url(url)
    with pytest.raises(ValueError,match='Destination'):acquire('https://www.bls.gov/a',tmp_path.parent/'escaped',tmp_path)
    cached=tmp_path/'annual.csv';cached.write_text('isolated synthetic cache fixture',encoding='utf-8')
    before=cached.read_bytes()
    with pytest.raises(ValueError,match='Pinned source mismatch'):acquire('https://www.bls.gov/a',cached,tmp_path,'0'*64)
    assert cached.read_bytes()==before
    with pytest.raises(ValueError,match='1-3 attempts'):acquire('https://www.bls.gov/a',cached,tmp_path,attempts=999)


def test_labor_quantity_rate_rounding_and_wrong_units_fail(labor):
    checked=validate_labor_counts(labor);assert len(checked)==1176 and checked.passed.all()
    invalid=labor.copy();invalid.loc[0,'unemployment']*=1000
    with pytest.raises(ValueError,match='rounding'):validate_labor_counts(invalid)
    invalid=labor.copy();invalid.loc[0,'unemployment_rate_pct']=99
    with pytest.raises(ValueError,match='rounding'):validate_labor_counts(invalid)


def test_quoted_source_tables_have_exact_fields_and_complete_us_years():
    for path in [ROOT/'member3_labor_migration/sources.csv',ROOT/'docs/source_registry.csv']:
        with path.open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream,strict=True);rows=list(reader)
            assert len(reader.fieldnames)==10 and rows
            assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
            assert all(row['source_url'].startswith('https://') for row in rows)
    frame=pd.read_csv(ROOT/'member3_labor_migration/sources.csv')
    bls=frame[frame.source_organization=='U.S. Bureau of Labor Statistics']
    assert len(bls)==12 and bls.reference_period.nunique()==12


def test_akita_and_all_regions_are_visible_in_repaired_figures():
    record=json.loads((ROOT/'member3_labor_migration/figures/figure4_labor_2022.json').read_text(encoding='utf-8'))
    sample={r['country']:r for r in record['samples']}
    assert len(sample['USA']['ids'])==len(set(sample['USA']['ids']))==51
    assert len(sample['JPN']['ids'])==len(set(sample['JPN']['ids']))==47
    assert 'JP-05' in sample['JPN']['ids'] and sample['JPN']['x_range'][1]>38.6
    assert all(row['all_in_bounds'] and row['color_field']=='domestic_net_migration' for row in sample.values())
    jp=json.loads((ROOT/'member3_labor_migration/figures/jpn_labor_migration_2019_2022.json').read_text(encoding='utf-8'))
    assert jp['samples'][0]['n']==47 and 'JP-05' in jp['samples'][0]['ids']
    for stem in ['figure4_labor_2022','jpn_labor_migration_2019_2022','outliers_2022']:
        for suffix in ['png','svg']:
            assert (ROOT/f'member3_labor_migration/{stem}.{suffix}').read_bytes()==(ROOT/f'member3_labor_migration/figures/{stem}.{suffix}').read_bytes()


def test_pooled_services_blocked_before_any_figure_is_written(tmp_path,monkeypatch):
    frame=pd.read_csv(ROOT/'data/processed/merged_analysis.csv')
    for field in ['services_share_pct','services_va_local']:
        with pytest.raises(ValueError,match='BLOCKED'):require_comparable_pool(frame,[field])
        require_comparable_pool(frame.query("country=='USA'"),[field])
    chart=load_module('guarded_shared_plot',ROOT/'analysis/plot_correlations.py')
    monkeypatch.setattr(chart,'OUT',tmp_path/'must_not_exist')
    with pytest.raises(ValueError,match='BLOCKED'):chart.main(2022,'services_share_pct')
    assert not chart.OUT.exists()


def test_shared_merge_preserves_core_with_optional_missingness(labor):
    frame=pd.read_csv(ROOT/'data/processed/merged_analysis.csv')
    assert len(frame)==1176 and not frame.duplicated(['country','region_id','year']).any()
    assert frame.population_industry_match.eq('both').all()
    assert frame[['age65_share_pct','manufacturing_share_pct']].notna().all().all()
    assert frame.domestic_net_migration.isna().sum()==329
    assert frame.services_cross_country_status.str.startswith('BLOCKED').all()
    for year,g in frame.groupby('year'):
        assert g.groupby('country').size().to_dict()=={'USA':51,'JPN':47}
        assert set(g.loc[g.country=='JPN','gdp_reference_period'])=={f'FY{year}'}
        assert set(g.loc[g.country=='JPN','population_reference_date'])=={f'{year}-10-01'}
        assert set(g.loc[g.country=='USA','population_reference_date'])=={f'{year}-07-01'}
    invalid=frame.copy();invalid.loc[invalid.country=='JPN','gdp_reference_period']='CY2022'
    with pytest.raises(ValueError,match='metadata mismatch'):annotate_periods(invalid)


def test_main_results_match_unrounded_pre_repair_baseline_and_covariance_weights():
    baseline=json.loads((ROOT/'docs/remediation/regression_baseline.json').read_text(encoding='utf-8'))
    frame=pd.read_csv(ROOT/'data/processed/merged_analysis.csv')
    for row in baseline['unrounded_recomputed']:
        g=frame[frame.year==row['year']]
        if row['group']!='Pooled':g=g[g.country==row['group']]
        after=summarize(g,'age65_share_pct','manufacturing_share_pct')
        for field in ['pearson','spearman','slope','covariance']:
            assert after[field]==pytest.approx(row[field],abs=1e-12,rel=0)
        assert after['n']==row['n'] and after['excluded_missing']==0
    for row in baseline['covariance']:
        parts,total,_=decomposition(frame[frame.year==row['year']],'age65_share_pct','manufacturing_share_pct')
        assert total['denominator']=='N'
        assert {r['country']:r['country_weight'] for r in parts}=={'USA':51/98,'JPN':47/98}
        assert total['between_fraction']==pytest.approx(row['between_fraction'],abs=1e-12,rel=0)
        assert total['pooled_covariance']==pytest.approx(total['within_covariance']+total['between_covariance'],abs=1e-12,rel=0)


def test_national_and_boundary_evidence_preserves_real_region_codes():
    national=pd.read_csv(ROOT/'member1_demographics/national_source_checks.csv')
    assert len(national)==276 and national.passed.all() and national.difference.abs().max()<=1e-8
    boundaries=pd.read_csv(ROOT/'member1_demographics/boundary_join_checks.csv',dtype={'fips':str})
    assert len(boundaries)==51 and boundaries.region_id.is_unique and boundaries.fips.str.len().eq(2).all()
    assert boundaries.loc[boundaries.region_id=='US-AL','fips'].iloc[0]=='01'
    assert (boundaries.parts>1).sum()==14
    assert boundaries.original_value_checks.all() and boundaries.projection_parts_valid.all()
