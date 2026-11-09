"""Export audit registers and numerical findings from the frozen analysis delivery."""
from pathlib import Path
import csv, json, subprocess
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def source_metadata(name):
    if name.startswith('us_2010_'):return dict(table_id='SC-EST2020-ALLDATA6',release='Census Vintage2020 evaluation; 2010 census base',units='persons; percentages derived',period='July1 2011-2019')
    if name.startswith('us_2020_'):return dict(table_id='SC-EST2022-ALLDATA6',release='Census Vintage2022; June2023 age release',units='persons; percentages derived',period='July1 2020-2022')
    if name=='jp_long.xlsx':return dict(table_id='e-Stat 000013168610; population table10',release='2022-07-20 long-term census/intercensal series',units='thousand persons converted to persons',period='October1 2011-2020')
    if name.startswith('jp202'):
        year=int(name[2:6]);return dict(table_id=f'Population Estimates {year}; table'+name.split('table')[1].split('.')[0],release=f'April {year+1} annual population estimates',units='thousand persons or official percentage/index',period=f'October1 {year}')
    if name=='SAGDP.zip':return dict(table_id='SAGDP2__ALL_AREAS_1997_2025; lines1/12/92',release='September30 2026; NAICS2017',units='millions of current USD',period='CY2011-CY2022')
    if name in ['syuyo1.xlsx','soukatu1.xlsx']:return dict(table_id='CAO nominal economic-activity table / nominal GDP summary',release='FY2011-FY2022; 2008SNA; 2015 benchmark; pinned Nov5 2026 download',units='millions of current JPY',period='FY2011-FY2022; April-March')
    if name=='jpn_lfs.xlsx':return dict(table_id='e-Stat 000031952605; time-series tables2/3/4/6',release='Rolling workbook; latest annual result2025; retrieved Nov9 2026; delivered historical values match exactly',units='thousand persons converted to persons; percentages',period='2011-2022 calendar-year annual averages')
    if name=='jpn_migration_trend.xls':return dict(table_id='e-Stat 000031688387; table3',release='2017 annual-report historical table; Japanese nationals only',units='persons',period='CY2011-CY2017 selected')
    if name.startswith('jpn_migration_'):return dict(table_id='Basic Resident Registration annual table1 columnU; all nationalities',release=name.split('_')[-1].split('.')[0]+' annual report',units='persons',period='calendar year')
    if name=='us_migration_2020.csv':return dict(table_id='NST-EST2020-ALLDATA; NETMIG and DOMESTICMIG',release='Census Vintage2020; directory dated May4 2021',units='persons',period='July-to-July 2011-2020; domestic adapter2019')
    if name=='us_migration_2022.csv':return dict(table_id='NST-EST2022-ALLDATA; NETMIG and DOMESTICMIG',release='Census Vintage2022; December2022 totals release',units='persons',period='July-to-July 2021-2022; domestic adapter2022')
    if name.startswith('bls_'):return dict(table_id='BLS archived srgune table1',release='2023-03-01 for2022' if '2022' in name else '2020-03-04 for2019',units='thousand persons converted to persons; percentages',period='calendar-year annual average')
    return {}

def table(frame):
    columns=list(frame)
    rows=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for row in frame.itertuples(index=False,name=None):
        rows.append('| '+' | '.join('' if pd.isna(v) else f'{v:.6f}' if isinstance(v,float) else str(v).replace('|','/') for v in row)+' |')
    return '\n'.join(rows)

def main():
    if (ROOT/'docs/remediation/prechange_manifest.json').exists():
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        from verify_remediation import reports
        reports()
        return
    audit=HERE/'audit';results=HERE/'results'
    checks=pd.read_csv(audit/'source_record_checks.csv')
    summaries=pd.read_csv(audit/'source_check_summary.csv')
    files=json.loads((audit/'download_manifest.json').read_text(encoding='utf-8'))
    logs=[]
    for r in files:
        g=checks[checks.source_file==r['file']]
        is_bls=r['file'].startswith('bls_')
        logs.append(dict(source_file=r['file'],url=r['url'],retrieved_utc=r['retrieved_utc'],sha256=r.get('sha256',''),
                         pinned_hash_match=r.get('matches_pinned_hash',''),record_checks=len(g),
                         verification='independently verified numerical records' if len(g) else 'independently verified GDP reconciliation' if r['file']=='soukatu1.xlsx' else 'independently verified sample through web; raw HTTP unavailable' if is_bls else 'provenance supplied; not independently verified',
                         scope='6 states each in 2019 and 2022; employment and rate; audit/bls_primary_table_sample.csv' if is_bls else 'all delivered records for years represented in source_record_checks.csv',
                         status='PASS WITH LIMITATIONS' if is_bls else 'PASS' if r['status']=='retrieved' else 'BLOCKED',
                         notes='BLS tables viewed 2026-11-09; sample snapshot is a derived transcription, not original HTML' if is_bls else 'No rescaling or version replacement; source definitions remain country-specific'))
    logs.append(dict(source_file='WPP2024 national series',url='https://population.un.org/wpp/',retrieved_utc='',sha256='',pinned_hash_match='',record_checks=0,verification='provenance supplied; not independently verified',scope='national 2000-2022; not used in Member 4 analyses',status='NOT ASSESSED',notes='46-row supplied snapshot internally tested; original UN workbook not downloaded'))
    for r in logs:r.update(source_metadata(r['source_file']))
    pd.DataFrame(logs).to_csv(audit/'primary_source_verification_log.csv',index=False)
    # Construct clean citations from verified structured manifests, not ambiguous malformed CSV splitting.
    registry=[]
    for r in files:
        registry.append(dict(owner=r['owner'],source_file=r['file'],source_url=r['url'],sha256=r.get('sha256',''),retrieved_utc=r['retrieved_utc'],raw_path='data/raw/member4/'+r['file'],download_status=r['status'],metadata_origin='Member 1/2 pinned manifest or inspected Member 3 source definition',**source_metadata(r['file'])))
    pd.DataFrame(registry).to_csv(audit/'source_registry.csv',index=False)
    issues=[]
    def issue(id,member,severity,path,affected,evidence,consequence,correction,local,remaining,status='PASS WITH LIMITATIONS'):
        issues.append(dict(issue_id=id,member=member,severity=severity,file=path,affected=affected,evidence=evidence,consequence=consequence,recommended_correction=correction,local_integration_correction=local,remaining_action=remaining,owner=member,status=status))
    issue('M3-01','Member 3','Major','member3_labor_migration/findings.md; data/processed/labor_migration.csv','JPN net_migration 2011-2017, 329 rows',
          'Original trend table row 7 says Japanese / 日本人移動者. All 329 values match; 2019/2022 table 1 says All nationalities.',
          'A continuous all-resident 2011-2022 migration trend is not supported.',
          'Correct coverage metadata and segment or rebuild a consistent series.',
          'Annotated migration_original_definition; no numeric changes; M4 uses verified 2019/2022 domestic values separately.',
          'Owner to revise historical coverage and trend claims.','BLOCKED')
    issue('M3-02','Member 3','Major','data/processed/labor_migration.csv','USA net_migration 2011-2022, 612 rows',
          'All 612 match official NETMIG, which includes domestic and international migration; prompt requests domestic context.',
          'Original US values cannot be interpreted as domestic-only or pooled with Japan.',
          'Keep original field; add separately named DOMESTICMIG with periods.',
          'Added domestic_net_migration for all 98 regions in 2019 and 2022 from official files; originals retained.',
          'Use M4 domestic context with within-country and period caveats.')
    issue('M3-03','Member 3','Major','member3_labor_migration/sources.csv','CSV lines 3 and 4',
          'Header has 10 fields; lines 3 and 4 parse to 13 and 15 fields because commas are unquoted.',
          'Shared source aggregation fails and metadata columns cannot be trusted by a CSV parser.',
          'Use csv.writer with proper quoting and add all historical source releases.',
          'Created clean M4 registry from structured manifests and verified sources; original untouched.',
          'Owner to repair production source CSV.','BLOCKED')
    issue('M3-04','Member 3','Major','member3_labor_migration/check_bls_revision.py','top-level credential read and fetch()',
          'Hardcoded external workspace; appends registration key to BLS URL routed through r.jina.ai; averages M01-M12 rather than official M13.',
          'Unsafe credential handling and non-equivalent annual-rate comparison. Not executed; no credentials read.',
          'Use direct official BLS access, safe local configuration and official annual statistics; document vintage difference.',
          'Excluded checker and its monthly-mean revision interpretation; sampled archived official table 1 directly.',
          'Owner to repair script; assess previous use without assuming a leak occurred.','BLOCKED')
    issue('M3-05','Member 3','Major','member3_labor_migration/prepare_labor.py','US raw extracts; full pipeline reproducibility',
          'Reads bls_us_labor_2011_2022.csv and census_netmig extracts but supplies no creator/download path for them; raw cache absent initially.',
          'The advertised --download command cannot independently rebuild the entire US labor history from a clean clone.',
          'Supply archived-release parsers, exact releases and raw checksums.',
          'M4 verified all US migration and sampled 2019/2022 labor; did not overwrite original pipeline.',
          'Owner to complete US historical labor rebuild.','BLOCKED')
    issue('M3-06','Member 3','Major','member3_labor_migration/plot_figure4.py; member3_labor_migration/figures/figure4_labor_2022.png','JP-05 Akita 2022',
          'Fixed xlim=(10.5,36.5); Akita aged-65+ share is 38.6. Panel label also says 51 states + DC although USA n=51.',
          'One of 47 Japanese observations is outside the displayed range; label implies 52 US units.',
          'Extend axis to contain all observations, check bounds, label 50 states + DC.',
          'Recorded issue; M4 main figure shows every region within 10-40%.',
          'Owner to regenerate Figure 4 before group poster use.','BLOCKED')
    issue('M3-07','Member 3','Major','member3_labor_migration/report_section.md','sections 5.2 and 5.4; findings.md claims 3 and 9',
          'Aging/unemployment Pearson is -0.054091 USA and -0.460084 Japan: both negative, not reversal. Same-data outlier screen is not independent confirmation; age-matched pair does not isolate industry.',
          'Unsupported reversal and mechanism language could mislead the group conclusion.',
          'Describe weak USA versus negative Japan association; call cases illustrations; remove isolation/independent confirmation language.',
          'M4 narrative and examiner answers use descriptive claims only.',
          'Owner to edit Member 3 narrative.','BLOCKED')
    issue('M3-08','Member 3','Minor','member3_labor_migration/README.md; report_section.md; findings.md','stale coverage and small numerical claims',
          'Actual table has 1176 rows, not 145/615; USA labor history exists; Tokyo (22.8%) is younger than Okinawa (23.5%); Maine 3.0% differs from regional median 3.4%; current USA Spearman is 0.004942, not 0.02.',
          'Confusing handoff and inaccurate supporting sentences.',
          'Refresh coverage, numerical statements and pending lists from current data.',
          'Corrected values in M4 outputs and claim register.',
          'Owner to synchronize docs.')
    issue('M1-01','Member 1','Major','member1_demographics/population_detail_2011_2022.csv','USA 2019-2020 and Japan benchmark/history methods',
          'USA changes from Census Vintage2020 evaluation / 2010 base to Vintage2022 / blended2020 base. Japan history uses rounded counts; 2021/22 published rates.',
          'Endpoint changes include reference-base and rounding effects.',
          'Retain vintages and interpret changes descriptively.',
          'Preserved metadata; no interpolation or rescaling; endpoint analysis caveat retained.',
          'Known limitation already disclosed by Member 1; no numerical repair needed.')
    issue('M2-01','Member 2','Major','data/processed/industry.csv','services_share_pct across countries',
          'BEA line92 private services excludes government; Japan BO tertiary aggregate includes public activities.',
          'Pooled service correlation or country service ranking would use different definitions.',
          'Use within-country service analyses only.',
          'Kept service definitions; no pooled services model.',
          'Known limitation already disclosed by Member 2; retain in poster.')
    issue('M2-02','Member 2','Major','data/processed/industry.csv','all GDP shares and annual comparison',
          'US CY vs Japan FY (April-March); amounts nominal; US September2026 revision vs Japan 2015 benchmark release.',
          'Year key is approximate timing alignment; share changes are not real-output or job changes.',
          'Keep periods, units, revisions and economic interpretation in captions.',
          'Metadata and captions retained; no currency conversion, chained-value sum or rescaling.',
          'Known comparability limitation; no numerical repair needed.')
    issue('M4-01','Member 4','Minor','data/processed/merged_analysis.csv; docs/source_registry.csv; docs/team_tasks.md','legacy shared integration outputs',
          'Stored merge is 98 rows while current canonical sources contain 1176; task checkboxes lag Member 2/3 delivery.',
          'Legacy integration files may be mistaken for current full panel.',
          'Use documented M4 audited outputs and coordinate any shared-file refresh.',
          'New integrated_context_panel.csv with 1176 rows and audited 2019/2022 cores; old files preserved.',
          'Integration owner to choose shared final packaging after review.')
    pd.DataFrame(issues).to_csv(audit/'issues.csv',index=False)
    corrections=[
        dict(change_id='C01',field='migration_original_definition',records=329,action='Label JPN 2011-2017 Japanese-only',source='jpn_migration_trend.xls row7',numeric_values_changed=0,core_rows_removed=0),
        dict(change_id='C02',field='domestic_net_migration',records=196,action='Add separate verified domestic measure for 2019/2022',source='Census DOMESTICMIG; Japan table1 column U',numeric_values_changed=0,core_rows_removed=0),
        dict(change_id='C03',field='source_registry',records=20,action='Export clean independent registry; do not parse malformed Member3 metadata into false columns',source='structured manifests and inspected official files',numeric_values_changed=0,core_rows_removed=0)]
    pd.DataFrame(corrections).to_csv(audit/'corrections.csv',index=False)
    # Four separate dimensions, scoped rather than an all-or-nothing verdict.
    readiness=[
        ['Member 1','regional demographic data 2011-2022','PASS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','All regional canonical fields verified; WPP and map geometry not independently verified; benchmark break retained'],
        ['Member 1','WPP national claims','NOT ASSESSED','NOT ASSESSED','PASS WITH LIMITATIONS','NOT ASSESSED','Internal supplied snapshot checks only; no Member4 national claim'],
        ['Member 2','manufacturing 2011-2022','PASS','PASS WITH LIMITATIONS','PASS','PASS','All 1176 records and 564 Japan GDP reconciliations verified; CY/FY and nominal-share limits'],
        ['Member 2','pooled services','PASS','BLOCKED','PASS','BLOCKED','Numerically correct, different country aggregates; country-specific use allowed'],
        ['Member 3','labor 2019/2022 within-country','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','Japan exhaustive; USA six-region sample per year; counts rounding valid; narrative/figure repairs needed'],
        ['Member 3','US labor other years','NOT ASSESSED','PASS WITH LIMITATIONS','BLOCKED','NOT ASSESSED','Provenance supplied but raw annual reconstruction unavailable; current-API monthly-mean checker excluded'],
        ['Member 3','migration 2019/2022 within-country','PASS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','All 98 original records verified per year; domestic adapter; periods still differ'],
        ['Member 3','continuous all-resident migration 2011-2022','PASS WITH LIMITATIONS','BLOCKED','PASS WITH LIMITATIONS','BLOCKED','Japanese-only historical values cannot be presented as continuous all-resident history'],
        ['Member 3','Figure4 and reversal narrative','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','PASS WITH LIMITATIONS','BLOCKED','Akita clipped; labor correlations do not reverse sign']]
    rd=pd.DataFrame(readiness,columns=['member','scope','A_provenance_numbers','B_coverage_comparability','C_reproducibility_validation','D_figures_claims','evidence'])
    rd.to_csv(audit/'readiness.csv',index=False)
    inventory=[]
    for number,module,dataset,command in [(1,'member1_demographics','demographics','python member1_demographics/complete_population.py --raw-dir data/raw/member4'),(2,'member2_industry','industry','python member2_industry/prepare_industry.py --download'),(3,'member3_labor_migration','labor_migration','python member3_labor_migration/prepare_labor.py --download')]:
        paths=sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/module).rglob('*') if p.is_file() and '__pycache__' not in str(p))
        data=pd.read_csv(ROOT/f'data/processed/{dataset}.csv')
        commit=subprocess.check_output(['git','log','-1','--format=%H','--',f'data/processed/{dataset}.csv'],cwd=ROOT,text=True).strip()
        inventory.append(dict(member=number,module=module,canonical=f'data/processed/{dataset}.csv',canonical_last_commit=commit,rows=len(data),years='2011-2022',geography='USA 51; JPN 47 per year',code='; '.join(p for p in paths if p.endswith('.py')),documents='; '.join(p for p in paths if p.endswith('.md')),datasets='; '.join(p for p in paths if p.endswith('.csv')),figures='; '.join(p for p in paths if p.endswith('.png')),raw_initially_present=False,raw_verified_cache='data/raw/member4; download_manifest.json',origin='current origin/main 2bede5b; no local-only teammate inputs at start',reproduction_command=command,reproduction_warning='Owner command writes owner files; not executed in-place. See readiness and isolated reproduction checks.'))
    inventory.append(dict(member=4,module='analysis/member4',canonical='data/core_2019.csv; data/core_2022.csv',rows=196,years='2019; 2022',geography='98 each',code='run_analysis.py; descriptive.py; verify_sources.py; plot_figures.py; build_reports.py',documents='README.md; analysis_plan.md; audit_report.md; findings.md; poster/member4/',datasets='data/; results/; audit/',figures='figures/01-03 PNG+SVG',origin='new local uncommitted Member4 work',reproduction_command='python analysis/member4/run_analysis.py',reproduction_warning='Offline after source audit; never writes teammate outputs'))
    pd.DataFrame(inventory).to_csv(audit/'repository_inventory.csv',index=False)
    # Findings generated from result rows; source lock prevents silent narrative refresh.
    a=pd.read_csv(results/'associations.csv');primary=pd.read_csv(results/'primary_summary.csv')
    cov=pd.read_csv(results/'covariance_summary.csv');influence=pd.read_csv(results/'influence_summary.csv');overlap=pd.read_csv(results/'overlap.csv')
    context=a.query("variant=='within_country_context'")
    (HERE/'findings.md').write_text(f'''# Member 4 numerical findings

## Main result

The strong positive pooled aging–manufacturing association is almost absent within each country. This is aggregation-driven attenuation, not a robust direction reversal. All 98 regions are present in 2019 and 2022, with no primary exclusions. Each region has equal weight.

Pearson does not reverse direction in 2022. Spearman has a nominal sign reversal (+0.610267 pooled versus -0.012036 USA and -0.084724 Japan), but both within-country magnitudes are below 0.10 and the USA rank sign changes under omission. This weak rank pattern is explicitly retained; it does not support a robust Simpson-paradox headline.

{table(primary[['year','group','n','pearson','spearman','slope','x_min','x_max','y_min','y_max']])}

The x variable is the percentage of total residents aged 65+. The y variable is manufacturing nominal value added as a percentage of nominal regional GDP. Slopes measure percentage points of manufacturing share per percentage point of aging. No inferential p-values or intervals are used. Administrative units are geographically dependent and not assumed to be independent random draws.

## Aggregation

{table(cov)}

Using denominator N, pooled covariance equals the sum of country-count-weighted within-country covariance and covariance of country means. For 2022, 46.113322 = 0.416441 + 45.696881 pp², up to numerical precision. The between-country share is 99.0969%. This is an arithmetic description, not causal attribution or R². Country-demeaned Pearson is 0.021646 (slope 0.057240). Additive country indicators remove mean differences, not all confounding and not slope heterogeneity.

## Robustness

{table(a.query("variant in ['without_DC','population_weighted','country_adjusted'] and y=='manufacturing_share_pct'")[['year','group','variant','n','pearson','spearman','slope']])}

Available and common-region samples are identical (98, including USA 51 / Japan 47). Excluding DC is a sensitivity, not the primary specification. Population weighting changes the estimand toward the regional environment of residents; it is still ecological and does not estimate an individual-level relation. Weighted 2022 correlations are -0.184342 USA and +0.322449 Japan, so near-zero equal-region results must not be presented as universal absence of association.

{table(influence)}

Both within-country signs change when individual regions are omitted. These leave-one-out ranges are influence diagnostics, not confidence intervals. The pooled sign remains positive in every omission. No outliers were deleted from the primary analysis.

## Observed support

{table(overlap)}

The aging intervals do not overlap in either year. A nearest cross-country pair is not a common-support matched-age design. All selected cases are within-country. Industry ranges do overlap. Lines are restricted to each observed aging interval.

## Context and limited change analysis

{table(context[['year','group','y','n','pearson','spearman','slope']])}

Services remain country-specific. US private services exclude government; Japan's tertiary total includes public activities. Labor populations are USA civilian noninstitutional 16+ and Japan 15+. Unemployment rates use labor force, not total population, as their denominator. Domestic migration is an annual person count, not a rate; no population denominator has been invented. US migration is July-to-July, Japan calendar-year registration. Large-region scaling can affect migration correlations. None of these variables is used as an automatic regression control or as evidence about migrants' ages.

{table(pd.read_csv(results/'change_associations.csv'))}

Change analysis uses one 2019–2022 difference per region: Pearson 0.100620 USA and 0.162627 Japan. US population reference-base changes and nominal share price effects limit interpretation. A pooled independent-observation panel regression and country-clustered inference were not attempted.

## Evidence and interpretation

Observed: country means account for most of the pooled covariance, while country-specific equal-region linear relationships are near zero and unstable. Interpretation: the cross-country gap should not be read as a common regional gradient. Hypotheses for future investigation: urban concentration, industrial history, and selective migration might jointly influence these regional patterns. These hypotheses are not tested mechanisms or causal conclusions.

Principal figure: figures/01_pooled_within_2022.svg. Robustness/decomposition: figures/02_robustness_and_covariance.svg. Cases: figures/03_within_country_cases.svg. All have 300-dpi PNG companions and captions in poster/member4/figure_captions.md. Exact results are in results/associations.csv, covariance_summary.csv, influence_summary.csv, selected_cases.csv and case_candidate_pairs.csv. Every analysis has a ledger entry and sample membership in data/analysis_samples.csv.

Provenance: canonical input hashes and commits in audit/input_manifest.json and repository_inventory.csv; official URLs, retrieval times and hashes in audit/download_manifest.json; {len(checks):,} field-level source checks in audit/source_record_checks.csv, all passed within source-precision tolerances. These include exhaustive regional population and industry checks, exhaustive Japanese labor and selected migration years, all US migration years, and a six-state BLS sample in each main year. National WPP and remaining US labor years are not independently verified.
''',encoding='utf-8')
    finding_rows=[
        dict(finding_id='F1',claim='Pooled association nearly disappears within countries',year=2022,n='98 pooled; USA51; JPN47',evidence='Pearson 0.644435; 0.003224; 0.028647; Spearman 0.610267; -0.012036; -0.084724',figure='figures/01_pooled_within_2022.svg',table='results/primary_summary.csv',sensitivity='2019 0.618710;0.040097;-0.009533; same common sample',limitation='No stable within-country sign; no causal interpretation'),
        dict(finding_id='F2',claim='Most pooled covariance is between countries',year=2022,n='98',evidence='45.696881 / 46.113322 = 99.0969%; within 0.416441 pp2',figure='figures/02_robustness_and_covariance.svg',table='results/covariance_summary.csv',sensitivity='2019 between share 99.8077%; demeaned r 0.004491 vs 0.021646 in2022',limitation='Accounting decomposition, not causal explanation or variance explained'),
        dict(finding_id='F3',claim='Similar aging can coexist with different manufacturing shares',year=2022,n='all eligible pairs screened from USA51 and JPN47',evidence='IN/NV industry gap20.677317pp; Hokkaido/Toyama22.812522pp; contrasting smallest-gap pairs retained',figure='figures/03_within_country_cases.svg',table='results/selected_cases.csv',sensitivity='All candidate pairs exported; smallest-gap contrasting cases shown',limitation='Selected descriptive examples do not isolate industry; no cross-country aging overlap')]
    for r in finding_rows:r['provenance']='audit/input_manifest.json; audit/download_manifest.json; audit/source_record_checks.csv'
    pd.DataFrame(finding_rows).to_csv(results/'finding_evidence.csv',index=False)
    claims=[]
    d=pd.read_csv(ROOT/'data/processed/demographics.csv');i=pd.read_csv(ROOT/'data/processed/industry.csv');l=pd.read_csv(ROOT/'data/processed/labor_migration.csv')
    for country in ['USA','JPN']:
        g=d[(d.country==country)&(d.year==2022)]
        claims.append(dict(member='Member1',file='member1_demographics/findings.md',claim=f'{country}2022 aging distribution',observed=f'n={len(g)}; median={g.age65_share_pct.median():.6f}; min={g.age65_share_pct.min():.6f}; max={g.age65_share_pct.max():.6f}',status='PASS',verification='exhaustive canonical recomputation plus primary-source checks'))
        a=i[(i.country==country)&(i.year==2011)].manufacturing_share_pct.median();b=i[(i.country==country)&(i.year==2022)].manufacturing_share_pct.median()
        claims.append(dict(member='Member2',file='member2_industry/findings.md',claim=f'{country}2011-2022 manufacturing medians',observed=f'{a:.6f} to {b:.6f}; difference={b-a:.6f}pp',status='PASS',verification='full pinned industry source verification; medians not national shares'))
    tokyo=l[(l.region_id=='JP-13')&l.year.isin([2019,2022])].set_index('year').net_migration
    claims.extend([
        dict(member='Member1',file='member1_demographics/findings.md',claim='WPP national aging endpoints',observed='supplied 46-row snapshot internally consistent; original source not downloaded',status='NOT ASSESSED',verification='not used by Member4'),
        dict(member='Member3',file='member3_labor_migration/findings.md',claim='Tokyo net inflow roughly halved',observed=f'{tokyo[2019]} to {tokyo[2022]}; difference={tokyo[2022]-tokyo[2019]} persons',status='PASS',verification='both original all-nationalities annual workbooks checked'),
        dict(member='Member3',file='member3_labor_migration/report_section.md',claim='Aging-unemployment sign reversal between countries',observed='Pearson USA -0.054091; Japan -0.460084; both negative',status='BLOCKED',verification='same current canonical samples; no sign reversal'),
        dict(member='Member3',file='member3_labor_migration/figures/figure4_labor_2022.png',claim='All47 Japanese observations visible',observed='Akita38.6 outside xlim36.5',status='BLOCKED',verification='source-code bounds and canonical value'),
        dict(member='Member3',file='member3_labor_migration/findings.md',claim='All-resident migration2011-2022',observed='329 historical Japan values use Japanese-only scope',status='BLOCKED',verification='original table3 row7'),
        dict(member='Member3',file='member3_labor_migration/report_section.md',claim='Maine at median unemployment; Okinawa youngest',observed='Maine3.0 versus median3.4; Tokyo22.8 younger than Okinawa23.5',status='BLOCKED',verification='canonical2022 and official inputs'),
    ])
    pd.DataFrame(claims).to_csv(audit/'claim_checks.csv',index=False)
    print(f'Exported {len(issues)} issues, {len(logs)} source-verification entries and findings.')

if __name__=='__main__': main()
