"""Assemble the additive v2 poster from its declared local input snapshots."""
from pathlib import Path
import csv
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / 'content.json').read_text(encoding='utf-8'))
CLAIMS = []


def write(name, value):
    (HERE / name).write_text(value, encoding='utf-8', newline='\n')


def claim(key, file, where, field, fmt='.3f', scale=1):
    path = HERE / 'inputs' / file
    with path.open(encoding='utf-8', newline='') as f:
        rows = [r for r in csv.DictReader(f) if all(r[k] == str(v) for k, v in where.items())]
    if len(rows) != 1:
        raise ValueError(f'Ambiguous saved result: {key}')
    value = float(rows[0][field])
    display = format(value * scale, fmt)
    CLAIMS.append({'id': key, 'input': 'inputs/' + file, 'selection': where, 'field': field,
                   'raw_value': value, 'scale': scale, 'format': fmt, 'display': display,
                   'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return f'<span data-claim="{key}">{display}</span>'


def migration(key, country, year=2022, age='20-24', variant='primary'):
    return claim(key, 'migration_associations.csv', {'country': country, 'year': year, 'age_group': age, 'variant': variant}, 'pearson')


def figure(stem):
    original = (HERE / 'figures' / f'{stem}.svg').read_text(encoding='utf-8')
    start = original.index('<svg')
    text = original[start:]
    ids = re.findall(r'\bid="([^"]+)"', text)
    for ident in sorted(ids, key=len, reverse=True):
        text = text.replace(f'id="{ident}"', f'id="{stem}__{ident}"').replace(f'href="#{ident}"', f'href="#{stem}__{ident}"').replace(f'url(#{ident})', f'url(#{stem}__{ident})')
    text = re.sub(r'(<svg\b[^>]*?)\bwidth="[^"]+"', r'\1width="100%"', text, count=1)
    text = re.sub(r'(<svg\b[^>]*?)\bheight="[^"]+"', r'\1height="100%"', text, count=1)
    text = text.replace('<svg ', f'<svg role="img" aria-label="{stem}" ', 1)
    ET.fromstring(text)
    return f'<a class="chart" data-figure="{stem}" href="figures/{stem}.svg">{text}</a>'


def tables():
    mfg = []
    for group, name in [('Pooled', 'Pooled (98)'), ('USA', 'USA (51)'), ('JPN', 'Japan (47)')]:
        values = [claim(f'mfg_{group}_{year}', 'manufacturing_associations.csv',
                        {'year': year, 'group': group, 'variant': 'available', 'x': 'age65_share_pct', 'y': 'manufacturing_share_pct'}, 'pearson') for year in [2019, 2022]]
        mfg.append(f'<tr><th scope="row">{name}</th><td>{values[0]}</td><td>{values[1]}</td></tr>')
    mfg_html = '<table class="evidence-table manufacturing-table"><caption>Pearson r · equal-region weighting</caption><thead><tr><th>Sample (n)</th><th>2019</th><th>2022</th></tr></thead><tbody>' + ''.join(mfg) + '</tbody></table>'
    older = []
    for country, name in [('JPN', 'Japan (47)'), ('USA', 'USA (51)')]:
        values = [migration(f'older_{country}_{year}', country, year, age='65+') for year in [2019, 2022]]
        older.append(f'<tr><th scope="row">{name}</th><td>{values[0]}</td><td>{values[1]}</td></tr>')
    older_html = '<table class="evidence-table older-table"><caption>65+ migration rate vs aging · Pearson r</caption><thead><tr><th>Country (n)</th><th>2019</th><th>2022</th></tr></thead><tbody>' + ''.join(older) + '</tbody></table>'
    return mfg_html, older_html


def build():
    CLAIMS.clear()
    inputs = json.loads((HERE / 'input_manifest.json').read_text(encoding='utf-8'))
    for row in inputs:
        if hashlib.sha256((HERE / row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Input changed: ' + row['path'])
    mfg_table, older_table = tables()
    cov = claim('between_covariance_2022', 'covariance.csv', {'year': 2022}, 'between_fraction', '.1f', 100)
    jp19 = migration('young_JPN_2019', 'JPN', 2019)
    us19 = migration('young_USA_2019', 'USA', 2019)
    no_tokyo = migration('young_JPN_without_Tokyo', 'JPN', variant='without_Tokyo')
    no_dc = migration('young_USA_without_DC', 'USA', variant='without_DC')
    older_no_tokyo = migration('older_JPN_without_Tokyo', 'JPN', age='65+', variant='without_Tokyo')
    uncertain = claim('us_young_intervals_cross_zero', 'uncertainty.csv', {'country': 'USA', 'year': 2022, 'age_group': '20-24'}, 'intervals_including_zero', '.0f')
    tokyo = {key: claim('tokyo_' + key, 'tokyo_decomposition.csv', {'year': 2022}, field, '+,.0f')
             for key, field in [('teen', 'age15_19_net'), ('young', 'age20_24_net'), ('other', 'all_other_ages_net'), ('older', 'age65plus_net')]}
    authors = ''.join(f'<div class="author"><strong data-size-role="author">{html.escape(a["name"])}</strong><span data-size-role="student-id">{a["student_id"]}</span></div>' for a in CONFIG['authors'])
    figs = {stem: figure(stem) for stem in ['A_national', 'B_distribution', 'C_manufacturing_trend', 'D_aggregation', 'E_young_migration', 'F_tokyo']}
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Aging Across Economies - Poster v2</title><link rel="stylesheet" href="poster.css"></head>
<body><div class="screen-tools"><b>VERSION 2 · READY FOR TEAM REVIEW</b><span>A0 portrait · local vector poster</span><button id="scale-toggle">View at 100%</button><button onclick="window.print()">Print / save PDF</button></div>
<main class="poster">
<header class="masthead">
<div class="hero"><h1><span data-size-role="title-first">AGING ACROSS</span><span class="economies" data-size-role="title-second">ECONOMIES</span></h1>
<div class="research-question"><div class="course" data-size-role="affiliation">Data Visualization<br>City University of Hong Kong</div><p class="eyebrow">RESEARCH QUESTION</p><p class="question">How do regional economic structure and age-selective migration relate to population aging in Japan and the United States?</p></div></div>
<p class="subtitle" data-size-role="subtitle">Demographic Change, Regional Structure, and Age-Selective Migration<br>in Japan and the United States</p>
<div class="authors">{authors}</div>
</header>
<section class="study-design" aria-label="Study design">
<div class="scope-row"><p><b>National context</b> 2000-2022</p><p><b>Regional population / manufacturing</b> 2011-2022</p><p><b>Association / migration snapshots</b> 2019 &amp; 2022</p></div>
<div class="definition-row"><p><b>Aging:</b> residents aged 65+ as a share of all residents.</p><p><b>Manufacturing:</b> nominal value added / nominal regional GDP.</p><p><b>Migration:</b> inflows minus outflows, per 1,000 same-age residents.</p></div>
<div class="design-bottom"><p>98 regions: 50 U.S. states + DC; 47 prefectures. Equal-region Pearson / Spearman; Tokyo / DC and leave-one-out sensitivities; ACS uncertainty retained.</p><div class="country-key"><span><i class="us"></i>United States</span><span><i class="jp"></i>Japan</span></div></div>
</section>
<section class="population-section science-band">
<div class="population-copy"><h2 data-size-role="section-heading"><span>1</span> Shared aging,<br>uneven regions</h2>
<p class="text" data-size-role="body">Both countries aged over 2000-2022, with Japan at a higher level. Yet national trajectories conceal broad regional variation. The complete 2022 distribution establishes differences within each country; it does not make a state equivalent to a prefecture or identify the causes of aging.</p>
<p class="note">National UN estimates and regional Census / Japan estimates use different methods. Regional medians are not population-weighted national rates.</p></div>
<figure><figcaption class="figure-title"><b>A</b> National aging, 2000-2022</figcaption>{figs['A_national']}<p class="caption" data-size-role="caption">Historical estimates, both sexes. A common national source shows the two trajectories; regional data are kept separate.</p></figure>
<figure><figcaption class="figure-title"><b>B</b> All-region distribution, 2022</figcaption>{figs['B_distribution']}<p class="caption">Every region is shown. Labels mark country minima/maxima. Bar: median; band: middle 50%. Vertical offsets only separate dots.</p></figure>
</section>
<section class="economic-section science-band"><h2 data-size-role="section-heading"><span>2</span> Economic structure and aggregation</h2>
<div class="economic-grid"><div class="economic-context">
<figure><figcaption class="figure-title"><b>C</b> Manufacturing share, 2011-2022</figcaption>{figs['C_manufacturing_trend']}<p class="caption">Lines: regional medians. Bands: interquartile ranges, not confidence intervals. Nominal GDP shares, not employment shares; U.S. CY / Japan FY.</p></figure>
<p class="text">The pooled association is positive, but within-country linear associations are close to zero in both snapshots. Country differences dominate the pooled pattern. This does not establish that manufacturing is irrelevant, rule out nonlinear relationships, or show that all confounders have been controlled.</p>
<p class="covariance-note"><b>{cov}% of 2022 pooled covariance</b> corresponds to between-country group-mean differences.<br><span>Covariance accounting, not explained variance or a causal contribution.</span></p>
</div><div class="aggregation-evidence"><figure><figcaption class="figure-title"><b>D</b> Pooled versus within-country · 2022</figcaption>{figs['D_aggregation']}</figure>{mfg_table}</div></div>
</section>
<section class="migration-section science-band"><h2 data-size-role="section-heading"><span>3</span> Age-selective migration reveals opposing balances</h2>
<div class="migration-grid"><div class="migration-evidence">
<figure><figcaption class="figure-title"><b>E</b> Young-adult migration and aging · ages 20-24</figcaption>{figs['E_young_migration']}<p class="caption">Approximate 90% U.S. ratio intervals include denominator uncertainty; unavailable covariances are omitted. Hollow points include zero ({uncertain}/51); filled points exclude zero. Country scales differ.</p></figure>
<p class="text">Japan's young-adult association is strong and negative; the U.S. pattern is weaker and DC-sensitive. Age-selective balances add demographic detail, but a year's migration flow does not explain the accumulated age structure. Survey residence changes and registered migration events are distinct measures.</p>
<p class="sensitivity-note">2019 r: Japan {jp19}, USA {us19}. In 2022, without Tokyo: {no_tokyo}; without DC: {no_dc}.</p>
<div class="older-evidence">{older_table}<p class="note">Descriptive point summaries, not uncertainty-adjusted differences. Japan's 2022 65+ r becomes {older_no_tokyo} without Tokyo; older-adult patterns are not stable across years.</p></div>
</div><div class="tokyo-evidence"><figure><figcaption class="figure-title"><b>F</b> Tokyo: what the total conceals</figcaption>{figs['F_tokyo']}<p class="caption">JP-13, all nationalities; registered inter-prefectural events. In 2022, ages 15-19 ({tokyo['teen']}) and 20-24 ({tokyo['young']}) outweigh all other ages ({tokyo['other']}), which already include 65+ ({tokyo['older']}). Net counts, not rates; motives unmeasured.</p></figure></div></div>
</section>
<footer>
<section class="key-findings"><h3>Key Findings</h3><div class="finding-grid"><p><b>01</b> Shared aging coexists with substantial regional variation.</p><p><b>02</b> The pooled aging-manufacturing relationship is not a shared within-country pattern.</p><p><b>03</b> Young-adult migration is strongly associated with aging in Japan; the U.S. pattern is weaker and more uncertain.</p></div></section>
<section class="limitations"><h3>Limitations</h3><div><p>Descriptive evidence, not causal effects. Japanese rates are constructed from rounded population denominators; the 2019 official-rate table and exact age-reference day remain unverified.</p><p>ACS sampling error, spatial dependence and shared denominators complicate interpretation. Population dates differ (U.S. July / Japan October); GDP uses CY / FY. Two snapshots do not establish every year's pattern.</p></div></section>
<div class="sources"><p><b>Sources:</b> UN WPP2024; U.S. Census / Japan Population Estimates; BEA SAGDP2 / Cabinet Office; Japan Internal Migration Table 3; ACS 1-year B07001 / B07401. Exact inputs and full figures: accompanying manifest.</p><span>VERSION 2<br>READY FOR TEAM REVIEW</span></div>
</footer>
</main><script>
let fit = true;
function fitPoster() {{ document.documentElement.style.setProperty('--screen-scale', fit ? Math.min(1, (innerWidth - 32) / (841 * 96 / 25.4)) : 1); document.getElementById('scale-toggle').textContent = fit ? 'View at 100%' : 'Fit to width'; }}
document.getElementById('scale-toggle').onclick = () => {{ fit = !fit; fitPoster(); }};
window.addEventListener('resize', fitPoster); fitPoster();
</script></body></html>'''
    write('poster.html', page)
    manifest = {'status': 'READY FOR TEAM REVIEW', 'version': 2, 'inputs': inputs,
                'figures': json.loads((HERE / 'figure_manifest.json').read_text(encoding='utf-8')),
                'numerical_claims': CLAIMS,
                'study_scopes': {'national': '2000-2022, 46 observed country-years',
                                 'regional_population_manufacturing': '2011-2022 context; associations only 2019 and 2022',
                                 'association_samples_each_year': {'USA': 51, 'JPN': 47, 'pooled_manufacturing_only': 98}},
                'appendix': json.loads((HERE / 'appendix_manifest.json').read_text(encoding='utf-8')),
                'analytical_policy': 'Saved results only; exact native bins; no new models, pooled migration, services or causal estimation.'}
    write('content_manifest.json', json.dumps(manifest, indent=2) + '\n')
    print(f'Built v2 HTML; {len(CLAIMS)} source-mapped numerical claims, six complete figure exports.')


if __name__ == '__main__':
    build()
