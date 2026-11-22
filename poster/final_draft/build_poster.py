"""Assemble existing validated SVGs into a local poster; no analytical plotting."""
from pathlib import Path
import copy
import csv
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
CONFIG=json.loads((HERE/'content.json').read_text(encoding='utf-8'))


def write(path,text):
    path.write_text(text,encoding='utf-8',newline='\n')


def load_csv(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def evidence():
    records=[]
    def get(key,path,where,field,fmt,scale=1):
        found=[r for r in load_csv(path) if all(r[k]==str(v) for k,v in where.items())]
        if len(found)!=1:raise ValueError(f'Ambiguous evidence: {key}')
        raw=float(found[0][field]);display=format(raw*scale,fmt)
        records.append(dict(id=key,path=path,selection=where,field=field,source_value=raw,
            scale=scale,display=display,source_sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
        return f'<span data-claim="{key}">{display}</span>'
    migration='analysis/age_migration/results/associations.csv'
    def mig(key,country,year=2022,variant='primary'):
        return get(key,migration,dict(country=country,year=year,age_group='20-24',variant=variant),'pearson','.3f')
    values={'jp_r':mig('japan_young_r','JPN'), 'jp_no_tokyo':mig('japan_without_tokyo','JPN',variant='without_Tokyo'),
        'jp_2019':mig('japan_young_2019','JPN',2019),'us_r':mig('usa_young_r','USA'),
        'us_2019':mig('usa_young_2019','USA',2019),'us_no_dc':mig('usa_without_dc','USA',variant='without_DC')}
    values['cov']=get('between_covariance','analysis/member4/results/covariance_summary.csv',{'year':2022},'between_fraction','.1f',100)
    values['uncertain']=get('us_uncertain','analysis/age_migration/results/us_uncertainty_summary.csv',{'year':2022,'age_group':'20-24'},'intervals_including_zero','.0f')
    for key,field in [('total','total_net'),('teen','age15_19_net'),('young','age20_24_net'),('other','all_other_ages_net'),('older','age65plus_net')]:
        values[key]=get('tokyo_'+key,'analysis/age_migration/results/tokyo_decomposition.csv',{'year':2022},field,'+,.0f')
    write(HERE/'claim_checks.json',json.dumps(records,indent=2)+'\n')
    return values


VIEWS=[]


def view(asset,name,box,*,axis=None,shared_y=False,readability=False,min_font=None,legend_shift=0,css=''):
    """A viewport of source vector geometry. Only typography/reflow is adjusted."""
    src=HERE/'assets'/asset
    tree=ET.parse(src);svg=tree.getroot()
    # Matplotlib often defines shared markers inside its first axes. Hoist every
    # definition BEFORE selecting a panel so later panels retain their points.
    definitions=ET.Element(f'{{{NS}}}defs')
    definition_ids=set()
    for parent in list(svg.iter()):
        for child in list(parent):
            if child.tag==f'{{{NS}}}defs':
                for item in list(child):
                    ident=item.attrib.get('id')
                    if ident and ident in definition_ids:raise ValueError('Duplicate source definition: '+ident)
                    if ident:definition_ids.add(ident)
                    definitions.append(copy.deepcopy(item))
                parent.remove(child)
    svg.insert(0,definitions)
    if axis is not None:
        chosen=svg.find(f'.//{{{NS}}}g[@id="axes_{axis}"]')
        if chosen is None:raise ValueError('Missing source axes')
        if shared_y:
            original=svg.find(f'.//{{{NS}}}g[@id="matplotlib.axis_2"]')
            if original is None:raise ValueError('Missing original shared y axis')
            # Country panels already have their grid and tick marks. Repeat
            # only the shared text so grid strokes are not drawn twice.
            strip=ET.Element(f'{{{NS}}}g',{'id':'repeated_y_labels'})
            for group in original.iter(f'{{{NS}}}g'):
                if re.fullmatch(r'text_\d+',group.attrib.get('id','')):
                    strip.append(copy.deepcopy(group))
            shift={2:328.834160,3:657.668319}[axis]
            wrapper=ET.Element(f'{{{NS}}}g',{'transform':f'translate({shift} 0)'})
            for node in strip.iter():
                if 'id' in node.attrib:node.attrib['id']='shared_'+node.attrib['id']
            wrapper.append(strip);chosen.append(wrapper)
        for parent in svg.iter():
            for child in list(parent):
                cid=child.attrib.get('id','')
                if re.fullmatch(r'axes_\d+',cid) and child is not chosen:parent.remove(child)
    typographic_changes=0
    if readability:
        for text in svg.iter(f'{{{NS}}}text'):
            style=text.attrib.get('style','')
            found=re.search(r'font-size: ([\d.]+)px',style)
            if found and float(found[1])<=10:
                size=12 if float(found[1])>=10 else 10.4
                text.attrib['style']=style.replace(found[0],f'font-size: {size}px')
                typographic_changes+=1
    if min_font is not None:
        for node in svg.iter(f'{{{NS}}}text'):
            style=node.attrib.get('style','')
            found=re.search(r'font-size: ([\d.]+)px',style)
            if found and float(found[1])<min_font:
                node.attrib['style']=style.replace(found[0],f'font-size: {min_font}px')
                typographic_changes+=1
    if legend_shift:
        # Widen the space between existing legend entries after enlarging text.
        # Only these two legend groups move; no series or axis coordinates move.
        for ident in ['line2d_34','text_28']:
            node=svg.find(f'.//{{{NS}}}g[@id="legend_1"]/{{{NS}}}g[@id="{ident}"]')
            if node is None:raise ValueError('Manufacturing legend structure changed')
            node.attrib['transform']=f'translate({legend_shift} 0)'
        label=next(n for n in svg.iter(f'{{{NS}}}text') if n.text=='Share of nominal regional GDP (%)')
        label.attrib['transform']='translate(-14 0) '+label.attrib['transform']
    svg.attrib.update(viewBox=' '.join(map(str,box)),width='100%',height='100%',
        preserveAspectRatio='xMidYMid meet',role='img',**{'aria-label':name,'class':'source-svg'})
    # Original geometry and labels are retained; prefixes isolate SVG definitions.
    text=ET.tostring(svg,encoding='unicode')
    ids=re.findall(r'\bid="([^"]+)"',text)
    prefix=re.sub(r'\W','_',name)+'__'
    for old in sorted(ids,key=len,reverse=True):
        text=text.replace(f'id="{old}"',f'id="{prefix}{old}"').replace(f'href="#{old}"',f'href="#{prefix}{old}"').replace(f'url(#{old})',f'url(#{prefix}{old})')
    references=set(re.findall(r'(?:href="#|url\(#)([^"\)]+)',text))
    actual_ids=set(re.findall(r'\bid="([^"]+)"',text))
    if references-actual_ids:raise ValueError(f'Unresolved SVG references in {name}: {references-actual_ids}')
    if len(actual_ids)!=len(ids):raise ValueError('Duplicate SVG ids in '+name)
    VIEWS.append(dict(name=name,asset='assets/'+asset,viewBox=box,selected_axes=axis,
        shared_y_axis_duplicated=shared_y,small_text_size_adjustments=typographic_changes,
        manufacturing_second_legend_shift=legend_shift,
        shared_definitions_preserved=len(definition_ids),unresolved_svg_references=0,
        geometry_policy='Original data coordinates, paths, markers, lines and numeric axes retained; text/legend reflow only; no analytical regeneration'))
    return f'<a class="chart {css}" href="assets/{asset}" title="Open the unchanged full source figure" data-view="{name}">{text}</a>'


def build():
    # Exact copied assets must still agree with the selected validated sources.
    sources=json.loads((HERE/'figure_sources.json').read_text(encoding='utf-8'))
    for row in sources:
        for p in (ROOT/row['path'],HERE/row['copy']):
            if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Figure source changed: '+str(p))
    VIEWS.clear()
    n=evidence()
    figures={
        'A':view('national_aging.svg','A_national',[-4,49,658,317],css='national'),
        'B_US':view('regional_aging.svg','B_USA',[-25,48,550,782],axis=1,readability=True,css='ranked'),
        'B_JP':view('regional_aging.svg','B_Japan',[522,48,550,782],axis=2,readability=True,css='ranked'),
        'C':view('manufacturing_trend.svg','C_manufacturing',[12,92,864,295],min_font=13.5,legend_shift=100,css='manufacturing'),
        'D_P':view('pooled_within.svg','D_pooled',[21,64,351,307],axis=1,css='economic'),
        'D_US':view('pooled_within.svg','D_USA',[349.83416,64,351,307],axis=2,shared_y=True,css='economic'),
        'D_JP':view('pooled_within.svg','D_Japan',[678.668319,64,351,307],axis=3,shared_y=True,css='economic'),
        'E_JP':view('migration_regional.svg','E_Japan',[7,72,480,288],axis=1,css='migration'),
        'E_US':view('migration_regional.svg','E_USA',[493,72,479,288],axis=2,css='migration'),
        'F':view('migration_cases.svg','F_Tokyo',[0,81,390,593],axis=1,css='tokyo')}
    authors=''.join(f'<div class="author"><strong>{html.escape(a["name"])}</strong><span>{a["student_id"]}</span></div>' for a in CONFIG['authors'])
    page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light"><title>Aging Across Economies - poster draft</title>
<link rel="stylesheet" href="poster.css"></head><body>
<div class="screen-tools"><b>READY FOR TEAM REVIEW</b><span>A0 portrait · click any chart for its complete original SVG</span><button id="scale-toggle">View at 100%</button><button onclick="window.print()">Print / save PDF</button></div>
<main class="poster" aria-label="A0 academic poster">
<header class="masthead">
<div class="hero"><h1><span>AGING ACROSS</span><span class="economies">ECONOMIES</span></h1>
<aside class="credits"><div class="course">{CONFIG['course']}</div><div class="affiliation">{CONFIG['affiliation']}</div><div class="authors">{authors}</div></aside></div>
<p class="subtitle">{CONFIG['subtitle'][0]}<br>{CONFIG['subtitle'][1]}</p>
<p class="takeaway">{CONFIG['takeaway']}</p>
<div class="study-line"><span>REGIONAL EVIDENCE · JAPAN &amp; THE UNITED STATES</span><span class="country-key"><i class="us"></i> United States <i class="jp"></i> Japan</span><span>2019 COMPARISON · 2022 FOCUS</span></div>
</header>
<section class="columns">
<article class="column aging">
<div class="section-heading"><span class="section-number">1</span><h2>Shared aging,<br>uneven regions</h2></div>
<p class="intro">Both countries are aging. Japan has the higher 65+ share, while national averages conceal substantial regional variation.</p>
<figure><figcaption class="figure-title"><b>A</b> National aging, 2000-2022</figcaption>{figures['A']}
<p class="caption">UN WPP2024 historical estimates, both sexes, July 1. This national series is separate from the regional sources below.</p></figure>
<figure class="ranked-group"><figcaption class="figure-title"><b>B</b> Every region, ranked · 2022</figcaption>
{figures['B_US']}{figures['B_JP']}
<p class="caption">All 50 U.S. states plus DC and 47 prefectures. Both panels use the same 0-45% scale; dashed lines are equally weighted regional medians, not national rates. Census Vintage2022 (July 1); Statistics Bureau of Japan (October 1).</p></figure>
</article>
<article class="column structure">
<div class="section-heading"><span class="section-number">2</span><h2>Economic structure:<br>no single regional rule</h2></div>
<p class="intro">The pooled aging-manufacturing association is positive. Within either country, the linear relationship is close to zero.</p>
<figure><figcaption class="figure-title"><b>C</b> Manufacturing share, 2011-2022</figcaption>{figures['C']}
<p class="caption">Nominal manufacturing value added / nominal GDP. Lines are regional medians; bands span the middle 50% of regions, not confidence intervals. U.S. calendar years; Japan fiscal years. BEA / Cabinet Office.</p></figure>
<figure class="economic-group"><figcaption class="figure-title"><b>D</b> Aggregation changes the picture · 2022</figcaption>
{figures['D_P']}{figures['D_US']}{figures['D_JP']}
<p class="caption">Identical numeric axes; every region equally weighted. Original panels reflowed vertically, with their shared y-axis repeated. Fits stay within observed aging ranges. The 2019 comparison shows the same broad attenuation.</p></figure>
<aside class="interpretation"><span class="eyebrow">INTERPRETATION</span><p><strong>{n['cov']}% of pooled covariance</strong> lies between country means. The pooled relationship should not be read as a common within-country regional pattern.</p><small>Covariance accounting, not explained variance or a causal contribution.</small></aside>
</article>
<article class="column migration-column">
<div class="section-heading"><span class="section-number">3</span><h2>Age-selective migration:<br>demographic process</h2></div>
<p class="intro">Young-adult net migration is strongly negatively associated with regional aging in Japan. The U.S. pattern is weaker and more uncertain.</p>
<figure><figcaption class="figure-title"><b>E</b> Young-adult migration and aging · 2022</figcaption>
{figures['E_JP']}{figures['E_US']}
<p class="caption">Net moves per 1,000 same-age residents, ages 20-24. U.S. bars are approximate 90% ratio MOEs, including denominator uncertainty; unknown covariance is omitted. Hollow points include zero.</p></figure>
<div class="evidence-note"><span class="eyebrow">ROBUSTNESS &amp; UNCERTAINTY</span><p>Japan: <b>r = {n['jp_r']}</b>; without Tokyo, <b>{n['jp_no_tokyo']}</b> (2019: <b>{n['jp_2019']}</b>). U.S.: <b>{n['us_r']}</b>; without DC, <b>{n['us_no_dc']}</b> (2019: <b>{n['us_2019']}</b>). <b>{n['uncertain']}/51</b> U.S. young-rate intervals include zero.</p></div>
<figure><figcaption class="figure-title"><b>F</b> Tokyo: what the total conceals</figcaption>{figures['F']}
<p class="caption">Tokyo prefecture (JP-13), all nationalities, both sexes. Full native age profile plus unknown age; registered inter-prefectural moves. These are counts, not rates.</p></figure>
<div class="tokyo-note"><p><b>2022 total: {n['total']}.</b> Ages 15-19: {n['teen']}; ages 20-24: {n['young']}. All other ages combined: <b>{n['other']}</b>, including 65+: {n['older']}.</p></div>
</article>
</section>
<footer>
<section class="key-findings" aria-label="Exactly three key findings"><h2>Key Findings</h2><div class="finding-grid">
<p><b>01</b><span>Both Japan and the United States are aging, but regional aging patterns vary widely.</span></p>
<p><b>02</b><span>The pooled aging-manufacturing association mainly reflects country differences, not a common within-country regional pattern.</span></p>
<p><b>03</b><span>Age-specific flows reveal demographic process: the young-adult association is strong in Japan, but weaker and more uncertain in the U.S.</span></p>
</div></section>
<section class="limitations"><h3>Limitations</h3><div><p>Descriptive associations, not causal effects; one year's flow cannot explain an accumulated age structure.</p><p>Japan uses constructed rates from rounded population denominators. The 2019 official-rate table and exact age-reference day remain unverified.</p><p>ACS survey residence changes differ from Japanese calendar-year registrations; U.S. estimates carry sampling uncertainty.</p><p>Population dates and GDP periods differ (U.S. CY / Japan FY). Total migration can conceal offsetting age balances.</p></div></section>
<div class="source-line"><span><b>Sources:</b> A UN WPP2024 · B Census / Statistics Bureau of Japan · C-D BEA SAGDP2 / Cabinet Office · E-F Japan Internal Migration / ACS 1-year B07001-B07401. Full provenance: accompanying README.</span><span class="review-status">READY FOR TEAM REVIEW</span></div>
</footer>
</main><script>
let fitToWidth = true;
const scaleToggle = document.getElementById('scale-toggle');
function fitPoster() {{
  const scale = fitToWidth ? Math.min(1, (window.innerWidth - 32) / (841 * 96 / 25.4)) : 1;
  document.documentElement.style.setProperty('--screen-scale', Math.max(0.1, scale));
  scaleToggle.textContent = fitToWidth ? 'View at 100%' : 'Fit to width';
}}
scaleToggle.addEventListener('click', () => {{ fitToWidth = !fitToWidth; fitPoster(); }});
window.addEventListener('resize', fitPoster);
fitPoster();
</script></body></html>'''
    write(HERE/'poster.html',page)
    write(HERE/'layout_views.json',json.dumps(VIEWS,indent=2)+'\n')
    print('Built poster.html from six unchanged SVG exports; 10 layout views, no analytical redraw.')


if __name__=='__main__':build()
