"""Offline checks. Synthetic fixtures never leave this test module."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/member4'))
from descriptive import summarize,decomposition,classify
from run_analysis import merge_inputs,validate

def fixture_tables():
    # Clearly synthetic unit-test values, not research observations.
    keys=pd.DataFrame({'country':['USA','USA','JPN'],'region_id':['US-AA','US-BB','JP-01'],'year':[2022]*3})
    dem=keys.assign(age65_share_pct=[10.,20.,30.],total_population=[10,20,30])
    ind=keys.assign(manufacturing_share_pct=[20.,30.,40.])
    lab=keys.assign(unemployment_rate_pct=[2.,np.nan,4.],net_migration=[-1.,np.nan,3.])
    return dem,ind,lab,{'US-AA':'USA','US-BB':'USA','JP-01':'JPN'}

def test_join_cardinality_optional_missingness_does_not_shrink_core():
    d,i,l,k=fixture_tables();f=merge_inputs(d,i,l.iloc[:1],k)
    assert len(f)==3 and f.manufacturing_share_pct.notna().sum()==3
    assert f.unemployment_rate_pct.isna().sum()==2
    assert f.loc[f.region_id=='US-AA','net_migration'].iloc[0]==-1

def test_duplicate_keys_fail_before_join():
    d,i,l,k=fixture_tables()
    with pytest.raises(ValueError,match='duplicate'):merge_inputs(pd.concat([d,d.iloc[[0]]]),i,l,k)

def test_unknown_or_national_region_rejected():
    d,i,l,k=fixture_tables();d.loc[0,'region_id']='USA-NATIONAL'
    with pytest.raises(ValueError,match='invalid region'):merge_inputs(d,i,l,k)

@pytest.mark.parametrize('column,value,message',[('age65_share_pct',101.,'share'),('age65_share_pct',np.inf,'non-finite'),('total_population',0,'denominator')])
def test_invalid_values(column,value,message):
    d,i,l,k=fixture_tables();d.loc[0,column]=value
    with pytest.raises(ValueError,match=message):validate(d,k,'synthetic')

def test_nominal_units_and_share_check():
    d,i,l,k=fixture_tables()
    i=i.assign(nominal_gdp_local=100.,manufacturing_va_local=[20.,30.,40.],services_va_local=50.,services_share_pct=50.,gdp_reference_period=['CY2022','CY2022','FY2022'])
    validate(i,k,'synthetic');i.loc[0,'manufacturing_va_local']*=1000
    with pytest.raises(ValueError,match='share mismatch'):validate(i,k,'synthetic')

def test_grouped_and_pooled_reference_calculation():
    f=pd.DataFrame({'country':['A']*3+['B']*3,'x':[1.,2.,3.,4.,5.,6.],'y':[3.,1.,2.,9.,7.,8.]})
    s=summarize(f,'x','y')
    assert s['pearson']==pytest.approx(np.corrcoef(f.x,f.y)[0,1])
    assert s['slope']==pytest.approx(np.polyfit(f.x,f.y,1)[0])
    assert s['spearman']==pytest.approx(np.corrcoef(f.x.rank(),f.y.rank())[0,1])
    for _,g in f.groupby('country'):assert summarize(g,'x','y')['pearson']==pytest.approx(-.5)

def test_constant_and_small_samples_stay_missing():
    for f in [pd.DataFrame({'x':[1,1,1],'y':[2,3,4]}),pd.DataFrame({'x':[1,2],'y':[2,3]})]:
        s=summarize(f,'x','y');assert np.isnan(s['pearson']) and s['status']=='insufficient_or_constant'

def test_pairwise_missingness_is_reported():
    f=pd.DataFrame({'x':[1,2,3,np.nan],'y':[2,4,6,9]})
    s=summarize(f,'x','y');assert (s['n'],s['excluded_missing'])==(3,1)
    assert s['slope']==pytest.approx(2)

def test_covariance_with_unequal_groups_reconstructs_and_adjustment_matches():
    f=pd.DataFrame({'country':['A']*3+['B']*4,'x':[1.,2.,3.,7.,8.,9.,10.],'y':[3.,2.,1.,10.,9.,8.,7.]})
    parts,s,a=decomposition(f,'x','y')
    assert s['pooled_covariance']==pytest.approx(np.cov(f.x,f.y,ddof=0)[0,1])
    assert s['within_covariance']+s['between_covariance']==pytest.approx(s['pooled_covariance'])
    assert [r['country_weight'] for r in parts]==pytest.approx([3/7,4/7])
    assert a['pearson']==pytest.approx(-1)

def test_synthetic_strict_reversal():
    f=pd.DataFrame({'country':['A']*3+['B']*3,'x':[1,2,3,8,9,10],'y':[3,2,1,10,9,8]})
    pooled=summarize(f,'x','y')['pearson'];within=[summarize(g,'x','y')['pearson'] for _,g in f.groupby('country')]
    assert classify(pooled,within)=='direction reversal consistent with Simpson-type pattern'

def test_synthetic_nonreversal_and_weak_signs_never_strict_headline():
    assert classify(.7,[.2,.3])=='same direction; aggregation changes magnitude'
    assert classify(.7,[-.2,.3])=='different directions across countries'
    assert 'weak' in classify(.7,[-.001,-.002])
    assert 'no strict' in classify(.7,[.001,.002])

def test_population_weighting_is_separate_and_requires_valid_weights():
    f=pd.DataFrame({'x':[1.,2.,4.],'y':[3.,1.,6.],'w':[1.,2.,5.]})
    s=summarize(f,'x','y','w');assert s['weighting']=='population' and np.isnan(s['spearman'])
    w=f.w/f.w.sum();a=f.x-np.dot(w,f.x);b=f.y-np.dot(w,f.y)
    assert s['slope']==pytest.approx(np.dot(w,a*b)/np.dot(w,a*a))
    f.loc[0,'w']=0
    with pytest.raises(ValueError,match='positive'):summarize(f,'x','y','w')

def test_reviewed_current_inputs_and_historical_inputs_are_protected():
    # Intentional owner repairs have a separately validated lock. The old hashes
    # still protect the complete pre-change backup and immutable audit evidence.
    from freeze_inputs import main as protect
    protect()

def test_real_primary_sample_and_source_gate():
    for year in [2019,2022]:
        f=pd.read_csv(ROOT/f'analysis/member4/data/core_{year}.csv')
        assert len(f)==98 and not f.duplicated(['country','region_id','year']).any()
        assert f.groupby('country').size().to_dict()=={'JPN':47,'USA':51}
        assert not f[['age65_share_pct','manufacturing_share_pct']].isna().any().any()
    checks=pd.read_csv(ROOT/'analysis/member4/audit/source_record_checks.csv')
    assert checks.status.eq('PASS').all()

def test_primary_numbers_recompute_and_optional_series_cannot_contaminate():
    f=pd.read_csv(ROOT/'analysis/member4/data/core_2022.csv')
    s=summarize(f,'age65_share_pct','manufacturing_share_pct')
    f['domestic_net_migration']=np.nan
    assert summarize(f,'age65_share_pct','manufacturing_share_pct')==s
    r=pd.read_csv(ROOT/'analysis/member4/results/primary_summary.csv').query("year==2022 and group=='Pooled'").iloc[0]
    assert s['pearson']==pytest.approx(r.pearson,abs=1e-9)
