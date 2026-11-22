"""Check source fidelity, complete samples, actual PDF type and layout.

This validator writes only qa/validation.json in this new draft. --standalone
checks the declared deliverable bundle without claiming repository-baseline access.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import locale
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pypdf import PdfReader
import pdfplumber

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NS = 'http://www.w3.org/2000/svg'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def validate(standalone=False):
    manifest = read_json('input_manifest.json')
    for item in manifest:
        local = HERE / item['path']
        assert digest(local) == item['sha256'], item['path']
        assert len(rows(local)) == item['rows']
        if not standalone:
            source = ROOT / item['source_path']
            assert digest(source) == item['source_sha256'], item['source_path']
            if isinstance(item['selection'], dict):
                selected = [r for r in rows(source) if all(r[k] in values for k, values in item['selection'].items())]
                assert selected == rows(local), item['path']
            else:
                assert source.read_bytes() == local.read_bytes()
    for font in read_json('font_manifest.json'):
        assert digest(HERE / font['path']) == font['sha256']
    for item in read_json('appendix_manifest.json'):
        assert digest(HERE / item['path']) == item['source_sha256']
        if not standalone:
            assert digest(ROOT / item['source_path']) == item['source_sha256']
    before = read_json('initial_state.json')
    original_count = None
    if not standalone:
        for item in before['protected_files']:
            assert (ROOT / item['path']).is_file() and digest(ROOT / item['path']) == item['sha256'], item['path']
        original_count = len(before['protected_files'])
        for args, expected in [(['branch', '--show-current'], before['branch']), (['rev-parse', 'HEAD'], before['head'])]:
            assert subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True, encoding='utf-8').stdout.strip() == expected

    population = rows(HERE / 'inputs/population_2022.csv')
    ids = {c: {r['region_id'] for r in population if r['country'] == c} for c in ['USA', 'JPN']}
    assert len(population) == 98 and len(ids['USA']) == 51 and len(ids['JPN']) == 47
    assert ids['JPN'] == {f'JP-{n:02d}' for n in range(1, 48)}
    assert 'US-DC' in ids['USA'] and all(re.fullmatch(r'US-[A-Z]{2}', x) for x in ids['USA'])
    migration = rows(HERE / 'inputs/migration.csv')
    assert len({(r['country'], r['region_id'], r['year'], r['age_group']) for r in migration}) == len(migration)
    for year in ['2019', '2022']:
        for age in ['20-24', '65+']:
            for country in ['USA', 'JPN']:
                group = [r for r in migration if r['country'] == country and r['year'] == year and r['age_group'] == age]
                assert {r['region_id'] for r in group} == ids[country]
                for r in group:
                    assert all(r[k] != '' for k in ['age65_share_pct', 'net_per_1000_same_age', 'age_population'])
                    assert float(r['age_population']) > 0
                    assert float(r['net_migration']) == float(r['in_migration']) - float(r['out_migration'])
                    assert math.isclose(float(r['net_per_1000_same_age']), 1000 * float(r['net_migration']) / float(r['age_population']), rel_tol=1e-12, abs_tol=1e-10)

    layout = read_json('qa/layout.json')
    for name, sha in layout['input_sha256'].items():
        assert digest(HERE / name) == sha, 'Stale rendering: ' + name
    assert digest(HERE / 'poster.pdf') == layout['pdf_sha256']
    for field in ['overlaps', 'text_overflows', 'duplicate_ids', 'unresolved_svg_references', 'javascript_errors', 'blocked_requests']:
        assert layout[field] == [], field
    assert all(font['status'] == 'loaded' for font in layout['loaded_fonts'])
    assert layout['key_findings'] == 3
    for section in layout['sections']:
        assert section['scrollHeight'] <= section['clientHeight'] + 1, section['name']
        assert section['right'] <= layout['poster']['right'] and section['bottom'] <= layout['poster']['bottom']
    config = read_json('content.json')
    assert layout['author_names'] == [a['name'] for a in config['authors']]
    assert layout['author_ids'] == [a['student_id'] for a in config['authors']]
    figures = read_json('figure_manifest.json')
    chart_boxes = {r['id']: r for r in layout['charts']}
    for item in figures:
        bounds = chart_boxes[item['id']]
        assert abs(bounds['width'] * 25.4 / 96 - item['width_mm']) < .1
        assert abs(bounds['height'] * 25.4 / 96 - item['height_mm']) < .1
    page = (HERE / 'poster.html').read_text(encoding='utf-8')
    for local in re.findall(r'href="(?!#)([^"#]+)"', page):
        assert not re.match(r'(https?|file):', local) and (HERE / local).is_file(), local
    for font in re.findall(r"url\('([^']+)'\)", (HERE / 'poster.css').read_text(encoding='utf-8')):
        assert (HERE / font).is_file()

    rendered_claims = {r['id']: r['text'] for r in layout['claims']}
    content = read_json('content_manifest.json')
    assert len(content['numerical_claims']) == len(rendered_claims)
    for claim in content['numerical_claims']:
        source = HERE / claim['input']
        assert digest(source) == claim['input_sha256']
        selected = [r for r in rows(source) if all(r[k] == str(v) for k, v in claim['selection'].items())]
        assert len(selected) == 1
        value = float(selected[0][claim['field']])
        assert value == claim['raw_value']
        assert rendered_claims[claim['id']] == format(value * claim['scale'], claim['format'])
    counts = {}
    for stem, expected in [('B_distribution', 98), ('D_aggregation', 196), ('E_young_migration', 98)]:
        svg = ET.parse(HERE / 'figures' / f'{stem}.svg').getroot()
        collections = [g for g in svg.iter(f'{{{NS}}}g') if re.fullmatch(r'PathCollection_\d+', g.attrib.get('id', ''))]
        count = sum(len(list(g.iter(f'{{{NS}}}use'))) for g in collections)
        assert count == expected, (stem, count)
        counts[stem] = count
    checks = {r['figure']: r for r in read_json('figure_checks.json')}
    for c in checks.values():
        assert c['text_outside_canvas'] == []
    for stem, source_name, selectors, group_key in [
        ('D_aggregation', 'manufacturing_associations.csv',
         {'year': '2022', 'variant': 'available', 'x': 'age65_share_pct', 'y': 'manufacturing_share_pct'}, 'group'),
        ('E_young_migration', 'migration_associations.csv',
         {'year': '2022', 'age_group': '20-24', 'variant': 'primary'}, 'country'),
    ]:
        saved = rows(HERE / 'inputs' / source_name)
        svg_text = ' '.join(ET.parse(HERE / 'figures' / f'{stem}.svg').getroot().itertext())
        for panel in checks[stem]['panels']:
            selected = [r for r in saved if r[group_key] == panel[group_key]
                        and all(r[k] == v for k, v in selectors.items())]
            assert len(selected) == 1
            for field in ['pearson', 'spearman']:
                assert math.isclose(panel[field], float(selected[0][field]), abs_tol=1e-14)
                assert f'{panel[field]:.3f}' in svg_text
            if stem == 'D_aggregation':
                for field in ['slope', 'intercept']:
                    assert panel[field + '_from_saved_result'] == float(selected[0][field])
    for country, group in checks['B_distribution']['countries'].items():
        assert set(group['region_ids']) == ids[country]
    us = next(r for r in checks['E_young_migration']['panels'] if r['country'] == 'USA')
    assert us['hollow_points'] == 35 and us['error_bars'] == 51
    assert us['y_limits'][0] < us['interval_min'] and us['y_limits'][1] > us['interval_max']
    for year in checks['F_tokyo']['years']:
        assert year['bars'] == 20 and year['sum_native_and_unknown'] == year['published_total']

    reader = PdfReader(HERE / 'poster.pdf')
    assert len(reader.pages) == 1
    pdf_page = reader.pages[0]
    width, height = [float(v) * 25.4 / 72 for v in [pdf_page.mediabox.width, pdf_page.mediabox.height]]
    assert abs(width - 841) < .2 and abs(height - 1189) < .2
    assert not any(a.get_object().get('/Subtype') == '/Link' for a in pdf_page.get('/Annots', []))
    runs = []
    def collect(text, cm, tm, font, size):
        if text.strip():
            # Compose text and current matrices, including rotations. A rotated
            # glyph's bounding-box height is NOT its effective font size.
            scale = math.hypot(cm[0] * tm[0] + cm[2] * tm[1], cm[1] * tm[0] + cm[3] * tm[1])
            runs.append({'text': text.strip(), 'font_size_pt': size * scale})
    extracted = pdf_page.extract_text(visitor_text=collect)
    def size_of(text):
        found = [r['font_size_pt'] for r in runs if r['text'] == text]
        assert found, 'Text missing from actual PDF: ' + text
        return found[0]
    def size_starting(text):
        found = [r['font_size_pt'] for r in runs if r['text'].startswith(text)]
        assert found, text
        return found[0]
    actual_type = {'title_first': size_of('AGING ACROSS'), 'title_second': size_of('ECONOMIES'),
                   'authors': {a['name']: size_of(a['name']) for a in config['authors']},
                   'student_ids': {a['student_id']: size_of(a['student_id']) for a in config['authors']},
                   'subtitle': size_of('Demographic Change, Regional Structure, and Age-Selective Migration'),
                   'section_heading': size_of('Economic structure and aggregation'),
                   'explanatory_body': size_starting('Both countries aged over'),
                   'caption': size_starting('Historical estimates, both sexes.'),
                   'plot_axis_label': size_of('Residents aged 65+ (%)'),
                   'plot_source_note': size_of('UN WPP2024 Estimates; both sexes; July 1.')}
    for key, target in [('title_first', 106), ('title_second', 116), ('subtitle', 29), ('section_heading', 34), ('explanatory_body', 24), ('caption', 20), ('plot_axis_label', 20), ('plot_source_note', 18)]:
        assert abs(actual_type[key] - target) < .05, (key, actual_type[key])
    assert all(abs(v - 32) < .05 for v in actual_type['authors'].values())
    assert all(abs(v - 21) < .05 for v in actual_type['student_ids'].values())
    assert min(r['font_size_pt'] for r in runs) >= 17.9
    for phrase in ['Covariance accounting', 'not explained variance', 'same-age', 'Hollow points', '35/51', 'constructed', 'unverified', 'JP-13', 'Unknown', 'READY FOR TEAM REVIEW']:
        assert phrase in extracted, phrase
    with pdfplumber.open(HERE / 'poster.pdf') as pdf:
        chars = pdf.pages[0].chars
        char_bounds = {'left_pt': min(c['x0'] for c in chars), 'right_pt': max(c['x1'] for c in chars),
                       'top_pt': min(c['top'] for c in chars), 'bottom_pt': max(c['bottom'] for c in chars)}
        assert char_bounds['left_pt'] > 16 * 72 / 25.4
        assert char_bounds['right_pt'] < float(pdf_page.mediabox.width) - 16 * 72 / 25.4
        assert char_bounds['top_pt'] > 16 * 72 / 25.4
        assert char_bounds['bottom_pt'] < float(pdf_page.mediabox.height) - 16 * 72 / 25.4
    report = {'status': 'PASS', 'mode': 'standalone declared bundle' if standalone else 'repository and draft',
              'python': sys.version, 'locale_encoding': locale.getencoding(), 'utf8_mode': sys.flags.utf8_mode,
              'protected_files_unchanged': original_count, 'source_snapshots_verified': len(manifest),
              'numerical_claims_verified': len(rendered_claims), 'svg_marker_counts': counts,
              'us_young_uncertainty': us, 'tokyo_native_reconciliation': checks['F_tokyo']['years'],
              'page': {'pages': 1, 'width_mm': width, 'height_mm': height},
              'effective_pdf_type_pt': actual_type, 'minimum_effective_type_pt': min(r['font_size_pt'] for r in runs),
              'pdf_character_bounds': char_bounds, 'non_chart_body_words': layout['non_chart_body_words'],
              'pdf_sha256': digest(HERE / 'poster.pdf'), 'overflows': 0, 'overlaps': 0,
              'fonts_loaded': True, 'network_requests': 0, 'print_scaling': 'native A0, no fit-to-smaller-page scaling'}
    (HERE / 'qa/validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ['status', 'protected_files_unchanged', 'numerical_claims_verified', 'page', 'effective_pdf_type_pt']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standalone', action='store_true')
    validate(parser.parse_args().standalone)
