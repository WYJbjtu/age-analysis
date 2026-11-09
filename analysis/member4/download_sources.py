"""Read-only public official downloads to Member 4 cache; no teammate outputs touched."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import argparse, hashlib, json
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'data/raw/member4'
OUT = Path(__file__).resolve().parent/'audit/download_manifest.json'

def sources():
    items = []
    for module, filename in [('member1_demographics','population_source_manifest.json'),('member2_industry','source_manifest.json')]:
        for r in json.loads((ROOT/module/filename).read_text(encoding='utf-8')):
            if r['file'].startswith('wpp'):
                continue
            items.append({'file':r['file'],'url':r['url'],'expected_sha256':r['sha256'],'owner':module})
    for name,url in [
        ('jpn_lfs.xlsx','https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031952605&fileKind=0'),
        ('jpn_migration_2022.xlsx','https://www.stat.go.jp/data/idou/2022np/jissu/zuhyou/hyo1.xlsx'),
        ('jpn_migration_2019.xls','https://www.stat.go.jp/data/idou/2019np/kihon/zuhyou/hyo1.xls'),
        ('jpn_migration_trend.xls','https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031688387&fileKind=0'),
        ('us_migration_2022.csv','https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/totals/NST-EST2022-ALLDATA.csv'),
        ('us_migration_2020.csv','https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/state/totals/nst-est2020-alldata.csv'),
        ('bls_2022.html','https://www.bls.gov/news.release/archives/srgune_03012023.htm'),
        ('bls_2019.html','https://www.bls.gov/news.release/archives/srgune_03042020.htm')]:
        items.append({'file':name,'url':url,'expected_sha256':None,'owner':'member3_labor_migration'})
    return items

def fetch(r, previous, retry):
    path = RAW/r['file']
    if path.exists() and r['file'] in previous:
        prior = previous[r['file']]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=prior.get('sha256'):
            raise ValueError(f'Cached file changed: {path}')
        return prior
    if not retry and r['file'] in previous: return previous[r['file']]
    result = dict(r, retrieved_utc=datetime.now(timezone.utc).isoformat())
    if r['file'] in previous:
        result['previous_attempts']=previous[r['file']].get('previous_attempts',[])+[{k:v for k,v in previous[r['file']].items() if k!='previous_attempts'}]
    try:
        with urlopen(Request(r['url'],headers={'User-Agent':'Mozilla/5.0 research-source-verification'}),timeout=40) as response:
            data=response.read()
            result.update(final_url=response.url,content_type=response.headers.get('Content-Type'))
        path.write_bytes(data)
        sha=hashlib.sha256(data).hexdigest()
        result.update(status='retrieved',sha256=sha,bytes=len(data),matches_pinned_hash=(sha==r['expected_sha256'] if r['expected_sha256'] else None))
    except Exception as e:
        result.update(status='unavailable',error=f'{type(e).__name__}: {e}')
    print(result['file'],result['status'],result.get('matches_pinned_hash'),flush=True)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--retry-failed',action='store_true');args=p.parse_args()
    RAW.mkdir(parents=True,exist_ok=True);OUT.parent.mkdir(parents=True,exist_ok=True)
    previous={r['file']:r for r in json.loads(OUT.read_text(encoding='utf-8'))} if OUT.exists() else {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda r:fetch(r,previous,args.retry_failed),sources()))
    OUT.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
