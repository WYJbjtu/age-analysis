from pathlib import Path
import requests, concurrent.futures, hashlib, json, datetime
ROOT=Path(__file__).resolve().parents[1]
URLS={
 'census_sc_est2022_alldata6.csv':'https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/asrh/sc-est2022-alldata6.csv',
 'BEA_SAGDP.zip':'https://apps.bea.gov/regional/zip/SAGDP.zip',
 'census_states_2022.zip':'https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip',
 'census_nst_est2022_all.csv':'https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/totals/NST-EST2022-ALLDATA.csv',
 'census_sc_est2022_layout.pdf':'https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2022/sc-est2022-alldata6.pdf',
 'census_nst_est2022_layout.pdf':'https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2022/NST-EST2022-ALLDATA.pdf',
}
def fetch(item):
 name,url=item
 p=ROOT/'raw'/name
 if not p.exists():
  r=requests.get(url,timeout=180);r.raise_for_status();p.write_bytes(r.content)
 rec={'file':str(p),'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 print(name,rec['bytes'],flush=True)
 return rec
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  records=list(pool.map(fetch,URLS.items()))
 (ROOT/'raw/source_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
