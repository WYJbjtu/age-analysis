"""Independent official-source checks for the previously unassessed Member 1 components."""
from pathlib import Path
import argparse,io,json,sys,zipfile,xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parents[1];MEMBER=ROOT/'member1_demographics'
sys.path.insert(0,str(ROOT/'src'))
from aging_economies.source_io import digest


def verify_national(raw):
    path=raw/'wpp_ages.xlsx'
    pin=next(r for r in json.loads((MEMBER/'population_source_manifest.json').read_text()) if r['file']==path.name)
    if digest(path)!=pin['sha256']:raise ValueError('WPP release identity differs; do not silently change versions')
    book=load_workbook(path,read_only=True,data_only=True);sheet=book['Estimates'];sheet.reset_dimensions()
    records=[];header=None;metadata=[]
    try:
        for index,row in enumerate(sheet.iter_rows(values_only=True),1):
            if index<17:
                metadata.extend(str(v) for v in row if v is not None);continue
            if index==17:header={name:j for j,name in enumerate(row) if name is not None};continue
            if row[header['ISO3 Alpha-code']] not in ('USA','JPN'):continue
            country=row[header['ISO3 Alpha-code']];year=int(row[header['Year']])
            if not 2000<=year<=2022:continue
            if row[header['Variant']]!='Estimates':raise ValueError('Projection entered historical series')
            if int(row[header['Location code']])!={'USA':840,'JPN':392}[country]:raise ValueError('UN country-code mismatch')
            if row[header['Total']]!=100:raise ValueError('Percentage denominator not per 100 total population')
            records.append(dict(country=country,year=year,age65_share_pct=float(row[header['65+']]),
                working_age_share_pct=float(row[header['15-64']]),age0_14_share_pct=float(row[header['0-14']]),
                un_location_code=int(row[header['Location code']]),total_percentage=float(row[header['Total']]),
                source_row=index,variant='Estimates'))
    finally:book.close()
    if not any('both sexes' in s.lower() for s in metadata):raise ValueError('Sex coverage not established')
    official=pd.DataFrame(records).sort_values(['country','year'])
    if len(official)!=46 or official.duplicated(['country','year']).any():raise ValueError('Incomplete UN extract')
    if not np.allclose(official.age65_share_pct+official.working_age_share_pct+official.age0_14_share_pct,100,atol=1e-8,rtol=0):
        raise ValueError('Nonoverlapping UN age groups do not sum to total')
    checks=[]
    for filename in ['source_snapshots/wpp2024_selected_estimates.csv','national_trends_wpp2024_2000_2022.csv']:
        existing=pd.read_csv(MEMBER/filename)
        pairs=official.merge(existing,on=['country','year'],validate='one_to_one',suffixes=('_source','_saved'))
        if len(pairs)!=46:raise ValueError('Saved national coverage differs')
        for row in pairs.itertuples():
            for field in ['age65_share_pct','working_age_share_pct','age0_14_share_pct']:
                difference=getattr(row,field+'_saved')-getattr(row,field+'_source')
                checks.append(dict(file=filename,country=row.country,year=row.year,field=field,
                                   official=getattr(row,field+'_source'),saved=getattr(row,field+'_saved'),
                                   difference=difference,passed=abs(difference)<=1e-8))
    if not all(r['passed'] for r in checks):raise ValueError('National source discrepancy requires numerical repair')
    pd.DataFrame(checks).to_csv(MEMBER/'national_source_checks.csv',index=False,float_format='%.12f')
    official.to_csv(MEMBER/'national_source_extract.csv',index=False,float_format='%.12f')
    return dict(status='PASS',source_url=pin['url'],sha256=pin['sha256'],source_sheet='Estimates',
        rows=46,field_checks=len(checks),max_difference=max(abs(r['difference']) for r in checks),
        definition='Published WPP2024 percentage: both-sex de facto population aged 65+ / total de facto population, July 1, per 100 population.',
        numerator_and_denominator='The source is a percentage product (F06), not a population-count product. Total column is 100; 0-14, 15-64 and 65+ partition it. No regional-mean substitute or invented count is used.',
        metadata_url='https://population.un.org/dataportal/data/indicators/71/locations/180/start/2024/end/2024/metadata',
        estimate_status='2000-2022 are historical Estimates; no projection rows used',independent_count_reconstruction='NOT EVALUATED; original product publishes percentages')


def verify_maps(raw):
    import shapefile
    from pyproj import Transformer
    path=raw/'census_states_2022.zip'
    expected='fb2c327c32869dc27bee7a6e0e6130f9d936c4f85638b8414af799f1251e3816'
    if digest(path)!=expected:raise ValueError('Original 2022 boundary identity differs')
    lookup=pd.read_csv(ROOT/'data/reference/region_lookup.csv').query("country=='USA'").set_index('region_id')
    values=pd.read_csv(ROOT/'data/processed/demographics.csv').query("country=='USA' and year==2022")
    industry=pd.read_csv(ROOT/'data/processed/industry.csv').query("country=='USA' and year==2022").set_index('region_id')
    plotted=pd.read_csv(ROOT/'handover/us_2022/processed/us_states_2022_core.csv',dtype={'region_code':str}).set_index('region_code')
    if len(plotted)!=51 or not plotted.index.is_unique:raise ValueError('Original map data keys are not unique')
    if values.region_id.nunique()!=51 or values.age65_share_pct.isna().any():raise ValueError('Missing map values')
    with zipfile.ZipFile(path) as archive:
        stem='cb_2022_us_state_20m'
        reader=shapefile.Reader(shp=io.BytesIO(archive.read(stem+'.shp')),
            shx=io.BytesIO(archive.read(stem+'.shx')),dbf=io.BytesIO(archive.read(stem+'.dbf')))
        records=[]
        for item in reader.iterShapeRecords():
            attributes=item.record.as_dict();rid='US-'+attributes['STUSPS']
            if rid not in lookup.index:continue
            if attributes['NAME']!=lookup.loc[rid,'region_name']:raise ValueError('Boundary name/code mismatch')
            if not item.shape.points or not np.isfinite(np.array(item.shape.points)).all():raise ValueError('Invalid geometry')
            original=plotted.loc[str(attributes['STATEFP'])]
            aging=float(values.set_index('region_id').loc[rid,'age65_share_pct'])
            manufacturing=float(industry.loc[rid,'manufacturing_share_pct'])
            if original.region_name!=attributes['NAME']:raise ValueError('Original FIPS/name join differs')
            if abs(original.aging_rate_pct-aging)>1e-8 or abs(original.manufacturing_share_pct-manufacturing)>1e-8:
                raise ValueError('Original plotted values differ from validated canonical inputs')
            crs={'US-AK':'EPSG:3338','US-HI':'EPSG:3759','US-DC':'EPSG:26918'}.get(rid,'EPSG:5070')
            transform=Transformer.from_crs('EPSG:4269',crs,always_xy=True)
            parts=list(item.shape.parts)+[len(item.shape.points)]
            for start,end in zip(parts,parts[1:]):
                points=np.asarray(item.shape.points[start:end])
                if len(points)<3 or not np.isfinite(transform.transform(points[:,0],points[:,1])).all():
                    raise ValueError('Geometry projection loses a polygon part')
            records.append(dict(region_id=rid,fips=str(attributes['STATEFP']),parts=len(item.shape.parts),
                vertices=len(item.shape.points),inset={'US-AK':'Alaska','US-HI':'Hawaii','US-DC':'DC'}.get(rid,'main'),
                value=aging,manufacturing_share_pct=manufacturing,original_value_checks=True,projection_parts_valid=True))
        metadata=ET.fromstring(archive.read(stem+'.shp.iso.xml'))
        restrictions=[' '.join(el.itertext()).strip() for el in metadata.iter()
                      if any(v in el.tag for v in ['useLimitation','otherConstraints','accessConstraints'])]
    table=pd.DataFrame(records)
    if len(table)!=51 or table.region_id.nunique()!=51 or set(table.region_id)!=set(lookup.index):raise ValueError('Map coverage/join failure')
    if table.inset.value_counts().to_dict()!={'main':48,'Alaska':1,'Hawaii':1,'DC':1}:raise ValueError('Inset coverage failure')
    table.sort_values('region_id').to_csv(MEMBER/'boundary_join_checks.csv',index=False,float_format='%.10f')
    return dict(status='PASS WITH LIMITATIONS',source='Census 2022 cartographic state boundaries, 1:20,000,000',
        url='https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip',sha256=expected,
        regions=51,main=48,insets=['Alaska','Hawaii','DC'],unmatched=0,duplicate_region_records=0,
        original_map_values_verified=102,projected_parts_all_valid=True,
        multipart_regions=int((table.parts>1).sum()),multipart_handling='Multiple polygon parts belong to one state observation.',
        copyright='US Census public-domain data; cite Census. Boundary metadata restrictions retained below.',
        restrictions=restrictions,scale='Single normalization for each metric across main map and all insets; missing values never become zero.',
        limitations='Generalized small-scale boundaries omit some small features; inset scales differ. No Japanese boundary map exists in this repository; use the existing 47-prefecture ranked chart.',
        japan_map_status='NOT APPLICABLE: no existing Japanese boundary asset or map generator')


def main(raw):
    result={'national':verify_national(raw),'maps':verify_maps(raw)}
    (MEMBER/'independent_verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('UN: 46 national rows / 276 source-field comparisons passed. US boundaries: 51 unique region joins passed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--raw-dir',type=Path,default=ROOT/'data/raw/member1')
    main(parser.parse_args().raw_dir)
