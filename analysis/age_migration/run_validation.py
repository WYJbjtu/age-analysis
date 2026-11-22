"""Explicit local validation runner. No networking, cleanup, Git mutation or lock refresh."""
import datetime as dt
import importlib.metadata
import locale
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from acquire import MODULE, json_write
from verify_extension import baseline_check, isolated

ROOT=MODULE.parents[1]


def run():
    if (MODULE/'extension_manifest.json').exists():
        raise RuntimeError('Validation evidence is frozen; use the documented read-only checks or isolated replay, not overwrite saved evidence')
    logs=MODULE/'results/logs';logs.mkdir(exist_ok=True)
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
    unique=uuid.uuid4().hex[:12]
    test_args=['-m','pytest','-q','tests','member2_industry','analysis/age_migration/tests','-p','no:cacheprovider']
    tests=[('full_offline_utf8_off',['-X','utf8=0',*test_args,'--basetemp',f'data/cache/age-migration-tests-{unique}']),
        ('full_offline_encoding_warnings',['-X','utf8=0','-X','warn_default_encoding',*test_args,'--basetemp',f'data/cache/age-migration-encoding-{unique}']),
        ('reviewed_v6_integrity',['-X','utf8=0','scripts/remediation_state.py']),
        ('member4_readonly_freeze_entry',['-X','utf8=0','analysis/member4/freeze_inputs.py']),
        ('data_contracts',['-X','utf8=0','scripts/validate_data.py']),
        ('main_analysis_readonly_regression',['-X','utf8=0','scripts/verify_remediation.py','regression','--no-write'])]
    records=[]
    for label,args in tests:
        print('RUN '+label,flush=True)
        completed=subprocess.run([sys.executable,*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,timeout=360,check=False)
        output=completed.stdout.decode(locale.getencoding()).replace('\r\n','\n')
        (logs/f'{label}.txt').write_text(output,encoding='utf-8',newline='\n')
        found=re.findall(r'\d+ passed[^\n]*',output)
        summary=found[-1].strip() if found else output.strip().splitlines()[-1] if output.strip() else '(no output)'
        records.append(dict(label=label,command=[sys.executable,*args],exit_code=completed.returncode,
            summary=summary,log=f'results/logs/{label}.txt'))
        print(f'{label}: {completed.returncode}; {summary}',flush=True)
        if completed.returncode:raise RuntimeError(f'{label} failed; see captured log')
    environment=dict(python=sys.version,executable=sys.executable,platform=sys.platform,
        locale_encoding=locale.getencoding(),preferred_encoding=locale.getpreferredencoding(False),
        utf8_mode=sys.flags.utf8_mode,stdout_encoding=sys.stdout.encoding,
        packages={name:importlib.metadata.version(name) for name in ('numpy','pandas','matplotlib','openpyxl','xlrd','pytest')},
        not_tested=['cp1252','Linux in this extension task','fresh package installation'])
    original_count=baseline_check(strict_bytes=True)
    # One pre-freeze offline rehearsal; the final frozen manifest is checked separately.
    replay=isolated(manifest_required=False)
    json_write(MODULE/'results/validation.json',dict(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        environment=environment,commands=records,original_tracked_files_unchanged=original_count,
        isolated_reproduction=replay,raw_live_retrieval='See sources/manifest.json; this runner is offline',
        active_shared_lock='v6 unchanged',main_results='read-only 38-comparison regression; see log',
        safety='No historical unsafe scripts executed/imported; no Git or remote write operations'))
    print('Validation and pre-freeze isolated reproduction passed.',flush=True)


if __name__=='__main__':run()
