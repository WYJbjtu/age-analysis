"""Pure parsers for official archived BLS annual tables; no import-time I/O."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib, json, re
import pandas as pd

RELEASES={2011:'02292012',2012:'03012013',2013:'02282014',2014:'03042015',
          2015:'02262016',2016:'02282017',2017:'02272018',2018:'02282019',
          2019:'03042020',2020:'03032021',2021:'03022022',2022:'03012023'}


class TableText(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('tr','p','pre','caption','h1','h2','h3'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('td','th'):self.parts.append(' | ')
        elif tag in ('tr','p','pre','caption'):self.parts.append('\n')
    def handle_data(self,data):self.parts.append(data)


def parse_annual_table(text,year,name_to_id,previous=False):
    """Use the published annual column, never an average of rounded monthly rates."""
    if '<html' in text.lower():
        parser=TableText();parser.feed(text);text=''.join(parser.parts)
    text=re.sub(r'^L\d+:\s?', '', text,flags=re.M)
    start=re.search(r'Table\s+1\.\s+Employment status',text,re.I)
    if not start: raise ValueError(f'{year}: annual table 1 is missing')
    section=text[start.start():]
    end=re.search(r'Table\s+2\.',section,re.I)
    if end:section=section[:end.start()]
    if str(year) not in section[:1500] or 'thousands' not in section[:1500].lower():
        raise ValueError(f'{year}: table year/units missing')
    rows=[]
    for line in section.splitlines():
        for name,rid in name_to_id.items():
            match=re.match(r'^\s*'+re.escape(name)+r'(?=[.\s|])',line)
            if not match:continue
            tail=re.sub(r'\([a-zA-Z]+\)','',line[match.end():])
            values=re.findall(r'(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?',tail)
            if len(values)<10:raise ValueError(f'{year}: truncated annual row {rid}')
            values=[float(v.replace(',','')) for v in values]
            offset=0 if previous else 1
            rows.append(dict(country='USA',region_id=rid,year=year-1 if previous else year,
                civilian_population_16plus=int(values[offset]*1000),labor_force=int(values[2+offset]*1000),
                employment=int(values[4+offset]*1000),unemployment=int(values[6+offset]*1000),
                unemployment_rate_pct=values[8+offset],source_release='srgune_'+RELEASES[year]))
            break
    frame=pd.DataFrame(rows)
    if len(frame)!=len(name_to_id) or frame.region_id.nunique()!=len(name_to_id):
        raise ValueError(f'{year}: expected {len(name_to_id)} unique states/DC, found {len(frame)}')
    if set(frame.region_id)!=set(name_to_id.values()):raise ValueError('BLS geography mismatch')
    return frame.sort_values('region_id').reset_index(drop=True)


def parse_employment_population_ratio(text,year,name_to_id):
    """Published Table 2 rate; denominator is civilian noninstitutional 16+."""
    if '<html' in text.lower():
        parser=TableText();parser.feed(text);text=''.join(parser.parts)
    text=re.sub(r'^L\d+:\s?', '', text,flags=re.M)
    match=re.search(r'Table\s+2\.\s+Employment-population ratios',text,re.I)
    if not match:raise ValueError('BLS Table 2 missing')
    section=text[match.start():]
    if str(year) not in section[:700] or '[Percent]' not in section[:700]:
        raise ValueError('BLS Table 2 year/units missing')
    values={}
    for line in section.splitlines():
        for name,rid in name_to_id.items():
            match=re.match(r'^\s*'+re.escape(name)+r'(?=[.\s|])',line)
            if match:
                numbers=re.findall(r'[-+]?\d+(?:\.\d+)?',line[match.end():])
                if len(numbers)<2:raise ValueError('Truncated BLS employment-population row')
                if rid in values:raise ValueError('Duplicate BLS employment-population row')
                values[rid]=float(numbers[1]);break
    if set(values)!=set(name_to_id.values()):raise ValueError('Incomplete employment-population ratios')
    return values


def load_archives(raw,snapshot_dir,lookup):
    names=lookup.loc[lookup.country=='USA'].set_index('region_name').region_id.to_dict()
    pinned=json.loads((snapshot_dir/'manifest.json').read_text(encoding='utf-8'))
    records={r['year']:r for r in pinned['files']}
    current=[];previous=[];evidence=[]
    for year in RELEASES:
        path=raw/f'bls_{year}.html';kind='raw official HTML'
        if path.exists():
            log=Path(__file__).resolve().parents[1]/'docs/remediation/acquisition.json'
            acquisition={r['file']:r for r in json.loads(log.read_text(encoding='utf-8'))}
            evidence_row=acquisition.get(path.name,{})
            if (evidence_row.get('status') not in ('retrieved','cached') or
                evidence_row.get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest() or
                evidence_row.get('url')!=f'https://www.bls.gov/news.release/archives/srgune_{RELEASES[year]}.htm'):
                raise ValueError(f'Unverified BLS raw cache: {year}')
        else:
            path=snapshot_dir/f'bls_{year}_web.txt';kind='official-page text captured by web reader'
            if hashlib.sha256(path.read_bytes()).hexdigest()!=records[year]['sha256']:
                raise ValueError(f'BLS snapshot changed: {year}')
        text=path.read_text(encoding='utf-8')
        frame=parse_annual_table(text,year,names)
        # Retain the previous detail table's 2022 field without inventing older rates.
        if year==2022:
            frame['employment_population_ratio_pct']=frame.region_id.map(parse_employment_population_ratio(text,year,names))
        current.append(frame)
        previous.append(parse_annual_table(text,year,names,previous=True))
        evidence.append(dict(year=year,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            url=f'https://www.bls.gov/news.release/archives/srgune_{RELEASES[year]}.htm',
            input_type=kind,scope='all 51 states/DC; published current and prior annual columns'))
    return pd.concat(current,ignore_index=True),pd.concat(previous,ignore_index=True),evidence


def parse_m13(payload):
    """Optional API validation: annual M13 is mandatory; ignore monthly values."""
    result={}
    for series in payload.get('Results',{}).get('series',[]):
        annual={int(v['year']):float(v['value']) for v in series['data'] if v['period']=='M13'}
        if not annual:raise ValueError('Official annual M13 missing; monthly averaging is not equivalent')
        result[series['seriesID']]=annual
    if not result:raise ValueError('No official annual series')
    return result
