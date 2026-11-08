"""Reproduce Member 2's 2011–2022 industry panel from pinned official sources.

Uses only the Python standard library; all years come from the same source vintage.
Japan services are the published tertiary aggregate, NOT harmonized US services.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import posixpath
import re
import sys
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'member2_industry'
RAW = ROOT / 'data/raw/member2'
sys.path.insert(0, str(ROOT / 'src'))
from aging_economies.contracts import read_lookup, validate_table

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
YEARS = tuple(range(2011, 2023))
BEA_TABLE = 'SAGDP2__ALL_AREAS_1997_2025.csv'
FIELDS = ('country', 'region_id', 'year', 'manufacturing_share_pct',
          'services_share_pct', 'nominal_gdp_local', 'manufacturing_va_local',
          'services_va_local', 'gdp_reference_period')
SERVICES = ('AD', 'AH', 'AP', 'AQ', 'AR', 'AU', 'AV', 'AY', 'AZ', 'BA', 'BB', 'BC')


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def xlsx_cells(path, sheet_name):
    """Read published values, excluding phonetic annotations in Japanese text."""
    with ZipFile(path) as archive:
        def plain_text(element):
            return ''.join(t.text or '' for t in
                           element.findall('s:t', NS) + element.findall('s:r/s:t', NS))

        strings = [plain_text(si) for si in
                   ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        sheet = next(s for s in book.find('s:sheets', NS) if s.get('name') == sheet_name)
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next(r.get('Target') for r in relationships
                      if r.get('Id') == sheet.get(f'{{{REL}}}id'))
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        cells = {}
        for cell in ET.fromstring(archive.read(target)).findall('.//s:sheetData/s:row/s:c', NS):
            value = cell.find('s:v', NS)
            if cell.get('t') == 'inlineStr':
                cells[cell.get('r')] = plain_text(cell.find('s:is', NS))
            elif value is not None and value.text is not None:
                cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text
        return cells


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f'Non-finite source value: {value}')
    return result


def japan_rows(cells, summary, year):
    for cell, expected in {'I5': '製造業', 'BL5': '県内総生産', 'BO7': '第３次産業'}.items():
        if cells.get(cell) != expected:
            raise ValueError(f'Unexpected Japanese source layout: {cell}')
    if f'【{year}（' not in cells.get('B3', '') or '100万円' not in cells.get('R3', ''):
        raise ValueError('Japanese source year or monetary unit changed')
    year_columns = [address[:-1] for address, value in summary.items()
                    if re.fullmatch(r'[A-Z]+5', address) and str(value) == str(year)]
    if len(year_columns) != 1:
        raise ValueError(f'GDP cross-check table must have exactly one FY{year} column')
    column = year_columns[0]
    gdp_checks = {str(summary[f'A{r}']).zfill(2): number(summary[f'{column}{r}'])
                  for r in range(7, 54)}
    result, audit, seen = [], [], set()
    for address, code in cells.items():
        if not re.fullmatch(r'A\d+', address) or not re.fullmatch(r'\d{2}', str(code)):
            continue
        if not 1 <= int(code) <= 47:
            continue
        if code in seen:
            raise ValueError(f'Duplicate prefecture {code}')
        seen.add(code)
        row = address[1:]
        get = lambda column: number(cells[f'{column}{row}'])
        gdp, manufacturing, services = get('BL'), get('I'), get('BO')
        if gdp <= 0 or min(manufacturing, services) < 0 or manufacturing + services > gdp:
            raise ValueError(f'Invalid GDP components for JP-{code}')
        if gdp != gdp_checks[code]:
            raise ValueError(f'GDP cross-check failed for JP-{code}/{year}')
        service_gap = services - sum(get(col) for col in SERVICES)
        accounting_gap = gdp - (get('BI') + get('BJ') - get('BK'))
        # Published components rounded to JPY millions; allow accumulated rounding.
        if abs(service_gap) > 6 or abs(accounting_gap) > 2:
            raise ValueError(f'Component reconciliation failed for JP-{code}/{year}')
        result.append({
            'country': 'JPN', 'region_id': f'JP-{code}', 'year': str(year),
            'manufacturing_share_pct': f'{100 * manufacturing / gdp:.10f}',
            'services_share_pct': f'{100 * services / gdp:.10f}',
            'nominal_gdp_local': f'{gdp:.0f}',
            'manufacturing_va_local': f'{manufacturing:.0f}',
            'services_va_local': f'{services:.0f}', 'gdp_reference_period': f'FY{year}',
        })
        audit.append({'region_id': f'JP-{code}', 'year': year, 'source_row': int(row),
                      'region_name_ja': cells[f'B{row}'],
                      'gdp_matches_summary': True,
                      'services_rounding_gap_jpy_million': service_gap,
                      'gdp_rounding_gap_jpy_million': accounting_gap})
    if seen != {f'{n:02d}' for n in range(1, 48)}:
        raise ValueError('Expected exactly 47 prefectures; no cities or national totals')
    return sorted(result, key=lambda r: r['region_id']), audit


def usa_rows(records, lookup, years=YEARS):
    """Build every year directly from one pinned BEA vintage, without a seed CSV."""
    names = {r['region_id']: r['region_name'] for r in lookup if r['country'] == 'USA'}
    descriptions = {'1': 'All industry total', '12': 'Manufacturing',
                    '92': 'Private services-providing industries 3/'}
    source_rows = {}
    for row in records:
        name, line = row.get('GeoName'), row.get('LineCode')
        if name not in names.values() or line not in descriptions:
            continue
        key = (name, line)
        if key in source_rows:
            raise ValueError(f'Duplicate BEA source row: {key}')
        if (row['Description'].strip() != descriptions[line]
                or row['Unit'] != 'Millions of current dollars'):
            raise ValueError(f'Unexpected BEA definition or unit: {key}')
        source_rows[key] = row
    expected = {(name, line) for name in names.values() for line in descriptions}
    if set(source_rows) != expected:
        raise ValueError('Missing BEA region or industry source rows')
    result = []
    for rid, name in sorted(names.items()):
        for year in years:
            amounts = [number(source_rows[name, line].get(str(year), ''))
                       for line in descriptions]
            gdp, manufacturing, services = amounts
            if gdp <= 0 or min(manufacturing, services) < 0 or manufacturing + services > gdp:
                raise ValueError(f'Invalid GDP components for {rid}/{year}')
            result.append({
                'country': 'USA', 'region_id': rid, 'year': str(year),
                'manufacturing_share_pct': f'{100 * manufacturing / gdp:.10f}',
                'services_share_pct': f'{100 * services / gdp:.10f}',
                'nominal_gdp_local': f'{gdp:.1f}',
                'manufacturing_va_local': f'{manufacturing:.1f}',
                'services_va_local': f'{services:.1f}', 'gdp_reference_period': f'CY{year}',
            })
    return result


def ensure_sources(download):
    manifest = json.loads((MODULE / 'source_manifest.json').read_text())
    RAW.mkdir(parents=True, exist_ok=True)
    for source in manifest:
        path = RAW / source['file']
        if not path.exists() and download:
            pending = path.with_suffix(path.suffix + '.tmp')
            with urlopen(source['url'], timeout=180) as response:
                pending.write_bytes(response.read())
            if hashlib.sha256(pending.read_bytes()).hexdigest() != source['sha256']:
                raise ValueError(f'Source vintage changed: {source["file"]}; review before using')
            pending.replace(path)
        if not path.exists():
            raise ValueError(f'Missing {path}; rerun with --download')
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Source checksum mismatch: {path}')
        with ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError(f'Corrupt archive: {path}')


def main(download=False):
    ensure_sources(download)
    path = ROOT / 'data/processed/industry.csv'
    headers, current = read_csv(path) if path.exists() else (list(FIELDS), [])
    _, lookup = read_csv(ROOT / 'data/reference/region_lookup.csv')
    with ZipFile(RAW / 'SAGDP.zip') as archive:
        records = csv.DictReader(io.StringIO(archive.read(BEA_TABLE).decode('utf-8-sig')))
        american = usa_rows(records, lookup)
    with ZipFile(RAW / 'syuyo1.xlsx') as archive:
        sheets = ET.fromstring(archive.read('xl/workbook.xml')).find('s:sheets', NS)
        sheet_names = [sheet.get('name') for sheet in sheets]
    summary = xlsx_cells(RAW / 'soukatu1.xlsx', '実数')
    japanese, audit = [], []
    for year in YEARS:
        matches = [name for name in sheet_names if name.startswith(f'{year}（')]
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one Japanese source sheet for FY{year}')
        rows, checks = japan_rows(xlsx_cells(RAW / 'syuyo1.xlsx', matches[0]), summary, year)
        japanese.extend(rows)
        audit.extend(checks)
    expected_keys = {(r['country'], r['region_id'], str(year)) for r in lookup for year in YEARS}
    generated = american + japanese
    actual_keys = {(r['country'], r['region_id'], r['year']) for r in generated}
    if len(generated) != len(expected_keys) or actual_keys != expected_keys:
        raise ValueError('Expected the complete 98-region, 12-year industry panel')
    # Preserve records outside the requested panel, if any, without using them as inputs.
    retained = [r for r in current if (r['country'], r['region_id'], r['year']) not in expected_keys]
    output = sorted(retained + generated, key=lambda r: (r['country'], r['region_id'], int(r['year'])))
    temporary = path.with_suffix('.csv.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator='\n')
        writer.writeheader()
        writer.writerows(output)
    validate_table(temporary, 'industry', read_lookup(ROOT / 'data/reference/region_lookup.csv'))
    temporary.replace(path)
    (MODULE / 'validation.json').write_text(json.dumps({
        'years': list(YEARS), 'panel_rows': len(generated),
        'usa_rows_generated': len(american), 'jpn_rows_generated': len(japanese),
        'coverage_by_year': {str(year): {'USA': 51, 'JPN': 47} for year in YEARS},
        'jpn_gdp_crosschecks_passed': len(audit), 'jpn_checks': audit,
        'services_cross_country_comparable': False,
        'source_manifest': 'source_manifest.json',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'2011–2022: {len(american)} USA + {len(japanese)} JPN = {len(generated)} validated rows.')
    print('Service definitions differ: use separate country panels; no pooled service comparison.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Download missing pinned source files')
    main(parser.parse_args().download)
