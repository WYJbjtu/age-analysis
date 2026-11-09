"""Freeze the inspected Git baseline and protected files; never update an existing lock."""
from pathlib import Path
import hashlib, json, subprocess
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'audit'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    # Local remediation is a new reviewed version, not a rewrite of historical v1.
    if (ROOT/'docs/remediation/prechange_manifest.json').exists():
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        from remediation_state import verify
        result=verify()
        print('Protected current reviewed version and historical v1:',result)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'input_manifest.json'
    if target.exists():
        manifest = json.loads(target.read_text(encoding='utf-8'))
        changed = [r['path'] for r in manifest['files'] if digest(ROOT/r['path']) != r['sha256']]
        if changed:
            raise ValueError(f'Protected inputs changed: {changed}')
        print(f"Protected inputs unchanged: {len(manifest['files'])}")
        return
    paths = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
    files = [{'path':p, 'bytes':(ROOT/p).stat().st_size, 'sha256':digest(ROOT/p)} for p in paths if p and (ROOT/p).is_file()]
    manifest = {'original_checkout':'10c5a4792a22abedd40347d019e879d848b61dd5',
                'baseline_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
                'recorded_date':'2026-11-09', 'local_uncommitted_inputs_at_start':False,
                'remote_writes':False, 'files':files}
    target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Frozen {len(files)} protected files')

if __name__=='__main__': main()
