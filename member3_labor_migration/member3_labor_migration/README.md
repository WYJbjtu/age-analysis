# Member 3 — labor, migration and regional cases

Owns `data/processed/labor_migration.csv` and this directory only.

## Status (2026-11-06)

| Country | Years | employment | unemployment_rate_pct | net_migration |
| --- | --- | --- | --- | --- |
| USA (51) | 2011–2022 | ✅ BLS archived annual averages | ✅ BLS archived annual averages | ✅ Vintage 2020 (2011–2020) + Vintage 2022 (2021–2022) |
| JPN (47) | 2011–2022 | ✅ Labour Force Survey (12 years) | ✅ Labour Force Survey | ✅ 2018–2022 (all nationalities) |

`data/processed/labor_migration.csv` holds **1,176 rows** (98 regions × 12
years, 2011–2022), all `(country, region_id, year)` keys unique. Labour is
complete for every region-year; Japanese migration is complete for 2018–2022
and empty for 2011–2017 (definition break, see below). US labour is parsed from
the archived BLS state annual-average releases (one per year; the 2022 column
matches the team's BLS extract exactly); US net migration combines Census
Vintage 2020 (2011–2020) with Vintage 2022 (2021–2022), and the 2020 overlap
exposes the vintage revision. The US labour columns are
filled from the BLS extract the team supplied
(`data/raw/member3/bls_us_labor_2022.csv`); without that file the script leaves
them empty.

## Deliverables

- `../data/processed/labor_migration.csv` — **1,176 rows** (98 regions × 12 years,
  2011–2022), contract columns only; labour complete, Japanese migration
  2018–2022 (2011–2017 empty by design, see the definition note below).
- `fetch_us_inputs.py` — retrieves the archived BLS annual releases and the
  Census net-migration files into `data/raw/member3/` (default: through a text
  proxy; add `--direct` where bls.gov and census.gov answer directly).
- `prepare_labor.py` — rebuilds the Japanese rows for 2011–2022 from the
  official workbooks and assembles the US panel from the CSVs written by
  `fetch_us_inputs.py`.
- `jpn_labor_detail.csv` / `us_labor_detail.csv` — raw Japanese and US counts
  (labour force, employment, unemployment, rates) for the same rows; kept here
  because the contract table only allows three labour/migration columns.
- `plot_two_country_trend.py` — 12-year median unemployment and employment index,
  US vs Japan (`figures/two_country_trend_2011_2022.png`).
- `plot_japan_trend.py` — Japan panel: 12-year median unemployment rate and
  2018–2022 net migration for the five largest migration regions.
- `figures/jpn_panel_2011_2022.png` / `.svg`.
- `plot_figure4.py` — Figure 4: US and Japan aging × unemployment shaded by net
  migration, shared axes.
- `figures/figure4_labor_2022.png` / `.svg` — Figure 4.
- `outliers_2022.py` — outlier screen: linear trend within each country,
  standardised residuals, |z| ≥ 1.5 flagged.
- `outliers_2022.csv` + `figures/outliers_2022.png` / `.svg` — the screen's table
  and figure; the flagged regions are the same ones used as cases.
- `plot_japan_labor.py` — Japan-only panel: (a) 2022 aging × unemployment
  shaded by net migration, (b) net-migration change 2019 → 2022.
- `figures/jpn_labor_migration_2019_2022.png` / `.svg`.
- `report_section.md` — the Member 3 report section (data, definitions,
  methods, results, limitations, sources), ready to paste into the team report.
- `findings.md` — short, numbered findings with numbers and limits.
- `bls_revision_check.csv` + `check_bls_revision.py` — archived annual values vs the
  current BLS API revision (needs `.bls_key` in `data/raw/member3/`).
- `sources.csv` — one row per dataset and year; `summary.json` — coverage and URLs.

## Reproduce

From the repository root:

```bash
python member3_labor_migration/prepare_labor.py --download   # fetch missing raw files
python scripts/validate_data.py
python member3_labor_migration/plot_figure4.py                # Figure 4
python member3_labor_migration/plot_japan_labor.py            # Japan 2019/2022
python member3_labor_migration/plot_japan_trend.py            # Japan 2011-2022 panel
python -m pytest -q
```

Raw workbooks go to the git-ignored `data/raw/member3/`; existing files are
reused, so the run is offline-reproducible once they are in place. Requires
`openpyxl`; the figure needs `pandas` + `matplotlib`.

### 2019 migration workbooks are `.xls`

The Statistics Bureau publishes the 2022 report as `.xlsx` but the 2019 report
only as `.xls`, which `openpyxl` cannot read. Convert it once (Excel: *Save As
→ .xlsx*; LibreOffice: `soffice --headless --convert-to xlsx`) and keep the
converted `rb_population_movement_2019_hyo1.xlsx` next to the `.xls`. The script
prefers the converted file and only calls LibreOffice if it has to.

## Definitions and comparability

- **Japan raw counts** — jpn_labor_detail.csv keeps labour force (第２表), employment (第３表) and unemployed (第４表) in persons plus the rate (第６表); the 47 values satisfy labour force ≈ employment + unemployment with a rounding gap of at most 1,000 persons (published to the nearest thousand).
- **Japan employment** — Labour Force Survey, prefectural *model estimates*
  (モデル推計値), annual average, published in thousand persons and multiplied
  by 1000 here; a rounded estimate, not an exact head count. One release is
  used for both years, so the two years are internally consistent.
- **Japan unemployment rate** — same release, percent, 0–100.
- **Japan net migration** — 住民基本台帳人口移動報告, `転入超過数`
  (in-migrants minus out-migrants), calendar year, **2018–2022**, all
  nationalities; the 47 values sum to zero in each year. The 2011–2017 tables
  are headed *日本人移動者* (Japanese movers only), a different population
  definition (Osaka 2017: 2,961 Japanese-only vs 1,136 all-nationalities), so
  those years are kept in `jpn_migration_japanese_2011_2017.csv` as a reference
  series and never chained into the 2018–2022 figures.
- **US net migration** — Census Vintage 2020 (2011–2020) and Vintage 2022
  (2021–2022), domestic + international, July-to-July.
- Japanese and US migration definitions are **not harmonised** (period,
  foreign residents, internal vs internal+international): report countries
  separately, never merge into one cross-country migration measure.
- Labour-force universes differ too: US LAUS uses the civilian noninstitutional
  population aged 16+, Japan's Labour Force Survey uses the population aged 15+.
  Do not build a cross-country unemployment ranking before reconciling
  denominators.
- Population growth is **not** maintained here: it is derived from Member 1's
  `demographics.csv` as the brief requires, so the same population series is
  used everywhere.

## Status

Everything the brief asks Member 3 for is in place:

1. US `employment` and `unemployment_rate_pct` for 2011–2022, parsed from the 12
   archived BLS annual releases (`fetch_us_inputs.py`); the 2022 column matches
   the team-supplied extract exactly.
2. Japanese labour for all 12 years (564 rows); Japanese migration for
   2018–2022 under one definition (all nationalities). The 2011–2017 values are
   Japanese-movers only and are kept as a reference series rather than chained.
3. Combined Figure 4, the two-country trend figure and the case selection, all
   built on the full 1,176-row table.

Open items that belong to other members: the 2011 aging rate (needed if Figure 4
should encode the change in aging instead of the change in unemployment) and
industry employment composition for the second phase.


