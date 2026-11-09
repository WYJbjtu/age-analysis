"""Isolated integrity corruption fixtures; no real evidence or lock is modified."""
from pathlib import Path
import io
import json
import stat
import sys
import warnings
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import remediation_state as integrity


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def put(root, name, data):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def row(name, data):
    return dict(path=name, sha256=integrity.sha256(data), bytes=len(data))


def zip_bytes(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data, mode in entries:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)  # Deliberately duplicate fixture entry.
                archive.writestr(info, data)
    return out.getvalue()


def refresh_fixture_lock(root):
    """Only synthetic fixture expectations, never the real project lock."""
    path = root / 'docs/remediation/input_manifest_v5.json'
    lock = json.loads(path.read_bytes())
    for record in lock['files']:
        data = integrity.canonical((root / record['path']).read_bytes(), record['representation'], record['path'])
        record.update(sha256=integrity.sha256(data), bytes=len(data))
    path.write_bytes(encoded(lock))


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / 'synthetic-checkout'
    core = 'data/processed/synthetic.csv'
    audit = 'analysis/member4/results/synthetic.csv'
    contents = {core: b'value\r\n1\r\n', audit: b'value\r\n2\r\n'}
    contents[integrity.V1] = encoded({'files': [row(core, contents[core])]})
    initial = {'backup': 'Z:/nonexistent-developer-profile/original-backup',
               'files': [row(n, b) for n, b in contents.items()]}
    contents[integrity.PRECHANGE] = encoded(initial)
    prior = 'docs/remediation/input_manifest_v4.json'
    contents[prior] = encoded({'version': 4, 'previous_locks': [], 'files': initial['files']})
    archive_name = 'docs/remediation/historical_evidence.zip'
    archive = zip_bytes([(n, b, stat.S_IFREG | 0o644) for n, b in contents.items()])
    index = dict(archive=archive_name, archive_sha256=integrity.sha256(archive), reviewed_locks=[prior],
                 files=[row(n, b) for n, b in contents.items()])
    current = {**contents, archive_name: archive, integrity.EVIDENCE: encoded(index), 'current.py': b'VALUE = 1\n'}
    for name, data in current.items():
        # A fresh Git representation differs from the preserved historical CRLF bytes.
        put(root, name, integrity.canonical(data, integrity.representation(name), name))
    records = []
    for name in current:
        data = (root / name).read_bytes()
        records.append({**row(name, data), 'representation': integrity.representation(name)})
    put(root, 'docs/remediation/input_manifest_v5.json', encoded(dict(version=5,
        representation_policy='explicit-utf8-lf-v1', files=records,
        previous_locks=[dict(path=prior, repository_sha256=integrity.sha256(contents[prior]))])))
    return root


def rewrite_fixture_archive(root, modify):
    """Recompute only the enclosing synthetic ZIP checksums to reach member validation."""
    index = json.loads((root / integrity.EVIDENCE).read_bytes())
    with zipfile.ZipFile(root / index['archive']) as archive:
        entries = [(i.filename, archive.read(i), i.external_attr >> 16) for i in archive.infolist()]
    data = zip_bytes(modify(entries))
    put(root, index['archive'], data)
    index['archive_sha256'] = integrity.sha256(data)
    put(root, integrity.EVIDENCE, encoded(index))
    refresh_fixture_lock(root)


def test_deliverable_only_verification_without_developer_backup(checkout):
    result = integrity.verify(checkout)
    assert result['historical_evidence_files'] == 3
    assert result['historical_v1_files'] == 1
    assert result['immutable_repository_files'] == 2
    assert result['local_backup'] == 'not requested'


def test_verification_from_unrelated_working_directory(checkout, tmp_path, monkeypatch):
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert integrity.verify(checkout)['historical_evidence_files'] == 3


@pytest.mark.parametrize('path,layer', [
    ('current.py', 'current reviewed'),
    ('analysis/member4/results/synthetic.csv', 'immutable repository artifact'),
])
def test_protected_current_or_immutable_content_cannot_change(checkout, path, layer):
    (checkout / path).write_bytes(b'corrupt synthetic fixture\n')
    with pytest.raises(integrity.IntegrityError, match=layer):
        integrity.verify(checkout)


@pytest.mark.parametrize('operation', ['delete', 'modify'])
def test_required_historical_evidence_must_exist_and_match(checkout, operation):
    path = checkout / 'docs/remediation/historical_evidence.zip'
    if operation == 'delete':
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b'corrupt fixture')
    with pytest.raises(integrity.IntegrityError, match='portable evidence.*historical_evidence.zip'):
        integrity.verify(checkout)


def test_archive_member_tampering_fails_original_recorded_hash(checkout):
    rewrite_fixture_archive(checkout, lambda rows: [(n, b'changed' if n.endswith('synthetic.csv') else b, m) for n, b, m in rows])
    with pytest.raises(integrity.IntegrityError, match='member: original checksum mismatch'):
        integrity.verify(checkout)


def test_expected_archive_checksum_tampering_fails(checkout):
    index = json.loads((checkout / integrity.EVIDENCE).read_bytes())
    index['archive_sha256'] = '0' * 64
    put(checkout, integrity.EVIDENCE, encoded(index))
    refresh_fixture_lock(checkout)
    with pytest.raises(integrity.IntegrityError, match='archive checksum mismatch'):
        integrity.verify(checkout)


def test_missing_required_member_fails(checkout):
    rewrite_fixture_archive(checkout, lambda rows: rows[1:])
    with pytest.raises(integrity.IntegrityError, match='missing members'):
        integrity.verify(checkout)


@pytest.mark.parametrize('name', ['/outside', '../outside', 'a/../../outside', 'C:/outside', 'a\\..\\outside', './outside', 'a//outside'])
def test_archive_paths_cannot_escape_namespace(checkout, name):
    rewrite_fixture_archive(checkout, lambda rows: rows + [(name, b'fixture', stat.S_IFREG | 0o644)])
    with pytest.raises(integrity.IntegrityError, match='unsafe repository-relative path'):
        integrity.verify(checkout)


def test_duplicate_archive_names_fail(checkout):
    rewrite_fixture_archive(checkout, lambda rows: rows + [rows[0]])
    with pytest.raises(integrity.IntegrityError, match='duplicate name'):
        integrity.verify(checkout)


def test_archive_symlinks_are_never_followed(checkout):
    rewrite_fixture_archive(checkout, lambda rows: [(rows[0][0], b'../escape', stat.S_IFLNK | 0o777), *rows[1:]])
    with pytest.raises(integrity.IntegrityError, match='unsafe link/type'):
        integrity.verify(checkout)


def test_explicit_invalid_local_backup_fails_without_fallback(checkout, tmp_path):
    with pytest.raises(integrity.IntegrityError, match='explicit local backup'):
        integrity.verify(checkout, local_backup=tmp_path / 'absent-backup')
    backup = tmp_path / 'corrupt-backup'
    put(backup / 'files', 'data/processed/synthetic.csv', b'wrong')
    with pytest.raises(integrity.IntegrityError, match='explicit local backup: original checksum mismatch'):
        integrity.verify(checkout, local_backup=backup)


def test_verification_is_read_only(checkout):
    before = {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob('*') if p.is_file()}
    integrity.verify(checkout)
    integrity.verify(checkout)
    after = {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob('*') if p.is_file()}
    assert after == before


def test_text_policy_accepts_only_line_ending_representation_change(checkout):
    path = checkout / 'current.py'
    path.write_bytes(b'VALUE = 1\r\n')
    integrity.verify(checkout)
    path.write_bytes(b'VALUE = 1 \r\n')
    with pytest.raises(integrity.IntegrityError, match='current reviewed: checksum mismatch'):
        integrity.verify(checkout)


def test_original_manifests_remain_authoritative_if_member_inventory_is_changed(checkout):
    rewrite_fixture_archive(checkout, lambda rows: [(n, b'changed' if n.endswith('synthetic.csv') else b, m) for n, b, m in rows])
    index = json.loads((checkout / integrity.EVIDENCE).read_bytes())
    for record in index['files']:
        if record['path'].endswith('synthetic.csv'):
            record.update(sha256=integrity.sha256(b'changed'), bytes=7)
    put(checkout, integrity.EVIDENCE, encoded(index))
    refresh_fixture_lock(checkout)
    with pytest.raises(integrity.IntegrityError, match='original prechange: original checksum mismatch'):
        integrity.verify(checkout)


def test_missing_portable_lock_never_generates_a_replacement(checkout):
    (checkout / 'docs/remediation/input_manifest_v5.json').unlink()
    with pytest.raises(integrity.IntegrityError, match='portable reviewed lock required'):
        integrity.verify(checkout)
    assert not (checkout / 'docs/remediation/input_manifest_v5.json').exists()
