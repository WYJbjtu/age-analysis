"""Acquire official sources; failures are recorded and never replaced by invented data."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse, json, shutil, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from aging_economies.source_io import acquire, digest

BLS_RELEASES = {2011:'02292012', 2012:'03012013', 2013:'02282014', 2014:'03042015',
                2015:'02262016', 2016:'02282017', 2017:'02272018', 2018:'02282019',
                2019:'03042020', 2020:'03032021', 2021:'03022022', 2022:'03012023'}


def source_specs(group):
    result = []
    if group in ('all', 'member1'):
        manifest = json.loads((ROOT/'member1_demographics/population_source_manifest.json').read_text(encoding='utf-8'))
        wpp = next(r for r in manifest if r['file']=='wpp_ages.xlsx')
        result.append(dict(file='wpp_ages.xlsx', url=wpp['url'], sha256=wpp['sha256'], owner='member1'))
        result.append(dict(file='census_states_2022.zip',
            url='https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip',
            sha256='fb2c327c32869dc27bee7a6e0e6130f9d936c4f85638b8414af799f1251e3816', owner='member1'))
    if group in ('all', 'member3'):
        prior = json.loads((ROOT/'analysis/member4/audit/download_manifest.json').read_text(encoding='utf-8'))
        for r in prior:
            if r['owner']=='member3_labor_migration' and r['status']=='retrieved':
                result.append(dict(file=r['file'], url=r['url'], sha256=r['sha256'], owner='member3',
                                   original_cache='data/raw/member4/'+r['file']))
        for year in (2018, 2020, 2021):
            section = 'kihon' if year==2018 else 'jissu'
            result.append(dict(file=f'jpn_migration_{year}.xls', owner='member3',
                url=f'https://www.stat.go.jp/data/idou/{year}np/{section}/zuhyou/hyo1.xls'))
        for year, release in BLS_RELEASES.items():
            result.append(dict(file=f'bls_{year}.html', owner='member3',
                url=f'https://www.bls.gov/news.release/archives/srgune_{release}.htm', year=year))
    return result


def main(group, retry_failed=False):
    log = ROOT/'docs/remediation/acquisition.json'
    previous = json.loads(log.read_text(encoding='utf-8')) if log.exists() else []
    records = {r['file']:r for r in previous}
    def fetch(spec):
        path = ROOT/'data/raw'/spec['owner']/spec['file']
        record = dict(spec)
        if spec['file'] in records:
            record['previous_attempts']=[records[spec['file']]]
        try:
            if spec.get('original_cache') and (ROOT/spec['original_cache']).exists() and not path.exists():
                original=ROOT/spec['original_cache']
                if digest(original)!=spec['sha256']: raise ValueError('Original cache identity mismatch')
                path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(original,path)
                record['cache_origin']=spec['original_cache']
                record['original_acquisition_manifest']='analysis/member4/audit/download_manifest.json'
            record.update(acquire(spec['url'], path, ROOT/'data/raw', spec.get('sha256')))
            record['path']=path.relative_to(ROOT).as_posix()
        except Exception as error:
            record.update(status='unavailable', error=f'{type(error).__name__}: {error}', online_reverified=False)
        print(spec['file'],record['status'],flush=True)
        return record
    # Retain previous acquisition evidence rather than redownload unchanged cached files.
    todo=[s for s in source_specs(group) if s['file'] not in records or
          (records[s['file']]['status']!='unavailable' and not (ROOT/'data/raw'/s['owner']/s['file']).exists()) or
          (retry_failed and records[s['file']]['status']=='unavailable')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for record in pool.map(fetch,todo): records[record['file']]=record
    log.parent.mkdir(parents=True,exist_ok=True)
    log.write_text(json.dumps(list(records.values()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--group',choices=['all','member1','member3'],default='all')
    parser.add_argument('--retry-failed',action='store_true')
    args=parser.parse_args();main(args.group,args.retry_failed)
