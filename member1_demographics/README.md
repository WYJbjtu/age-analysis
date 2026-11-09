# Member1 population delivery

## Start here
- data/processed/demographics.csv: canonical contract table,1176 rows, unchanged column names.
- member1_demographics/population_detail_2011_2022.csv: full age-group counts, reference dates, precision, source version and rate method.
- population_2019.csv and population_2022.csv:98-region snapshots for integration.
- national_trends_wpp2024_2000_2022.csv:46 national rows; never append to region samples.
- figures/01–03: trend, regional comparison and endpoint-change figures, PNG/SVG/PDF.
- findings.md: numerical results, limitations and presentation structure.

## Data dictionary
country: USA/JPN. region_id: official repository code. year: reference year.
Canonical total_population corresponds to detail population_total (persons). Detail population_0_14, population_15_64, population_65plus retain source age counts. Japan counts multiplied by1000 retain only thousand-person precision; original rounding may leave a residual between groups and total.
age65_share_pct=65+/total×100; working_age_share_pct=15–64/total×100; old_age_dependency_ratio=65+/15–64×100. Japan2021/2022 uses officially published rates; older Japan years use counts. Percentages are0–100; changes are percentage points.
population_reference_date: USA July1, Japan October1. source_version and rate_method are row-level provenance. count_precision_persons:1 USA;1000 Japan. WPP national series uses both sexes, July1, Estimates, WPP2024.

## Reproduce
Install pandas,numpy,openpyxl,requests,matplotlib. Raw files must be in an explicit folder. See population_source_manifest.json for exact URLs/hashes. Downloaded raw files are not committed.
python member1_demographics/complete_population.py --raw-dir PATH_TO_RAW
python member1_demographics/plot_population.py
python scripts/validate_data.py
PYTHONPATH=src python -m pytest -q tests member2_industry/test_industry.py

Census direct downloads may return403; the same public official link can be downloaded normally through a browser. Do not use Civilian population in place of Resident population. Files are normalized locally to the manifest filenames.

The UN original workbook is about240MB and contains an incorrect worksheet dimension; complete_population.py reads its actual worksheet XML. For lightweight offline reproduction, the reviewed46-row UN extract is supplied in source_snapshots/wpp2024_selected_estimates.csv. If wpp_ages.xlsx is absent the script uses this extract. Original full-source hash is retained in the manifest; the selected extract has its own hash in snapshot_manifest.json.

US release2022 core values are preserved. The current shared merge has all1176 population–industry region-year matches; labor/migration is optional context joined on the left. Full panel coverage does not establish that every historical series or reporting period is comparable.

The primary history publication has source-vintage/census-base differences; read findings.md before interpreting changes. No imputation, synthetic rows, or pooled repeated-year correlation.

## Storage and delivery
Author working files: D:/DSC5002_Member1. Releases are standalone versioned artifacts. No new desktop files. This module README supersedes historical handover notes describing missing Japanese population or national trends.

## Independent verification added 2026-11-09

The unchanged original WPP2024 F06 percentage workbook was retrieved from the UN and matched its original SHA-256. `verify_national_and_maps.py` independently reads the Estimates sheet using openpyxl (the original builder reads XML). It verifies USA/840 and JPN/392, both sexes, historical 2000–2022 estimates, July 1, and the mutually exclusive 0–14 / 15–64 / 65+ groups. All 276 comparisons across the 46-row snapshot and delivered national CSV pass at 1e-8 percentage-point tolerance. This source publishes percentages: aged65+ / total de facto population ×100. Reconstruction from a separate count product remains NOT EVALUATED; no count or regional-mean substitute is introduced.

The existing U.S. maps use checksum-verified Census 2022 cartographic boundaries at 1:20,000,000. All 51 state/DC code/name joins and 102 displayed values are checked; multipart geometries remain parts of a single region. Alaska, Hawaii and DC use insets with different geographic scales, while each map retains one absolute percentage color scale. The boundary metadata permits reuse with Census attribution and restricts use to generalized small-scale display. There is no existing Japanese boundary map in this repository; use the complete 47-prefecture ranked chart for country comparison, with its common 0–45% scale.

Evidence: [independent_verification.json](independent_verification.json), [national_source_checks.csv](national_source_checks.csv), [boundary_join_checks.csv](boundary_join_checks.csv). No validated regional/national population values or figures required replacement. Execute `python member1_demographics/verify_national_and_maps.py` after the optional `python scripts/fetch_remediation_sources.py --group member1`. Cached verification is offline. Current presentation selection: [poster README](../poster/README.md).
