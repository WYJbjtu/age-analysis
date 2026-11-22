"""Validate the assembled poster, copied vectors and unchanged repository inputs.

Read-only outside this new draft directory. Does not run analytical pipelines,
change reviewed locks, fetch sources, or regenerate expected scientific results.
Requires pypdf as declared in this draft's requirements.txt.
"""
from pathlib import Path
import csv
import hashlib
import json
import locale
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NS = 'http://www.w3.org/2000/svg'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def run(args):
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True,
                          encoding='utf-8').stdout


def geometry(node):
    """Compare exact data/axis primitive attributes, excluding hoisted defs."""
    result = []
    if node.tag == f'{{{NS}}}defs':
        return result
    if node.tag.rsplit('}', 1)[-1] in {'path', 'use', 'circle', 'ellipse', 'line', 'polygon', 'polyline', 'rect'}:
        result.append((node.tag, sorted(node.attrib.items())))
    for child in node:
        result.extend(geometry(child))
    return result


def check():
    baseline = read_json('initial_state.json')
    mismatches = [row['path'] for row in baseline['protected_files']
                  if not (ROOT / row['path']).is_file()
                  or digest(ROOT / row['path']) != row['sha256']]
    if mismatches:
        raise AssertionError(f'Pre-existing file changes: {mismatches}')
    source_rows = read_json('figure_sources.json')
    for row in source_rows:
        assert digest(ROOT / row['path']) == row['sha256'], row['path']
        assert digest(HERE / row['copy']) == row['sha256'], row['copy']

    page = (HERE / 'poster.html').read_text(encoding='utf-8')
    svg_texts = re.findall(r'<svg\b.*?</svg>', page, re.S)
    views = read_json('layout_views.json')
    assert len(svg_texts) == len(views) == 10
    parsed = {ET.fromstring(s).attrib['aria-label']: s for s in svg_texts}
    panel_checks = []
    expected_markers = {'B_USA': 51, 'B_Japan': 47, 'D_pooled': 98,
                        'D_USA': 51, 'D_Japan': 47, 'E_Japan': 47, 'E_USA': 51}
    for entry in views:
        name = entry['name']
        text = parsed[name]
        ids = re.findall(r'\bid="([^"]+)"', text)
        refs = re.findall(r'(?:href="#|url\(#)([^"\)]+)', text)
        assert len(ids) == len(set(ids)), name
        assert set(refs) <= set(ids), name
        # Undo only generated ID namespaces, then compare selected source
        # graphics. Presentation text may be resized/repositioned; data may not.
        displayed = ET.fromstring(text.replace(name + '__', ''))
        original = ET.parse(HERE / entry['asset']).getroot()
        original_scope = original if entry['selected_axes'] is None else original.find(
            f'.//{{{NS}}}g[@id="axes_{entry["selected_axes"]}"]')
        groups = [g for g in original_scope.iter(f'{{{NS}}}g')
                  if re.fullmatch(r'(?:PathCollection|PolyCollection|LineCollection|line2d|patch)_\d+', g.attrib.get('id', ''))]
        for group in groups:
            counterpart = displayed.find(f'.//{{{NS}}}g[@id="{group.attrib["id"]}"]')
            assert counterpart is not None, (name, group.attrib['id'])
            assert geometry(group) == geometry(counterpart), (name, group.attrib['id'])
        collections = [g for g in displayed.iter(f'{{{NS}}}g')
                       if re.fullmatch(r'PathCollection_\d+', g.attrib.get('id', ''))]
        markers = sum(len(list(g.iter(f'{{{NS}}}use'))) for g in collections)
        if name in expected_markers:
            assert markers == expected_markers[name], (name, markers)
        if name == 'F_Tokyo':
            labels = {t.text for t in displayed.iter(f'{{{NS}}}text')}
            assert {f'{age}-{age+4}' for age in range(0, 90, 5)} | {'90+', 'Age unknown', '2019', '2022'} <= labels
        panel_checks.append({'view': name, 'source_graphic_groups_compared': len(groups),
                             'unchanged_geometry': True, 'scatter_markers': markers,
                             'unresolved_references': 0})

    local_links = re.findall(r'(?:href|src)="([^"#]+)"', re.sub(r'<svg\b.*?</svg>', '', page, flags=re.S))
    for link in local_links:
        assert not link.startswith(('http:', 'https:', 'file:')), link
        assert (HERE / link).is_file(), link
    css = (HERE / 'poster.css').read_text(encoding='utf-8')
    for asset in re.findall(r"url\('([^']+)'\)", css):
        assert (HERE / asset).is_file(), asset

    metrics = read_json('layout_check.json')
    for file, sha in metrics['rendered_input_sha256'].items():
        assert digest(HERE / file) == sha, 'Render is stale: ' + file
    assert digest(HERE / 'poster.pdf') == metrics['pdf_sha256'], 'PDF is stale'
    for key in ['duplicate_svg_ids', 'unresolved_svg_references', 'sibling_overlaps', 'javascript_errors', 'blocked_remote_requests']:
        assert metrics[key] == [], key
    assert all(f['status'] == 'loaded' for f in metrics['loaded_fonts'])
    assert metrics['key_findings'] == 3
    assert metrics['svg_views'] == 10
    config = read_json('content.json')
    assert metrics['author_names'] == [a['name'] for a in config['authors']]
    for col in metrics['columns']:
        assert col['scrollHeight'] <= col['clientHeight'] + 1, col['class']
        assert col['lastChildBottom'] <= col['bottom'] + 1, col['class']
        assert col['bottom'] < metrics['footer']['y'], col['class']
    assert metrics['footer']['bottom'] < metrics['poster']['bottom']

    claims = read_json('claim_checks.json')
    rendered = {r['id']: r['text'] for r in metrics['claims']}
    for claim in claims:
        p = ROOT / claim['path']
        assert digest(p) == claim['source_sha256']
        with p.open(encoding='utf-8', newline='') as f:
            rows = [r for r in csv.DictReader(f) if all(r[k] == str(v) for k, v in claim['selection'].items())]
        assert len(rows) == 1
        assert float(rows[0][claim['field']]) == claim['source_value']
        assert rendered[claim['id']] == claim['display']
    assert len(rendered) == len(claims)

    pdf = PdfReader(HERE / 'poster.pdf')
    assert len(pdf.pages) == 1
    pdf_page = pdf.pages[0]
    width_mm, height_mm = [float(x) * 25.4 / 72 for x in
                           (pdf_page.mediabox.width, pdf_page.mediabox.height)]
    assert abs(width_mm - 841) < .2 and abs(height_mm - 1189) < .2
    pdf_text = pdf_page.extract_text()
    assert not any(a.get_object().get('/Subtype') == '/Link' for a in pdf_page.get('/Annots', []))
    for author in config['authors']:
        assert author['name'] in pdf_text and author['student_id'] in pdf_text
    assert 'READY FOR TEAM REVIEW' in pdf_text
    assert 'Key Findings' in pdf_text and 'Limitations' in pdf_text
    assert (HERE / 'poster.preview.png').is_file()
    # Build-created text is UTF-8/LF; copied original source bytes are exempt.
    for p in HERE.iterdir():
        if p.is_file() and p.suffix in {'.py', '.json', '.html', '.css', '.md', '.txt'}:
            raw = p.read_bytes()
            raw.decode('utf-8')
            assert b'\r' not in raw, p.name
    branch = run(['git', 'branch', '--show-current']).strip()
    head = run(['git', 'rev-parse', 'HEAD']).strip()
    assert branch == baseline['branch'] and head == baseline['head']
    report = {
        'status': 'PASS - assembled poster checks',
        'draft_status': 'READY FOR TEAM REVIEW',
        'python': sys.version, 'locale_encoding': locale.getencoding(),
        'utf8_mode': sys.flags.utf8_mode,
        'branch': branch, 'head': head, 'git_status': run(['git', 'status', '--short']).splitlines(),
        'protected_original_files_unchanged': len(baseline['protected_files']),
        'source_figures_copied_byte_for_byte': len(source_rows),
        'rendered_claims_matched_saved_results': len(claims),
        'panels': panel_checks,
        'pdf': {'pages': 1, 'width_mm': width_mm, 'height_mm': height_mm, 'file_links': 0,
                'sha256': digest(HERE / 'poster.pdf')},
        'preview_sha256': digest(HERE / 'poster.preview.png'),
        'fonts_loaded': True, 'asset_links_resolve': True,
        'layout_overflows': 0, 'layout_sibling_overlaps': 0,
        'no_page_network_requests': True,
        'scope': 'Poster assembly only; no statistical recomputation or shared-lock update.'
    }
    (HERE / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ['status', 'protected_original_files_unchanged',
        'source_figures_copied_byte_for_byte', 'rendered_claims_matched_saved_results', 'pdf']}, indent=2))


if __name__ == '__main__':
    check()
