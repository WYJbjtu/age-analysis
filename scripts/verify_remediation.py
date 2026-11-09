"""Current offline reproduction and regression checks, preserving historical audits."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,uuid
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from remediation_state import ROOT,DOCS,CURRENT,digest,verify,historical_backup


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def run(args,cwd=ROOT):
    command=[sys.executable,'-X','utf8',*map(str,args)]
    result=subprocess.run(command,cwd=cwd,env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True,encoding='utf-8')
    log=DOCS/'commands.jsonl'
    with log.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(command=command,cwd=str(cwd),exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr),ensure_ascii=False)+'\n')
    print(result.stdout,end='')
    if result.returncode:
        print(result.stderr);raise RuntimeError('Reproduction command failed: '+' '.join(map(str,args)))
    return result


def regression(write=True):
    sys.path.insert(0,str(ROOT/'analysis/member4'))
    from descriptive import summarize,decomposition
    baseline=json.loads((DOCS/'regression_baseline.json').read_text())
    d=pd.read_csv(ROOT/'data/processed/demographics.csv');i=pd.read_csv(ROOT/'data/processed/industry.csv')
    frame=d.merge(i,on=['country','region_id','year'],validate='one_to_one')
    if len(frame)!=baseline['panel_rows']:raise ValueError('Core panel changed')
    records=[]
    for old in baseline['unrounded_recomputed']:
        g=frame[frame.year==old['year']]
        if old['group']!='Pooled':g=g[g.country==old['group']]
        current=summarize(g,'age65_share_pct','manufacturing_share_pct')
        for key in ['pearson','spearman','slope','intercept','covariance']:
            difference=current[key]-old[key]
            records.append(dict(year=old['year'],group=old['group'],metric=key,before=old[key],after=current[key],difference=difference,passed=abs(difference)<=1e-12))
        if current['n']!=old['n'] or current['excluded_missing']!=0:raise ValueError('Primary sample changed')
    for old in baseline['covariance']:
        g=frame[frame.year==old['year']]
        parts,current,_=decomposition(g,'age65_share_pct','manufacturing_share_pct')
        for key in ['pooled_covariance','within_covariance','between_covariance','between_fraction']:
            diff=current[key]-old[key]
            records.append(dict(year=old['year'],group='decomposition',metric=key,before=old[key],after=current[key],difference=diff,passed=abs(diff)<=1e-12))
        if current['denominator']!='N':raise ValueError('Covariance normalization changed')
        for row in parts:
            if row['country_weight']!={'USA':51/98,'JPN':47/98}[row['country']]:raise ValueError('Country weights changed')
        support=g.groupby('country').age65_share_pct.agg(['min','max'])
        if support['min'].max()<=support['max'].min():raise ValueError('Aging support overlap changed')
    result=pd.DataFrame(records)
    if write:result.to_csv(DOCS/'regression_comparison.csv',index=False,float_format='%.17g')
    if not result.passed.all():raise AssertionError('Actual main result changed; investigate, do not force baseline')
    print(f'{len(result)} high-precision main regression comparisons passed; max difference {result.difference.abs().max():.3g}')
    return result


def reproduction():
    verify();regression()
    # A new directory avoids cleanup or accidental reuse of somebody else's work.
    stage=ROOT/'data/cache/remediation'/('reproduce-'+uuid.uuid4().hex[:12]);stage.mkdir(parents=True)
    checks=[]
    def copy(relative,target=stage):
        destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,destination)
    def equal(relative,kind='semantic',target=stage,note=''):
        if kind=='bytes':passed=digest(ROOT/relative)==digest(target/relative)
        else:
            pd.testing.assert_frame_equal(pd.read_csv(ROOT/relative),pd.read_csv(target/relative),check_exact=False,atol=1e-8,rtol=0)
            passed=True
        checks.append(dict(path=relative,comparison=kind,passed=passed,rebuilt_path=str(target/relative),note=note))
        if not passed:raise AssertionError('Reproduction changed '+relative)
    for p in ['data/reference/region_lookup.csv','data/processed/demographics.csv','data/processed/industry.csv',
              'member1_demographics/population_source_manifest.json','member1_demographics/snapshot_manifest.json',
              'member1_demographics/source_snapshots/wpp2024_selected_estimates.csv','member2_industry/source_manifest.json']:
        copy(p)
    # Supply the original full WPP source as well as the original regional sources.
    raw=stage/'data/raw/member1';raw.mkdir(parents=True)
    for row in json.loads((ROOT/'member1_demographics/population_source_manifest.json').read_text()):
        source=ROOT/'data/raw/member4'/row['file']
        if row['file']=='wpp_ages.xlsx':source=ROOT/'data/raw/member1'/row['file']
        if digest(source)!=row['sha256']:raise ValueError('Member1 raw version changed')
        shutil.copyfile(source,raw/row['file'])
    m1=module('remediation_population',ROOT/'member1_demographics/complete_population.py');m1.ROOT=stage;m1.MODULE=stage/'member1_demographics'
    m1.main(raw)
    for p in ['data/processed/demographics.csv','member1_demographics/population_detail_2011_2022.csv',
              'member1_demographics/population_2019.csv','member1_demographics/population_2022.csv',
              'member1_demographics/national_trends_wpp2024_2000_2022.csv']:
        equal(p,note='Pinned official sources, including original full WPP workbook; tolerance only saved decimal precision')
    # Use the delivered bytes after semantic checks so figure checks isolate plotting.
    for p in ['data/processed/demographics.csv','data/processed/industry.csv'] :copy(p)
    m2=module('remediation_industry',ROOT/'member2_industry/prepare_industry.py');m2.ROOT=stage;m2.MODULE=stage/'member2_industry';m2.RAW=ROOT/'data/raw/member2'
    m2.main(False);equal('data/processed/industry.csv');equal('member2_industry/comparability.json','bytes')
    copy('data/processed/industry.csv')
    m3=module('remediation_labor',ROOT/'member3_labor_migration/prepare_labor.py');m3.build(output_root=stage)
    for p in ['data/processed/labor_migration.csv',*[f'member3_labor_migration/{name}' for name in
              ['jpn_labor_detail.csv','us_labor_detail.csv','rounding_validation.csv','domestic_migration_comparison.csv','coverage.csv','sources.csv','summary.json']]]:
        equal(p,'bytes',note='No existing processed CSV input; independent raw-source rebuild')
    run([ROOT/'member3_labor_migration/check_bls_revision.py','--output',stage/'member3_labor_migration/bls_revision_check.csv'])
    equal('member3_labor_migration/bls_revision_check.csv','bytes')
    # Re-run the actual owner plotting/text programs with identical stage inputs.
    for p in ['plot_helpers.py','labor_validation.py','plot_figure4.py','plot_japan_labor.py','plot_japan_trend.py',
              'plot_two_country_trend.py','outliers_2022.py','build_findings.py']:
        copy('member3_labor_migration/'+p)
    for p in ['plot_figure4.py','plot_japan_labor.py','plot_japan_trend.py','plot_two_country_trend.py','outliers_2022.py','build_findings.py']:
        run([stage/'member3_labor_migration'/p],cwd=stage)
    for path in sorted((ROOT/'member3_labor_migration/figures').glob('*')):
        if path.suffix in ['.png','.svg','.json']:equal(path.relative_to(ROOT).as_posix(),'bytes')
    for name in ['README.md','findings.md','report_section.md','outliers_2022.csv']:
        equal('member3_labor_migration/'+name,'bytes')
    # Re-run the unchanged Member2 plotting program against the reviewed current
    # renderer's artifacts; previous-renderer originals remain in the backup.
    copy('member2_industry/plot_industry.py')
    run([stage/'member2_industry/plot_industry.py'],cwd=stage)
    for path in sorted((ROOT/'member2_industry/figures').glob('*')):
        if path.suffix in ['.png','.svg']:equal(path.relative_to(ROOT).as_posix(),'bytes')
    # Current Member4 output is separate from the frozen historical delivery.
    run([ROOT/'analysis/member4/run_analysis.py','--output-dir',stage/'member4'])
    for path in sorted((stage/'member4/results').glob('*.csv')):
        if path.name=='selected_cases.csv':continue # Context columns deliberately expanded; main selection tested separately.
        historical=ROOT/'analysis/member4/results'/path.name
        if not historical.exists():raise ValueError('Unexpected Member4 result')
        same=digest(path)==digest(historical)
        checks.append(dict(path='analysis/member4/results/'+path.name,comparison='bytes against historical',passed=same,rebuilt_path=str(path),note='Primary, sensitivity, covariance and within-country numerical results'))
    for path in sorted((stage/'member4/figures').glob('*')):
        same=digest(path)==digest(ROOT/'analysis/member4/figures'/path.name)
        checks.append(dict(path='analysis/member4/figures/'+path.name,comparison='bytes against historical',passed=same,rebuilt_path=str(path),note='Main/covariance/case figures'))
    old=pd.read_csv(ROOT/'analysis/member4/results/selected_cases.csv')
    new=pd.read_csv(stage/'member4/results/selected_cases.csv')
    columns=['country','region_id','year','selection','pair','aging_gap_pp','manufacturing_gap_pp','domestic_net_migration']
    pd.testing.assert_frame_equal(old[columns],new[columns],check_exact=True)
    checks.append(dict(path='analysis/member4/results/selected_cases.csv',comparison='exact selected regions and numerical fields',passed=True,rebuilt_path=str(stage/'member4/results/selected_cases.csv'),note='Context metadata extended without changing case selection'))
    pd.DataFrame(checks).to_csv(DOCS/'reproduction_checks.csv',index=False)
    if not all(row['passed'] for row in checks):raise AssertionError('Reproduction differences; see current reproduction_checks.csv')
    verify();print(f'{len(checks)} isolated reproduction checks passed; stage preserved at {stage}')


def tests():
    verify()
    temporary=ROOT/'data/cache'/('remediation-pytest-'+uuid.uuid4().hex)
    if temporary.exists():raise FileExistsError('Refuse to reuse a pytest cleanup destination')
    run(['-m','pytest','-q','--basetemp',temporary,'--junitxml',DOCS/'test_results.xml'])
    run(['scripts/validate_data.py'])


def reports():
    verify();reg=regression()
    summary=dict(main_comparisons=len(reg),main_max_absolute_difference=float(reg.difference.abs().max()),
        historical_protection=verify(),main_panel_rows=1176,main_regions_per_year={'USA':51,'JPN':47},
        optional_domestic_reference_rows=196,main_exclusions=0,
        live_source_retrieval='UN WPP, Census boundaries, Japanese2018/2020/2021 migration newly retrieved; pinned prior official raw files reused',
        bls_status='612 official archive rows independently read; traceable text-cache reproduction; direct HTML403; no current API verification',
        source_checks='not yet run',tests='not yet run',reproduction='not yet run',visual_review='not yet recorded')
    path=CURRENT/'audit/source_record_checks.csv'
    if path.exists():
        f=pd.read_csv(path);summary['source_checks']={'total':len(f),'failed':int(f.status.ne('PASS').sum())}
    path=DOCS/'test_results.xml'
    if path.exists():
        suites=list(ET.parse(path).getroot().iter('testsuite'))
        summary['tests']={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
    path=DOCS/'reproduction_checks.csv'
    if path.exists():
        f=pd.read_csv(path);summary['reproduction']={'checks':len(f),'failed':int((~f.passed).sum())}
    path=DOCS/'visual_review.json'
    if path.exists():summary['visual_review']=json.loads(path.read_text())
    (DOCS/'validation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Current validation written to docs/remediation/validation.json; original audit reports preserved.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['regression','reproduce','tests','reports'])
    parser.add_argument('--no-write',action='store_true',help='Read-only regression check; never refresh saved evidence')
    args=parser.parse_args()
    if args.no_write and args.action!='regression':parser.error('--no-write applies only to regression')
    if args.action=='regression':regression(write=not args.no_write)
    else:{'reproduce':reproduction,'tests':tests,'reports':reports}[args.action]()
