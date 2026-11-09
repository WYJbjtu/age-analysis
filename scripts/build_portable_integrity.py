"""Explicit, local-only authoring of portable evidence and a reviewed lock.

Never called by verification or tests. Existing archives/manifests/locks cannot
be overwritten. Source bytes are taken only from the recorded ORIGINAL backup.
"""
from pathlib import Path
import argparse
import json
import stat
import zipfile

from remediation_state import (ROOT, PRECHANGE, EVIDENCE, V1, canonical, digest,
                               file_bytes, historical_content, immutable,
                               json_file, representation, rows_by_path, sha256,
                               verify_history)


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def package():
    initial = json_file(ROOT, PRECHANGE, 'package source')
    backup = Path(initial['backup']) / 'files'
    names = rows_by_path(initial['files'], 'package source')
    old = json_file(ROOT, V1, 'package source')
    for row in old['files']:
        if row['path'] not in names or names[row['path']]['sha256'] != row['sha256']:
            raise ValueError('Original manifests disagree: ' + row['path'])
    archive_path = ROOT / 'docs/remediation/historical_evidence.zip'
    index_path = ROOT / EVIDENCE
    if archive_path.exists() or index_path.exists():
        raise FileExistsError('Preserve existing portable evidence; never refresh it')
    contents = {}
    inventory = []
    for name, row in names.items():
        data = file_bytes(backup, name, 'original external backup')
        if sha256(data) != row['sha256'] or len(data) != row['bytes']:
            raise ValueError('Original recorded bytes do not match: ' + name)
        contents[name] = data
        inventory.append(dict(path=name, sha256=row['sha256'], bytes=len(data),
                              provenance='Original external prechange backup; unchanged recorded SHA-256'))
    locks = [f'docs/remediation/input_manifest_v{v}.json' for v in (2, 3, 4)]
    for name in [PRECHANGE, *locks]:
        data = file_bytes(ROOT, name, 'original metadata')
        contents[name] = data
        inventory.append(dict(path=name, sha256=sha256(data), bytes=len(data),
                              provenance='Existing pre-portability metadata; exact local bytes before repair'))
    # Fixed timestamps and regular-file modes; no extraction is ever required.
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 9, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    write_json(index_path, dict(version=1, archive=archive_path.relative_to(ROOT).as_posix(),
        archive_sha256=digest(archive_path), archive_bytes=archive_path.stat().st_size,
        original_manifest=PRECHANGE, historical_manifest=V1, reviewed_locks=locks,
        original_backup_location_metadata=initial['backup'],
        original_files=len(names), historical_v1_files=len(old['files']),
        handling='Original bytes, including CRLF, never normalized. Archived code is evidence only and must not be executed.',
        sensitivity_review='Only original manifest-listed repository deliverables and four lock/manifest records. No user profile, credentials, .env, .git, environment or unrelated cache. High-confidence key/private-key scan: no hits; DOCX XML scanned without extraction. Largest original member2444669 bytes.',
        files=sorted(inventory, key=lambda row: row['path'])))
    verify_history()
    print(f'Packaged and verified {len(names)} original files plus {len(locks)+1} metadata records; {archive_path.stat().st_size} compressed bytes')


def lock(version, delta_path):
    if version <= 4:
        raise ValueError('Portable lock must follow preserved v1/v2/v3/v4')
    target = ROOT / f'docs/remediation/input_manifest_v{version}.json'
    if target.exists():
        raise FileExistsError('Never overwrite an existing reviewed lock')
    verify_history()
    _, _, evidence, original = historical_content()
    old = json.loads(original['docs/remediation/input_manifest_v4.json'])
    before = rows_by_path(old['files'], 'prior v4')
    delta_name = delta_path.resolve().relative_to(ROOT).as_posix()
    delta = json_file(ROOT, delta_name, 'authorized delta')
    changes = rows_by_path(delta['changes'], 'authorized delta')
    # Every v4 raw hash must still match, or be exactly named in the authorized
    # code/configuration delta. Data, figures and results may not be changed.
    for name, row in before.items():
        current = file_bytes(ROOT, name, 'reviewed delta')
        if name in changes:
            change = changes[name]
            if change['before_sha256'] != row['sha256']:
                raise ValueError('Authorized delta has wrong original hash: ' + name)
            if name.startswith(('data/', 'member1_demographics/', 'member2_industry/', 'member3_labor_migration/')) or immutable(name):
                raise ValueError('Portability fix cannot change analytical evidence: ' + name)
        elif sha256(current) != row['sha256']:
            raise ValueError('Unapproved change to v4 bytes: ' + name)
    for name, change in changes.items():
        data = file_bytes(ROOT, name, 'reviewed delta')
        if sha256(data) != change['after_sha256'] or not change['reason']:
            raise ValueError('Unreviewed delta bytes or reason: ' + name)
    included = set(before) | set(changes) | {EVIDENCE, evidence['archive'], PRECHANGE,
                  delta_name, 'docs/remediation/regression_baseline.json'} | set(evidence['reviewed_locks'])
    rows = []
    for name in sorted(included):
        data = file_bytes(ROOT, name, 'new reviewed lock')
        mode = representation(name)
        value = canonical(data, mode, name)
        rows.append(dict(path=name, sha256=sha256(value), bytes=len(value), representation=mode,
                         authoring_bytes_sha256=sha256(data),
                         previous_v4_sha256=before[name]['sha256'] if name in before else None))
    record = dict(version=version, representation_policy='explicit-utf8-lf-v1',
        reason='Authorized portability-only code/config/tests and repository evidence package. All unchanged v4 input bytes verified before mapping text CRLF to repository LF; historical ZIP bytes unchanged.',
        authorized_delta=delta_name,
        previous_locks=[dict(path=p, original_sha256=sha256(original[p]),
                            repository_sha256=sha256(canonical(original[p], 'utf8-lf', p))) for p in evidence['reviewed_locks']],
        historical_lock=V1, historical_evidence=EVIDENCE,
        files=rows)
    write_json(target, record)
    from remediation_state import verify
    print(json.dumps(verify(), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['package', 'lock'])
    parser.add_argument('--version', type=int, default=5)
    parser.add_argument('--delta', type=Path)
    args = parser.parse_args()
    if args.operation == 'package':
        package()
    else:
        if args.delta is None:
            parser.error('lock requires an explicit --delta file')
        lock(args.version, args.delta)
