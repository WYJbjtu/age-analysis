"""Isolated owner rebuilds and byte-level Member 4 reproduction; no remote access."""
from pathlib import Path
import hashlib, importlib.util, json, shutil, subprocess, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def copy(relative,dest):
    target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)

def main():
    if (ROOT/'docs/remediation/prechange_manifest.json').exists():
        sys.path.insert(0,str(ROOT/'scripts'))
        from verify_remediation import reproduction
        reproduction()
        return
    from freeze_inputs import main as protect
    protect()
    cache=ROOT/'data/cache/member4-reproduction';cache.mkdir(parents=True,exist_ok=True)
    checks=[]
    # Import inspected owner module, redirect its writers, and keep raw source files unchanged.
    m1root=cache/'member1';m1dir=m1root/'member1_demographics'
    for p in ['data/reference/region_lookup.csv','data/processed/demographics.csv',
              'member1_demographics/population_source_manifest.json','member1_demographics/snapshot_manifest.json',
              'member1_demographics/source_snapshots/wpp2024_selected_estimates.csv']:
        copy(p,m1root)
    m1=module('isolated_population',ROOT/'member1_demographics/complete_population.py');m1.ROOT=m1root;m1.MODULE=m1dir
    m1.main(ROOT/'data/raw/member4')
    for p in ['data/processed/demographics.csv','member1_demographics/population_detail_2011_2022.csv','member1_demographics/population_2019.csv','member1_demographics/population_2022.csv','member1_demographics/national_trends_wpp2024_2000_2022.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(ROOT/p),pd.read_csv(m1root/p),check_exact=False,atol=1e-8,rtol=0)
        checks.append(dict(check='Member1 isolated rebuild; semantic CSV equality',path=p,passed=True,notes='National WPP uses supplied snapshot, not independent source verification'))
    m2root=cache/'member2';m2dir=m2root/'member2_industry'
    for p in ['data/reference/region_lookup.csv','data/processed/industry.csv','member2_industry/source_manifest.json']:copy(p,m2root)
    m2=module('isolated_industry',ROOT/'member2_industry/prepare_industry.py');m2.ROOT=m2root;m2.MODULE=m2dir;m2.RAW=ROOT/'data/raw/member4'
    m2.main(False)
    pd.testing.assert_frame_equal(pd.read_csv(ROOT/'data/processed/industry.csv'),pd.read_csv(m2root/'data/processed/industry.csv'),check_exact=True)
    checks.append(dict(check='Member2 isolated rebuild; exact parsed CSV equality',path='data/processed/industry.csv',passed=True,notes='All 1176 rows; pinned official sources'))
    # Deterministic full M4 regeneration to a dedicated cache subdirectory.
    m4=cache/'member4'
    subprocess.run([sys.executable,str(HERE/'run_analysis.py'),'--output-dir',str(m4)],cwd=ROOT,check=True)
    for p in sorted(m4.rglob('*')):
        if not p.is_file():continue
        relative=p.relative_to(m4);expected=HERE/relative
        a=hashlib.sha256(p.read_bytes()).hexdigest();b=hashlib.sha256(expected.read_bytes()).hexdigest()
        checks.append(dict(check='Member4 deterministic bytes',path=str(relative).replace('\\','/'),passed=a==b,sha256=a,notes='PNG, SVG, CSV and environment outputs'))
    # Final documents are source artifacts; generated table-report writer is also deterministic.
    generated=[HERE/'findings.md',*[p for p in sorted((HERE/'audit').glob('*.csv')) if p.name!='reproduction_checks.csv'],HERE/'results/finding_evidence.csv']
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in generated}
    subprocess.run([sys.executable,str(HERE/'build_reports.py')],cwd=ROOT,check=True)
    for p in generated:
        checks.append(dict(check='Report regeneration deterministic bytes',path=str(p.relative_to(HERE)).replace('\\','/'),passed=before[str(p)]==hashlib.sha256(p.read_bytes()).hexdigest(),notes='Generated audit registers and findings'))
    pd.DataFrame(checks).to_csv(HERE/'audit/reproduction_checks.csv',index=False)
    if not all(c['passed'] for c in checks):raise AssertionError('Reproduction difference; inspect reproduction_checks.csv')
    protect();print(f'Isolated reproduction: {len(checks)} checks passed')

if __name__=='__main__':main()
