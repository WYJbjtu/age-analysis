from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
bad=[];count=0
for line in (root/'CHECKSUMS.sha256').read_text(encoding='utf-8').splitlines():
 expected,name=line.split('  ',1);p=root/name;count+=1
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:bad.append(name)
print(f'Checked {count} files; failures: {len(bad)}')
for name in bad:print(name)
raise SystemExit(bool(bad))
