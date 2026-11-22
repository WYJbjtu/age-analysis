"""Read-only checks, explicit one-time extension freeze, and isolated offline replay."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import locale
import os
import shutil
import subprocess
import sys
import uuid
from acquire import MODULE, json_read, json_write, digest

ROOT=MODULE.parents[1]
EXTERNAL=['data/reference/region_lookup.csv','member1_demographics/boundary_join_checks.csv',
          'member1_demographics/population_detail_2011_2022.csv','data/processed/labor_migration.csv']
GENERATED_DIRS={'data','figures'}
GENERATED_RESULTS={'variable_mapping.csv','source_checks.csv','coverage.csv','preparation.json',
    'population_vintage_comparison.csv','associations.csv','leave_one_out.csv','influence_summary.csv',
    'year_comparison.csv','case_selection.csv','case_totals.csv','tokyo_decomposition.csv','reference_checkpoints.csv',
    'us_uncertainty_summary.csv','japan2022_positive20_24.csv','analysis_summary.json','figure_manifest.json'}
GENERATED_DOCS={'report_zh.md','presentation/findings_en.md','presentation/segment_en.md','presentation/examiner_qa.md'}


def safe_relative(name):
    p=PurePosixPath(name)
    if p.is_absolute() or not p.parts or '..' in p.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe manifest path')
    return Path(*p.parts)


def inventory(module=MODULE):
    return sorted(p for p in module.rglob('*') if p.is_file()
        and not any(part in {'__pycache__','.pytest_cache'} for part in p.relative_to(module).parts)
        and p.suffix!='.pyc')


def represented(path,mode):
    b=path.read_bytes()
    if mode=='utf8-lf':
        value=b.decode('utf-8').replace('\r\n','\n')
        if '\r' in value:raise ValueError('Lone CR in extension text')
        return value.encode('utf-8')
    if mode!='bytes':raise ValueError('Unknown representation')
    return b


def row_for(path,base):
    rel=path.relative_to(base).as_posix()
    mode='bytes' if rel.startswith('sources/raw/') or path.suffix in {'.png','.svg'} else 'utf8-lf'
    return dict(path=rel,sha256=digest(represented(path,mode)),representation=mode,bytes=path.stat().st_size)


def baseline_check(root=ROOT,module=MODULE,strict_bytes=False):
    baseline=json_read(module/'results/baseline.json' if strict_bytes else module/'results/baseline_representation.json')
    failed=[]
    for row in baseline['tracked_files']:
        p=root/safe_relative(row['path'])
        content=p.read_bytes() if strict_bytes and p.is_file() else represented(p,row['representation']) if p.is_file() else b''
        if not p.is_file() or digest(content)!=row['sha256']:failed.append(row['path'])
    if failed:raise ValueError('Protected authoring baseline changed: '+str(failed))
    return len(baseline['tracked_files'])


def freeze(module=MODULE,root=ROOT):
    target=module/'extension_manifest.json'
    if target.exists():raise FileExistsError('Never overwrite an existing reviewed extension manifest')
    baseline_check(root,module,strict_bytes=True)
    planned=[p.relative_to(root).as_posix() for p in inventory(module) if p.name!='next_commit_files.txt']
    planned.extend(['analysis/age_migration/next_commit_files.txt','analysis/age_migration/extension_manifest.json'])
    (module/'next_commit_files.txt').write_text('\n'.join(sorted(set(planned)))+'\n',encoding='utf-8',newline='\n')
    files=[row_for(p,module) for p in inventory(module)]
    external=[]
    for name in EXTERNAL:
        path=root/name
        external.append(dict(path=name,sha256=digest(represented(path,'utf8-lf')),
            authoring_sha256=digest(path.read_bytes()),representation='utf8-lf',role='read-only declared input'))
    json_write(target,dict(version=1,scope='additive age_migration extension only; shared v6 remains unchanged',
        files=files,external_inputs=external,self_hash_policy='manifest excludes itself; next_commit_files includes it',
        raw_policy='exact official bytes; source manifest pins retrieval',text_policy='UTF-8 with LF representation',
        freeze_policy='explicit one-time reviewed authoring; routine check never writes hashes'))
    print(f'Frozen extension v1: {len(files)} files plus manifest; {len(external)} read-only shared inputs.')


def check(module=MODULE,root=ROOT,check_full_baseline=True):
    from prepare import Sources
    manifest=json_read(module/'extension_manifest.json')
    expected={r['path'] for r in manifest['files']}|{'extension_manifest.json'}
    actual={p.relative_to(module).as_posix() for p in inventory(module)}
    if actual!=expected:raise ValueError(f'Unexpected/missing extension files: {sorted(actual^expected)}')
    for row in manifest['files']:
        path=module/safe_relative(row['path'])
        if digest(represented(path,row['representation']))!=row['sha256']:
            raise ValueError('Extension checksum changed: '+row['path'])
    for row in manifest['external_inputs']:
        if digest(represented(root/safe_relative(row['path']),row['representation']))!=row['sha256']:
            raise ValueError('Declared shared input changed: '+row['path'])
    sources=Sources(module)
    baseline_n=baseline_check(root,module) if check_full_baseline else None
    print(f'Extension verified: {len(manifest["files"])} files; {len(sources.rows)} raw sources; original tracked files unchanged={baseline_n}.')
    return manifest


def generated(name):
    p=PurePosixPath(name)
    return p.parts[0] in GENERATED_DIRS or name in GENERATED_DOCS or (p.parts[0]=='results' and p.name in GENERATED_RESULTS)


def isolated(module=MODULE,root=ROOT,manifest_required=True):
    """Copy complete intended delivery, never a developer cache, and deny network."""
    manifest=check(module,root) if manifest_required else None
    dest=root/'data/cache'/('age-migration-isolated-'+uuid.uuid4().hex)
    dest=dest.resolve()
    if not dest.is_relative_to((root/'data/cache').resolve()) or dest.exists():
        raise ValueError('Isolated destination must be new and contained in project data/cache')
    baseline=json_read(module/'results/baseline.json')
    portable={r['path']:r for r in json_read(module/'results/baseline_representation.json')['tracked_files']}
    files=[root/safe_relative(r['path']) for r in baseline['tracked_files']]+inventory(module)
    for source in files:
        target=dest/source.relative_to(root)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        rel=source.relative_to(root).as_posix()
        if rel in portable and portable[rel]['representation']=='utf8-lf':
            # Simulate the repository's LF checkout in the isolated copy only.
            target.write_bytes(represented(source,'utf8-lf'))
    copied=dest/'analysis/age_migration'
    # Ephemeral execution harness: no analytical inputs, only blocks outbound sockets.
    harness=dest/'offline_harness.py'
    harness.write_text('''import runpy, socket, sys
from pathlib import Path
def denied(*args, **kwargs):
    raise AssertionError("Network prohibited in isolated offline reproduction")
socket.socket.connect = denied
socket.create_connection = denied
target = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(target.parent))
sys.argv = sys.argv[1:]
runpy.run_path(str(target), run_name="__main__")
''',encoding='utf-8',newline='\n')
    env=os.environ.copy();env['PYTHONPATH']=str(dest/'src');env['MPLCONFIGDIR']=str(dest/'data/cache/mpl')
    commands=[]
    for script in ('prepare.py','analyze.py','plot.py','build_docs.py'):
        args=[sys.executable,'-X','utf8=0',str(harness),str(copied/script)]
        result=subprocess.run(args,cwd=dest,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,check=False)
        output=result.stdout.decode(locale.getencoding())
        commands.append(dict(script=script,exit_code=result.returncode,output=output))
        print(f'ISOLATED {script}: {result.returncode}',flush=True)
        if result.returncode:raise RuntimeError(output)
    differences=[];compared=0
    for source in inventory(module):
        name=source.relative_to(module).as_posix()
        if generated(name):
            compared+=1
            # Figure binary bytes and text authoring bytes are expected deterministic here.
            if digest(source.read_bytes())!=digest((copied/name).read_bytes()):differences.append(name)
    if differences:raise ValueError('Isolated generated artifacts differ: '+str(differences))
    baseline_check(dest,copied)
    if manifest:check(copied,dest)
    # Source hashes are independently checked after generation as well as before parsing.
    from prepare import Sources
    Sources(copied)
    return dict(status='PASS',destination=str(dest),intended_files_copied=len(files),
        generated_files_compared=compared,differences=differences,network='blocked by socket guard',
        baseline_copy_representation='declared UTF-8 text normalized to LF in isolated copy only; official raw bytes exact',
        private_cache='none copied; complete delivered raw files used',environment='same installed Python/dependencies; not a fresh dependency install',
        commands=commands)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['freeze','check','baseline','isolated'])
    args=p.parse_args()
    if args.command=='freeze':freeze()
    elif args.command=='check':check()
    elif args.command=='baseline':print(f'{baseline_check(strict_bytes=True)} original tracked files byte-unchanged.')
    else:print(json.dumps(isolated(),ensure_ascii=True,indent=2))
