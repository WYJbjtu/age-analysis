"""Build the audience-facing three-column poster and its evidence appendix."""
from pathlib import Path
import csv
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
CLAIMS = []


def read_json(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def read_rows(name):
    with (HERE / 'inputs' / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def write(name, text):
    (HERE / name).write_text(text, encoding='utf-8', newline='\n')


def claim(key, file, where, field, fmt='.3f', scale=1):
    path = HERE / 'inputs' / file
    rows = [r for r in read_rows(file) if all(r[k] == str(v) for k, v in where.items())]
    if len(rows) != 1:
        raise ValueError(f'Ambiguous saved result: {key}')
    value = float(rows[0][field]); display = format(value * scale, fmt)
    CLAIMS.append({'id': key, 'input': 'inputs/' + file, 'selection': where, 'field': field,
                   'raw_value': value, 'scale': scale, 'format': fmt, 'display': display,
                   'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return f'<span data-claim="{key}">{display}</span>'


def migration(key, country, year=2022, variant='primary'):
    return claim(key, 'migration_associations.csv', {'country': country, 'year': year, 'age_group': '20-24', 'variant': variant}, 'pearson')


def figure(stem):
    source = (HERE / 'figures' / f'{stem}.svg').read_text(encoding='utf-8')
    text = source[source.index('<svg'):]
    for ident in sorted(re.findall(r'\bid="([^"]+)"', text), key=len, reverse=True):
        text = text.replace(f'id="{ident}"', f'id="{stem}__{ident}"').replace(f'href="#{ident}"', f'href="#{stem}__{ident}"').replace(f'url(#{ident})', f'url(#{stem}__{ident})')
    text = re.sub(r'(<svg\b[^>]*?)\bwidth="[^"]+"', r'\1width="100%"', text, count=1)
    text = re.sub(r'(<svg\b[^>]*?)\bheight="[^"]+"', r'\1height="100%"', text, count=1)
    text = text.replace('<svg ', f'<svg role="img" aria-label="{stem}" ', 1)
    ET.fromstring(text)
    return f'<a class="chart" data-figure="{stem}" href="figures/{stem}.svg">{text}</a>'


def appendix():
    specifications = [
        ('Manufacturing association, both years', 'manufacturing_associations.csv',
         ['year', 'group', 'n', 'pearson', 'spearman'], lambda r: r['variant'] == 'available' and r['x'] == 'age65_share_pct' and r['y'] == 'manufacturing_share_pct'),
        ('All saved migration comparisons and sensitivities', 'migration_associations.csv',
         ['country', 'year', 'age_group', 'variant', 'eligible', 'included', 'missing', 'pearson', 'spearman'], lambda r: True),
        ('Industry medians and regional quartiles', 'industry_trends.csv',
         ['country', 'year', 'regions', 'manufacturing_q1_pct', 'manufacturing_median_pct', 'manufacturing_q3_pct', 'services_q1_pct', 'services_median_pct', 'services_q3_pct'], lambda r: True),
    ]
    tables, inventory = [], []
    for title, filename, columns, select in specifications:
        rows = [r for r in read_rows(filename) if select(r)]
        assert rows
        columns = [c for c in columns if c in rows[0]]
        thead = ''.join('<th>' + html.escape(c) + '</th>' for c in columns)
        tbody = ''.join('<tr>' + ''.join('<td>' + html.escape(r[c]) + '</td>' for c in columns) + '</tr>' for r in rows)
        tables.append(f'<h2>{title}</h2><p>Exact saved values: <a href="../inputs/{filename}">{filename}</a></p><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>')
        inventory.append({'title': title, 'input': 'inputs/' + filename, 'rows': len(rows), 'columns': columns, 'format': 'Original CSV cell strings, no numerical recalculation'})
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Supplementary evidence</title><style>
body{font:16px/1.5 Georgia,serif;margin:32px;color:#241e1a;background:#faf7ef}h1,h2{color:#9c3029}table{border-collapse:collapse;font:13px/1.4 Arial,sans-serif}td,th{padding:6px 9px;border:1px solid #ccbfb4;text-align:right}th{background:#eee3d6}p{max-width:1000px}a{color:#2788ae}
</style></head><body><h1>Supplementary evidence</h1>
<p>These are existing validated result tables. Equal-region weights; migration countries remain separate. The 65+ and complete year-comparison results are retained here so that the main poster can prioritize readable plots.</p>
<p>Older-adult coefficients are descriptive point summaries, not survey-uncertainty-adjusted country differences. Japan's 2022 65+ result is sensitive to Tokyo; the older-adult pattern is not stable across years. ACS ratio intervals use available MOEs and omit unavailable covariances, including numerator-denominator covariance. Estimates from the same survey are not known to be independent.</p>
<p>Japan's migration rates are constructed from official population estimates rounded to 1,000 persons. The 2019 denominator uses the original annual vintage, while the primary aging stock uses Member 1's revised vintage. The 2019 official-rate table and exact Japanese migration age-reference day remain unverified. ACS uses residence changes over the preceding year and age at interview; Japan uses calendar-year registration events, which can count repeated moves. These are not harmonized event measures.</p>
<p>U.S. private services include utilities but exclude government and government enterprises. Japan's published tertiary aggregate includes utilities, public administration, education and health/social services. The separate trends do not authorize a pooled service analysis, cross-country service gap, combined ranking or harmonized service definition. Manufacturing is nominal manufacturing value added divided by same-region, same-period nominal GDP, not employment share.</p>
<p>The covariance decomposition uses denominator N throughout and country weights 51/98 and 47/98. It is covariance accounting, not explained variance or causation. One year's migration flow cannot account for the accumulated stock of aging, and two snapshots do not establish all panel years.</p>
<p><a href="full_regional_ranking.svg">Full original regional ranking</a> · <a href="full_native_cases.svg">Full original native-age cases</a></p>
''' + ''.join(tables) + '</body></html>'
    write('appendix/evidence_tables.html', page)
    return inventory


def build():
    CLAIMS.clear()
    config, inputs = read_json('content.json'), read_json('input_manifest.json')
    for row in inputs:
        assert hashlib.sha256((HERE / row['path']).read_bytes()).hexdigest() == row['sha256']
    assert read_json('inputs/industry_comparability.json')['services_pooled_status'] == 'BLOCKED'
    authors = ''.join(f'<div class="author"><strong data-size-role="author">{html.escape(a["name"])}</strong><span data-size-role="student-id">{a["student_id"]}</span></div>' for a in config['authors'])
    titles = [html.escape(t) for t in config['title']]
    subtitle = '<br>'.join(html.escape(t) for t in config['subtitle'])
    figs = {r['id']: figure(r['id']) for r in read_json('figure_manifest.json')}
    cov = claim('between_covariance_2022', 'covariance.csv', {'year': 2022}, 'between_fraction', '.1f', 100)
    mfg19 = [claim('mfg_' + group + '_2019', 'manufacturing_associations.csv', {'year': 2019, 'group': group, 'variant': 'available', 'x': 'age65_share_pct', 'y': 'manufacturing_share_pct'}, 'pearson') for group in ['Pooled', 'USA', 'JPN']]
    jp19, us19 = migration('young_JPN_2019', 'JPN', 2019), migration('young_USA_2019', 'USA', 2019)
    no_tokyo, no_dc = migration('young_without_Tokyo', 'JPN', variant='without_Tokyo'), migration('young_without_DC', 'USA', variant='without_DC')
    uncertain = claim('us_intervals_cross_zero', 'uncertainty.csv', {'country': 'USA', 'year': 2022, 'age_group': '20-24'}, 'intervals_including_zero', '.0f')
    tokyo = {key: claim('tokyo_' + key, 'tokyo_decomposition.csv', {'year': 2022}, field, '+,.0f') for key, field in [('teen', 'age15_19_net'), ('young', 'age20_24_net'), ('other', 'all_other_ages_net'), ('older', 'age65plus_net')]}
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Aging Across Economies</title><link rel="stylesheet" href="poster.css"></head>
<body><div class="screen-tools"><b>Aging Across Economies</b><span>A0 portrait</span><button id="scale-toggle">View at 100%</button><button onclick="window.print()">Print / save PDF</button></div>
<main class="poster">
<header class="masthead"><div class="hero"><h1><span data-size-role="title-first">{titles[0]}</span><span class="economies" data-size-role="title-second">{titles[1]}</span></h1>
<div class="course" data-size-role="affiliation">{html.escape(config['course'])}<br>{html.escape(config['affiliation'])}</div></div>
<p class="subtitle" data-size-role="subtitle">{subtitle}</p><div class="authors">{authors}</div></header>
<div class="columns">
<section class="column population-column" data-column="1" aria-label="Background, data, and aging">
<h2 data-size-role="column-heading">BACKGROUND &amp; DATA</h2>
<div class="background-data"><p class="text" data-size-role="body">Population aging is shared by Japan and the United States, but national averages can conceal distinct regional patterns. We examine how population age structure relates to industrial composition and age-selective domestic migration, distinguishing differences between countries from variation within them.</p>
<p class="text"><span class="data-label">Data.</span> We cover 51 U.S. state-level regions and 47 Japanese prefectures. National trends span 2000-2022; regional population and industry panels span 2011-2022. Association and migration comparisons use 2019 and 2022. Sources include UN WPP2024, U.S. Census/ACS, Japan's Statistics Bureau/e-Stat, BEA and Japan's Cabinet Office.</p></div>
<figure><figcaption class="figure-title"><b>A</b> National aging, 2000-2022</figcaption>{figs['A_national']}<p class="caption" data-size-role="caption">Historical estimates: residents aged 65+ as a share of the all-age population.</p></figure>
<figure><figcaption class="figure-title"><b>B</b> Regional aging distribution, 2022</figcaption>{figs['B_distribution']}<p class="caption">All 98 regions. Bar: median; band: IQR. Horizontal offsets separate dots. Labels identify each country's minimum and maximum.</p></figure>
<p class="text population-interpretation">Both countries aged, with Japan at a higher level, while regional variation remains substantial. UN national estimates and regional official estimates use distinct methods; equal-region medians are not population-weighted national rates. These distributions describe administrative units, rather than causes of aging.</p>
</section>
<section class="column industry-column" data-column="2" aria-label="Industrial structure">
<h2 data-size-role="column-heading">INDUSTRIAL STRUCTURE</h2>
<figure><figcaption class="figure-title"><b>C</b> Manufacturing shares, 2011-2022</figcaption>{figs['C_manufacturing']}<p class="caption">Regional medians and IQR; nominal manufacturing value added / GDP; U.S. CY / Japan FY.</p></figure>
<figure><figcaption class="figure-title"><b>D</b> Service-sector trends, 2011-2022</figcaption>{figs['D_services']}<p class="caption">Country-specific definitions; interpret trends within each country.</p></figure>
<figure><figcaption class="figure-title"><b>E</b> Aging and manufacturing, 2022</figcaption>{figs['E_aggregation']}</figure>
<p class="text industry-interpretation">Manufacturing medians moved in different directions over the panel. Services also changed within each country, under distinct definitions. For manufacturing, the positive pooled association is not reproduced as a strong linear relationship within either country under equal-region weighting.</p>
<p class="evidence-note">2019 Pearson r: pooled {mfg19[0]}; USA {mfg19[1]}; Japan {mfg19[2]}.</p>
<p class="covariance-note"><b>{cov}%</b> of 2022 pooled covariance corresponds to between-country mean differences.<small>Covariance accounting, not explained variance or causation.</small></p>
</section>
<section class="column migration-column" data-column="3" aria-label="Migration, Tokyo, and key findings">
<h2 data-size-role="column-heading">AGE-SELECTIVE MIGRATION</h2>
<figure><figcaption class="figure-title"><b>F</b> Young adults, ages 20-24 · 2022</figcaption>{figs['F_young_migration']}<p class="caption">Net = inflows minus outflows. U.S. bars: approximate 90% ratio intervals, including denominator uncertainty; unavailable covariances omitted. Hollow points include zero ({uncertain}/51); filled points exclude it. Country scales differ. Japan: constructed rates with rounded population denominators.</p></figure>
<p class="robustness">2019 Pearson r: Japan {jp19}, USA {us19}. In 2022, without Tokyo: {no_tokyo}; without DC: {no_dc}.</p>
<figure><figcaption class="figure-title"><b>G</b> Tokyo: what the total conceals</figcaption>{figs['G_tokyo']}<p class="caption">Registered inter-prefectural moves; all nationalities, both sexes. Native age groups and unknown age retained.</p></figure>
<p class="tokyo-interpretation">In 2022, ages 15-19 ({tokyo['teen']}) and 20-24 ({tokyo['young']}) outweighed all other ages ({tokyo['other']}, already including 65+: {tokyo['older']}). Total net migration conceals opposing age balances; one year's flows do not explain the accumulated age structure.</p>
<section class="key-findings"><h3>KEY FINDINGS</h3><div class="findings-list">
<p><b>01</b><span>Both countries are aging, with substantial regional variation.</span></p>
<p><b>02</b><span>The pooled aging-manufacturing association mainly reflects between-country differences, not a shared within-country linear pattern.</span></p>
<p><b>03</b><span>Young-adult net migration is strongly negatively associated with regional aging in Japan; the U.S. pattern is weaker and more uncertain.</span></p>
</div></section>
</section>
</div>
<footer class="footnote"><p>Timing: U.S. population July 1 / Japan October 1; GDP U.S. CY / Japan FY (April-March). Associations are descriptive, not causal effects. Two snapshots do not establish every year's pattern.</p></footer>
</main><script>
let fit = true;
function fitPoster() {{ document.documentElement.style.setProperty('--screen-scale', fit ? Math.min(1, (innerWidth - 32) / (841 * 96 / 25.4)) : 1); document.getElementById('scale-toggle').textContent = fit ? 'View at 100%' : 'Fit to width'; }}
document.getElementById('scale-toggle').onclick = () => {{ fit = !fit; fitPoster(); }};
window.addEventListener('resize', fitPoster); fitPoster();
</script></body></html>'''
    write('poster.html', page)
    supplementary = appendix()
    manifest = {'version': 3, 'status': 'READY FOR TEAM REVIEW', 'layout': config['layout'], 'inputs': inputs,
                'figures': read_json('figure_manifest.json'), 'numerical_claims': CLAIMS,
                'source_provenance': read_json('provenance_manifest.json'), 'original_appendices': read_json('appendix_manifest.json'),
                'supplementary_tables': supplementary, 'supplementary_path': 'appendix/evidence_tables.html',
                'service_scope': read_json('inputs/industry_comparability.json'),
                'analytical_policy': 'Existing validated results only; no new models; no pooled services or migration.',
                'visible_content_exclusions': ['version and workflow status', 'header time-window boxes', 'header methods strip', 'duplicate research question', 'full coefficient tables', 'optional 65+ table'],
                'study_scopes': {'national': '2000-2022: 46 observed country-years', 'regional': '2011-2022: 1176 region-years', 'main_associations_and_migration': '2019 and 2022: 51 USA + 47 JPN each year'}}
    write('content_manifest.json', json.dumps(manifest, indent=2) + '\n')
    print(f'Built three-column HTML, seven figure groups, {len(CLAIMS)} mapped poster claims and evidence appendix.')


if __name__ == '__main__':
    build()
