"""Versioned local input protection after the explicitly authorized remediation.

The original Member 4 lock is never rewritten. Its files must still match the
external pre-change backup; the current tree must match a separately reviewed
lock. Creating a lock is explicit and refuses to overwrite any existing version.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/remediation'
LOCK=DOCS/'input_manifest_v2.json'
CURRENT=ROOT/'data/cache/remediation/current_member4'


def active_lock():
    candidates=list(DOCS.glob('input_manifest_v*.json'))
    return max(candidates,key=lambda p:int(p.stem.rsplit('v',1)[1])) if candidates else LOCK


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def historical_backup():
    initial=json.loads((DOCS/'prechange_manifest.json').read_text(encoding='utf-8'))
    return initial,Path(initial['backup'])/'files'


def verify_history():
    initial,backup=historical_backup()
    for row in initial['files']:
        if digest(backup/row['path'])!=row['sha256']:
            raise ValueError('Pre-change backup differs: '+row['path'])
    old=json.loads((ROOT/'analysis/member4/audit/input_manifest.json').read_text())
    for row in old['files']:
        if digest(backup/row['path'])!=row['sha256']:
            raise ValueError('Historical Member 4 baseline differs: '+row['path'])
    # Audit records/results are immutable historical evidence, even though selected
    # pipeline entry points and their README/test are deliberately made compatible.
    for row in initial['files']:
        if row['path'].startswith(('analysis/member4/audit/','analysis/member4/results/',
                                   'analysis/member4/data/','analysis/member4/figures/')) or row['path']=='analysis/member4/audit_report.md':
            if digest(ROOT/row['path'])!=row['sha256']:
                raise ValueError('Historical audit artifact was overwritten: '+row['path'])
    return len(initial['files'])


def verify():
    count=verify_history()
    lock=active_lock()
    if not lock.exists():raise ValueError('Current reviewed input lock not yet created; run the documented freeze once after validation')
    current=json.loads(lock.read_text(encoding='utf-8'))
    for previous in current.get('previous_locks',[]):
        if digest(ROOT/previous['path'])!=previous['sha256']:raise ValueError('Previous lock changed')
    for row in current['files']:
        if digest(ROOT/row['path'])!=row['sha256']:
            raise ValueError('Current reviewed input changed after validation: '+row['path'])
    return {'historical_backup_files':count,'current_protected_files':len(current['files']),'current_input_lock':lock.relative_to(ROOT).as_posix()}


def freeze(version=2,reason='Authorized cross-member remediation'):
    target=DOCS/f'input_manifest_v{version}.json'
    if version<2 or target.exists():raise FileExistsError('Preserve existing locks; do not refresh hashes to silence failures')
    if version>2 and not reason:raise ValueError('A new reviewed version requires the specific correction reason')
    verify_history();initial,backup=historical_backup()
    sys.path.insert(0,str(ROOT/'src'))
    from aging_economies.contracts import read_lookup,validate_table
    lookup=read_lookup(ROOT/'data/reference/region_lookup.csv')
    for name in ['demographics','industry','labor_migration']:
        validate_table(ROOT/f'data/processed/{name}.csv',name,lookup)
    # No core numerical correction was indicated by the independently checked sources.
    for name in ['demographics','industry']:
        path=f'data/processed/{name}.csv'
        pd.testing.assert_frame_equal(pd.read_csv(ROOT/path),pd.read_csv(backup/path),check_exact=True)
    sys.path.insert(0,str(ROOT/'member3_labor_migration'))
    from prepare_labor import build
    rebuilt=build(output_root=ROOT/'data/cache/remediation/prelock_member3')
    pd.testing.assert_frame_equal(rebuilt,pd.read_csv(ROOT/'data/processed/labor_migration.csv'),check_dtype=False,check_exact=False,atol=1e-9,rtol=0)
    original=pd.read_csv(backup/'data/processed/labor_migration.csv')
    keys=['country','region_id','year']
    pd.testing.assert_frame_equal(rebuilt[original.columns].sort_values(keys).reset_index(drop=True),
                                  original.sort_values(keys).reset_index(drop=True),check_dtype=False,check_exact=True)
    national=pd.read_csv(ROOT/'member1_demographics/national_source_checks.csv')
    if len(national)!=276 or not national.passed.all():raise ValueError('UN source gate incomplete')
    maps=pd.read_csv(ROOT/'member1_demographics/boundary_join_checks.csv')
    if len(maps)!=51 or not maps.original_value_checks.all() or not maps.projection_parts_valid.all():
        raise ValueError('Map source/value gate incomplete')
    paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
    excluded=('docs/remediation/','poster/presentation_manifest.csv')
    selected=sorted({p for p in paths if p and (ROOT/p).is_file() and not p.startswith(excluded)})
    if any(p.startswith(('.git/','.env','.venv/','data/raw/','data/cache/')) and p!='data/raw/.gitkeep' for p in selected):
        raise ValueError('Unexpected private/cache path in input lock')
    rows=[dict(path=p,sha256=digest(ROOT/p),bytes=(ROOT/p).stat().st_size) for p in selected]
    previous=sorted(DOCS.glob('input_manifest_v*.json'))
    if previous and version<=max(int(p.stem.rsplit('v',1)[1]) for p in previous):raise ValueError('Version must increase')
    prior={r['path']:r['sha256'] for r in json.loads(active_lock().read_text())['files']} if previous else {}
    record=dict(version=version,reason=reason,
        historical_lock='analysis/member4/audit/input_manifest.json',backup=str(backup.parent),
        previous_locks=[dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p)) for p in previous],
        reviewed_delta=[r['path'] for r in rows if prior and prior.get(r['path'])!=r['sha256']],
        source_validation='UN276; map51/102; Member3 full raw rebuild and196 independent domestic comparisons; unchanged core numerical tables',
        validation_evidence=['member1_demographics/independent_verification.json','member3_labor_migration/summary.json','member3_labor_migration/domestic_migration_comparison.csv'],
        files=rows)
    target.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Created reviewed v{version} lock:',len(rows),'files; earlier locks and229-file external backup retained')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze-reviewed',action='store_true')
    parser.add_argument('--version',type=int,default=2);parser.add_argument('--reason',default='Authorized cross-member remediation')
    args=parser.parse_args()
    if args.freeze_reviewed:freeze(args.version,args.reason)
    else:print(verify())
