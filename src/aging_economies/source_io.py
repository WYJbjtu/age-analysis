"""Bounded, credential-free acquisition of public official statistical files."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import time

OFFICIAL_HOSTS = {'www.bls.gov', 'api.bls.gov', 'download.bls.gov',
                  'www2.census.gov', 'www.census.gov', 'population.un.org',
                  'www.e-stat.go.jp', 'www.stat.go.jp', 'www.esri.cao.go.jp', 'apps.bea.gov'}


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def official_url(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in OFFICIAL_HOSTS or parsed.username or parsed.password:
        raise ValueError('Only explicit, credential-free official HTTPS sources are allowed')
    if any(word in parsed.query.lower() for word in ['registrationkey', 'api_key', 'token', 'password']):
        raise ValueError('Credentials are not accepted in source URLs')


def acquire(url, destination, allowed_root, expected_sha256=None, timeout=45, attempts=2):
    """Download separately from parsing; never replace a different existing cache."""
    official_url(url)
    if not 1 <= attempts <= 3 or not 0 < timeout <= 60:
        raise ValueError('Acquisition requires 1-3 attempts and a timeout of at most 60 seconds')
    path = Path(destination).resolve()
    root = Path(allowed_root).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Destination must be inside the explicit data directory')
    if path.exists():
        value = digest(path)
        if expected_sha256 and value != expected_sha256:
            raise ValueError(f'Pinned source mismatch: {path.name}')
        return dict(url=url, path=str(path), sha256=value, bytes=path.stat().st_size,
                    status='cached', online_reverified=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.part')
    for attempt in range(attempts):
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0 research-reproducibility'})
            with urlopen(request, timeout=timeout) as response:
                official_url(response.url)
                with temporary.open('wb') as output:
                    for block in iter(lambda: response.read(1024 * 1024), b''):
                        output.write(block)
            value = digest(temporary)
            if expected_sha256 and value != expected_sha256:
                raise ValueError(f'Pinned source mismatch: {path.name}; source not accepted')
            temporary.replace(path)
            return dict(url=url, path=str(path), sha256=value, bytes=path.stat().st_size,
                        status='retrieved', online_reverified=True,
                        retrieved_utc=datetime.now(timezone.utc).isoformat())
        except HTTPError as error:
            if error.code in (401, 403, 404) or attempt == attempts - 1:
                raise
        except (TimeoutError, OSError):
            if attempt == attempts - 1:
                raise
        time.sleep(1)
    raise RuntimeError('Acquisition exhausted')
