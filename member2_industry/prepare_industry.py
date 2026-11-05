"""Reproduce Member 2's CY/FY2022 industry table from pinned official sources.

Uses only the Python standard library. US rows are verified and preserved;
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
JP_SHEET = '2022（令和4）年度'
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


def japan_rows(cells, summary):
    for cell, expected in {'I5': '製造業', 'BL5': '県内総生産', 'BO7': '第３次産業'}.items():
        if cells.get(cell) != expected:
            raise ValueError(f'Unexpected Japanese source layout: {cell}')
    if '2022' not in cells.get('B3', '') or '100万円' not in cells.get('R3', ''):
        raise ValueError('Japanese source year or monetary unit changed')
    if str(summary.get('O5')) != '2022':
        raise ValueError('GDP cross-check table is not FY2022')
    gdp_checks = {str(summary[f'A{r}']).zfill(2): number(summary[f'O{r}'])
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
            raise ValueError(f'GDP cross-check failed for JP-{code}')
        service_gap = services - sum(get(col) for col in SERVICES)
        accounting_gap = gdp - (get('BI') + get('BJ') - get('BK'))
        # Published components rounded to JPY millions; allow accumulated rounding.
        if abs(service_gap) > 6 or abs(accounting_gap) > 2:
            raise ValueError(f'Component reconciliation failed for JP-{code}')
        result.append({
            'country': 'JPN', 'region_id': f'JP-{code}', 'year': '2022',
            'manufacturing_share_pct': f'{100 * manufacturing / gdp:.10f}',
            'services_share_pct': f'{100 * services / gdp:.10f}',
            'nominal_gdp_local': f'{gdp:.0f}',
            'manufacturing_va_local': f'{manufacturing:.0f}',
            'services_va_local': f'{services:.0f}', 'gdp_reference_period': 'FY2022',
        })
        audit.append({'region_id': f'JP-{code}', 'source_row': int(row),
                      'region_name_ja': cells[f'B{row}'],
                      'gdp_matches_summary': True,
                      'services_rounding_gap_jpy_million': service_gap,
                      'gdp_rounding_gap_jpy_million': accounting_gap})
    if seen != {f'{n:02d}' for n in range(1, 48)}:
        raise ValueError('Expected exactly 47 prefectures; no cities or national totals')
    return sorted(result, key=lambda r: r['region_id']), audit


def verify_us(rows, lookup):
    with ZipFile(RAW / 'SAGDP.zip') as archive:
        filename = 'SAGDP2__ALL_AREAS_1997_2025.csv'
        records = list(csv.DictReader(io.StringIO(archive.read(filename).decode('utf-8-sig'))))
    values = {(r['GeoName'], r['LineCode']): r['2022'] for r in records
              if r.get('LineCode') in ('1', '12', '92')}
    names = {r['region_id']: r['region_name'] for r in lookup if r['country'] == 'USA'}
    current = [r for r in rows if r['country'] == 'USA' and r['year'] == '2022']
    if len(current) != 51 or {r['region_id'] for r in current} != set(names):
        raise ValueError('Expected existing 51 USA rows for CY2022')
    for row in current:
        name = names[row['region_id']]
        amounts = [number(values[name, line]) for line in ('1', '12', '92')]
        for column, expected in zip(('nominal_gdp_local', 'manufacturing_va_local', 'services_va_local'), amounts):
            if not math.isclose(number(row[column]), expected, abs_tol=0.00001, rel_tol=0):
                raise ValueError(f'US source mismatch: {name}/{column}')
        for column, amount in zip(('manufacturing_share_pct', 'services_share_pct'), amounts[1:]):
            if not math.isclose(number(row[column]), 100 * amount / amounts[0], abs_tol=1e-7, rel_tol=0):
                raise ValueError(f'US share mismatch: {name}/{column}')
        if row['gdp_reference_period'] != 'CY2022':
            raise ValueError(f'US reference period mismatch: {name}')
    return len(current)


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
    headers, current = read_csv(path)
    _, lookup = read_csv(ROOT / 'data/reference/region_lookup.csv')
    count = verify_us(current, lookup)
    japanese, audit = japan_rows(xlsx_cells(RAW / 'syuyo1.xlsx', JP_SHEET),
                                xlsx_cells(RAW / 'soukatu1.xlsx', '実数'))
    # Re-running replaces only our Japanese 2022 rows, retaining all other values.
    retained = [r for r in current if not (r['country'] == 'JPN' and r['year'] == '2022')]
    output = sorted(retained + japanese, key=lambda r: (r['country'], r['region_id'], r['year']))
    temporary = path.with_suffix('.csv.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator='\n')
        writer.writeheader()
        writer.writerows(output)
    validate_table(temporary, 'industry', read_lookup(ROOT / 'data/reference/region_lookup.csv'))
    temporary.replace(path)
    (MODULE / 'validation.json').write_text(json.dumps({
        'usa_rows_reverified': count, 'jpn_rows_added_or_refreshed': len(japanese),
        'jpn_gdp_crosschecks_passed': len(audit), 'jpn_checks': audit,
        'services_cross_country_comparable': False,
        'source_manifest': 'source_manifest.json',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'USA: {count} official-source checks passed; JPN: {len(japanese)} prefectures validated.')
    print('Service definitions differ: use separate country panels; no pooled service comparison.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Download missing pinned source files')
    main(parser.parse_args().download)
