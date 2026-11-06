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

US release2022 core values are preserved. Adding population years does not supply matching industry/labor years. The existing Member4 merge script uses an outer join and will show population-only historical rows until other members supply data; filter matched records and year as required. Member1 does not claim full1176-row matched industry data.

The primary history publication has source-vintage/census-base differences; read findings.md before interpreting changes. No imputation, synthetic rows, or pooled repeated-year correlation.

## Storage and delivery
Author working files: D:/DSC5002_Member1. Releases are standalone versioned artifacts. No new desktop files. This module README supersedes historical handover notes describing missing Japanese population or national trends.
