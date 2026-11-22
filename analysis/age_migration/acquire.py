"""Explicit official-source acquisition. Importing this module has no side effects."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request

MODULE = Path(__file__).resolve().parent
HOSTS = {'api.census.gov', 'www.census.gov', 'www2.census.gov',
         'www.e-stat.go.jp', 'www.stat.go.jp'}
LIMIT = 24 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def json_write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8', newline='\n')


def checked_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:
        raise ValueError('Only public official HTTPS sources are permitted')
    if any(k.lower() in {'key', 'appid', 'api_key'} for k, _ in urllib.parse.parse_qsl(parsed.query)):
        raise ValueError('Do not store credentials in source URLs')
    return url


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_payload(data, kind, content_type):
    if not data or len(data) > LIMIT:
        raise ValueError('Empty or excessive source response')
    if kind == 'json':
        if 'json' not in content_type:
            raise ValueError('Expected JSON content type')
        value = json.loads(data.decode('utf-8'))
        if not isinstance(value, (dict, list)):
            raise ValueError('Unexpected JSON schema')
    elif kind == 'xlsx' and not data.startswith(b'PK'):
        raise ValueError('Expected XLSX archive')
    elif kind == 'xls' and not data.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('Expected XLS compound file')
    elif kind == 'pdf' and not data.startswith(b'%PDF'):
        raise ValueError('Expected PDF')
    elif kind == 'html':
        if 'html' not in content_type or b'<html' not in data.lower():
            raise ValueError('Expected official HTML page')
    elif kind == 'dat':
        header = data.decode('utf-8-sig').splitlines()[0]
        if 'GEO_ID' not in header or '|' not in header:
            raise ValueError('Expected pipe-delimited ACS table-based summary file')


def fetch_one(spec, source_dir):
    filename = spec['file']
    if Path(filename).name != filename or ':' in filename:
        raise ValueError('Source file must be a simple basename')
    path = source_dir / 'raw' / filename
    url = checked_url(spec['url'])
    if path.exists():
        raise FileExistsError('Acquisition never replaces an existing raw source')
    opener = urllib.request.build_opener(OfficialRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'AgeMigrationResearch/1.0 (public academic data)'})
    for attempt in range(2):
        try:
            with opener.open(request, timeout=35) as response:
                if response.status != 200:
                    raise ValueError(f'Unexpected HTTP status {response.status}')
                data = response.read(LIMIT + 1)
                content_type = response.headers.get('Content-Type', '')
                final_url = checked_url(response.url)
            validate_payload(data, spec['format'], content_type)
            expected = spec.get('sha256')
            if expected and digest(data) != expected:
                raise ValueError('Official response differs from pinned source; retain version and investigate')
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
            return {**spec, 'sha256': digest(data), 'bytes': len(data),
                    'retrieved_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'final_url': final_url, 'content_type': content_type,
                    'status': 'live official retrieval verified'}
        except urllib.error.HTTPError as exc:
            if exc.code in (400, 401, 403, 404) or attempt == 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 1:
                raise
        time.sleep(1)
    raise RuntimeError('Bounded retrieval exhausted')


def acquire(source_dir=MODULE / 'sources', selected=None):
    source_dir = Path(source_dir)
    catalog = json_read(source_dir / 'catalog.json')
    manifest_path = source_dir / 'manifest.json'
    manifest = json_read(manifest_path) if manifest_path.exists() else []
    known = {row['id']: row for row in manifest}
    for spec in catalog:
        if selected and spec['id'] not in selected:
            continue
        if spec['id'] in known:
            old = known[spec['id']]
            if any(old[k] != spec[k] for k in ('file', 'url', 'format')):
                raise ValueError('Source ID cannot silently change file or URL')
            path = source_dir / 'raw' / old['file']
            if path.exists():
                if digest(path.read_bytes()) != old['sha256']:
                    raise ValueError('Raw source checksum changed')
                print(f"CACHED {spec['id']}")
                continue
            # Missing raw cache can be reacquired only against its pinned bytes.
            spec = {**spec, 'sha256': old['sha256']}
        new = fetch_one(spec, source_dir)
        if spec['id'] not in known:
            manifest.append(new)
            json_write(manifest_path, manifest)
        print(f"LIVE {spec['id']}: {new['bytes']} bytes {new['sha256']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids', nargs='+')
    args = parser.parse_args()
    acquire(selected=args.ids)
