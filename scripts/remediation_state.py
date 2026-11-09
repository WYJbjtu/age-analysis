"""Read-only integrity verification from repository-deliverable evidence.

Four layers stay distinct: current reviewed files, immutable repository audit
artifacts, original historical bytes in the evidence ZIP, and an optional local
backup. Only CRLF -> LF is canonicalized for explicitly declared UTF-8 text.
Historical archive member bytes are always hashed without normalization.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/remediation'
CURRENT = ROOT / 'data/cache/remediation/current_member4'
PRECHANGE = 'docs/remediation/prechange_manifest.json'
EVIDENCE = 'docs/remediation/historical_evidence.json'
V1 = 'analysis/member4/audit/input_manifest.json'
TEXT_SUFFIXES = {'.py', '.md', '.csv', '.json', '.svg', '.xml', '.html', '.toml',
                 '.yml', '.yaml', '.txt', '.sha256'}
TEXT_NAMES = {'.editorconfig', '.gitattributes', '.gitignore', '.gitkeep'}
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


class IntegrityError(ValueError):
    """A required verification layer failed; never a reason to skip validation."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha256(Path(path).read_bytes())


def relative_path(name, layer):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or any(ord(c) < 32 for c in name)
            or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..') for p in name.split('/'))
            or any(p.lower() in {'.git', '.venv', '.codex', '.aws', '.env'}
                   for p in name.split('/'))):
        raise IntegrityError(f'{layer}: unsafe repository-relative path {name!r}')
    return name


def file_bytes(root, name, layer):
    name = relative_path(name, layer)
    root = Path(root).resolve()
    path = root / name
    if not path.resolve().is_relative_to(root):
        raise IntegrityError(f'{layer}: path escapes repository: {name}')
    if any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
        raise IntegrityError(f'{layer}: symlink is not protected regular content: {name}')
    try:
        return path.read_bytes()
    except OSError as exc:
        raise IntegrityError(f'{layer}: missing or unreadable file {name}: {exc}') from exc


def representation(name):
    path = PurePosixPath(name)
    return 'utf8-lf' if path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES else 'bytes'


def canonical(data, mode, name):
    if mode == 'bytes':
        return data
    if mode != 'utf8-lf' or representation(name) != 'utf8-lf':
        raise IntegrityError(f'representation: invalid text policy for {name}: {mode}')
    try:
        data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise IntegrityError(f'representation: invalid UTF-8 in {name}') from exc
    result = data.replace(b'\r\n', b'\n')
    if b'\r' in result:
        raise IntegrityError(f'representation: lone CR in {name}')
    return result  # Do not strip spaces, change encoding, or add a final newline.


def json_file(root, name, layer):
    try:
        return json.loads(file_bytes(root, name, layer))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f'{layer}: invalid JSON {name}') from exc


def active_lock(root=ROOT):
    candidates = [(int(m[1]), p) for p in (Path(root) / 'docs/remediation').glob('input_manifest_v*.json')
                  if (m := re.fullmatch(r'input_manifest_v(\d+)\.json', p.name))]
    if not candidates:
        raise IntegrityError('current reviewed: missing reviewed input lock')
    return max(candidates)[1]


def historical_backup(root=ROOT):
    """Compatibility metadata for historical reports; does not access that path."""
    initial = json_file(root, PRECHANGE, 'historical metadata')
    return initial, Path(initial['backup']) / 'files'


def immutable(name):
    return name.startswith(('analysis/member4/audit/', 'analysis/member4/results/',
                            'analysis/member4/data/', 'analysis/member4/figures/')) or name == 'analysis/member4/audit_report.md'


def rows_by_path(rows, layer):
    result = {}
    for row in rows:
        name = relative_path(row['path'], layer)
        if name in result:
            raise IntegrityError(f'{layer}: duplicate inventory path {name}')
        result[name] = row
    return result


def historical_content(root=ROOT):
    """Validate the ZIP itself, every member, inventory, and original manifests.

    No member is extracted, imported or executed (including the archived unsafe
    BLS checker). Expected hashes come from the original, preserved manifests.
    """
    index = json_file(root, EVIDENCE, 'portable evidence')
    archive_name = relative_path(index['archive'], 'portable evidence')
    archive_data = file_bytes(root, archive_name, 'portable evidence')
    if sha256(archive_data) != index['archive_sha256']:
        raise IntegrityError(f'portable evidence: archive checksum mismatch: {archive_name}')
    expected = rows_by_path(index['files'], 'portable evidence inventory')
    contents = {}
    import io
    try:
        with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
            total = 0
            for info in archive.infolist():
                name = relative_path(info.filename, 'portable evidence member')
                if name in contents:
                    raise IntegrityError(f'portable evidence member: duplicate name {name}')
                mode = info.external_attr >> 16
                if info.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG) or info.flag_bits & 1:
                    raise IntegrityError(f'portable evidence member: unsafe link/type/encryption: {name}')
                total += info.file_size
                if info.file_size > MAX_MEMBER_BYTES or total > MAX_ARCHIVE_BYTES:
                    raise IntegrityError(f'portable evidence member: size limit exceeded: {name}')
                if name not in expected:
                    raise IntegrityError(f'portable evidence member: unexpected file {name}')
                data = archive.read(info)
                if len(data) != expected[name]['bytes'] or sha256(data) != expected[name]['sha256']:
                    raise IntegrityError(f'portable evidence member: original checksum mismatch: {name}')
                contents[name] = data
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise IntegrityError(f'portable evidence: unreadable ZIP {archive_name}: {exc}') from exc
    if set(contents) != set(expected):
        raise IntegrityError(f'portable evidence: missing members: {sorted(set(expected) - set(contents))}')
    try:
        initial = json.loads(contents[PRECHANGE])
        old = json.loads(contents[V1])
    except (KeyError, ValueError) as exc:
        raise IntegrityError('portable evidence: original prechange/v1 manifest missing or invalid') from exc
    original = rows_by_path(initial['files'], 'original prechange manifest')
    for layer, rows in [('original prechange', original), ('historical v1', rows_by_path(old['files'], 'historical v1'))]:
        for name, row in rows.items():
            if name not in contents or sha256(contents[name]) != row['sha256']:
                raise IntegrityError(f'{layer}: original checksum mismatch or missing member: {name}')
    allowed = set(original) | {PRECHANGE} | set(index['reviewed_locks'])
    if set(contents) != allowed:
        raise IntegrityError('portable evidence: inventory differs from original manifests and declared reviewed locks')
    # Old absolute locations remain historical text only. Their contents and the
    # prior lock chain must match the corresponding repository representation.
    for name in [PRECHANGE, *index['reviewed_locks']]:
        if canonical(file_bytes(root, name, 'historical manifest'), 'utf8-lf', name) != canonical(contents[name], 'utf8-lf', name):
            raise IntegrityError(f'historical manifest: repository representation changed: {name}')
        if name != PRECHANGE:
            for previous in json.loads(contents[name]).get('previous_locks', []):
                p = previous['path']
                if p not in contents or sha256(contents[p]) != previous['sha256']:
                    raise IntegrityError(f'historical lock chain: original checksum mismatch: {p}')
    return initial, old, index, contents


def verify_history(root=ROOT, local_backup=None):
    initial, old, index, contents = historical_content(root)
    count = 0
    for row in initial['files']:
        name = row['path']
        if immutable(name):
            current = file_bytes(root, name, 'immutable repository artifact')
            mode = representation(name)
            if canonical(current, mode, name) != canonical(contents[name], mode, name):
                raise IntegrityError(f'immutable repository artifact: original content changed: {name}')
            count += 1
    if local_backup is not None:
        # Explicit mode never falls back to the ZIP when a supplied backup fails.
        for row in initial['files']:
            data = file_bytes(Path(local_backup) / 'files', row['path'], 'explicit local backup')
            if sha256(data) != row['sha256']:
                raise IntegrityError(f'explicit local backup: original checksum mismatch: {row["path"]}')
    return {'historical_evidence_files': len(initial['files']), 'historical_v1_files': len(old['files']),
            'immutable_repository_files': count, 'archived_reviewed_locks': len(index['reviewed_locks']),
            'local_backup': 'verified' if local_backup is not None else 'not requested'}


def verify(root=ROOT, local_backup=None):
    root = Path(root).resolve()
    lock = active_lock(root)
    name = lock.relative_to(root).as_posix()
    current = json_file(root, name, 'current reviewed')
    if current.get('representation_policy') != 'explicit-utf8-lf-v1':
        raise IntegrityError(f'current reviewed: portable reviewed lock required: {name}')
    rows = rows_by_path(current['files'], 'current reviewed')
    if not {EVIDENCE, PRECHANGE, V1}.issubset(rows):
        raise IntegrityError('current reviewed: required evidence/manifest omitted from lock')
    for path, row in rows.items():
        layer = 'immutable repository artifact' if immutable(path) else ('portable evidence' if path.startswith('docs/remediation/historical_evidence.') else 'current reviewed')
        data = file_bytes(root, path, layer)
        checked = canonical(data, row['representation'], path)
        if sha256(checked) != row['sha256'] or len(checked) != row['bytes']:
            raise IntegrityError(f'{layer}: checksum mismatch: {path}')
    for previous in current['previous_locks']:
        path = previous['path']
        data = file_bytes(root, path, 'previous reviewed lock')
        if sha256(canonical(data, 'utf8-lf', path)) != previous['repository_sha256']:
            raise IntegrityError(f'previous reviewed lock: repository checksum mismatch: {path}')
    result = verify_history(root, local_backup)
    result.update(current_protected_files=len(rows), current_input_lock=name)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-backup', type=Path, help='Explicitly verify this backup root (containing files/), in addition to portable verification')
    args = parser.parse_args()
    print(json.dumps(verify(local_backup=args.local_backup), indent=2))
