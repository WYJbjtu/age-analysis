# Member 3 — Labour market, migration and regional cases

**Project:** Regional Associations Between Population Aging and Industrial Structure — A Comparative Study of U.S. States and Japanese Prefectures (DSC5002)
**Analytical year:** 2022 cross-section with the **2011–2022** labour panel behind
it (the 2019 comparison is a pre-pandemic check); migration covers **2018–2022**
because the earlier Japanese tables use a different population definition (§3)
**Owner:** Member 3 (`data/processed/labor_migration.csv`, `member3_labor_migration/`)

---

## 1. Scope

This section supplies the labour-market and migration layer of the project. It
answers two questions:

1. How do regional labour markets differ between U.S. states and Japanese
   prefectures in 2022?
2. How is population movement related to regional aging and industrial
   structure, and does the 2022 pattern also hold before the pandemic (2019)?

The section is explanatory: the core aging × industrial-structure analysis runs
on the population and industry tables alone. Nothing here is imputed; where a
value is unavailable the cell stays empty.

## 2. Data and sources

| Indicator | Source | Coverage | Reference period | Version |
|---|---|---|---|---|
| US employment, unemployment, unemployment rate | BLS Local Area Unemployment Statistics (LAUS), state annual averages | 51 regions (50 states + DC) | calendar **2011–2022** | 12 archived releases (2012–2023), current-year column |
| US net migration | Census Bureau, Population Estimates | 51 regions | 2011–2020 and 2021–2022 (July-to-July) | Vintage 2020 for 2011–2020; Vintage 2022 for 2021–2022 |
| Japan employment, unemployment, unemployment rate | Labour Force Survey, prefectural model estimates (e-Stat `statInfId=000031952605`) | 47 prefectures | annual averages **2011–2022** | one release, all 12 years |
| Japan net migration | 住民基本台帳人口移動報告 (Basic Resident Registration), table 1, column U | 47 prefectures | calendar **2018–2022** | single-year workbooks, all nationalities (2011–2017 exists only as Japanese-movers and is not merged, see §3) |

Full URLs, table names and notes: `member3_labor_migration/sources.csv`.
The analysis table is `data/processed/labor_migration.csv` (**1,176 rows**:
51 US + 47 JP regions × 12 years, 2011–2022), keyed on
`(country, region_id, year)`. Labour is complete for all 12 years; migration is
complete for 2018–2022 and deliberately empty for 2011–2017 (§3).

## 3. Definitions and comparability

- **Employment** is the number of employed persons (residence-based), not the
  manufacturing-employment share.
- **Unemployment rate** = unemployed ÷ labour force × 100, reported on a 0–100
  scale and taken from annual averages, never from a single month.
- **Labour-force universes differ:** US LAUS covers the civilian
  noninstitutional population aged **16+**; the Japanese survey covers the
  population aged **15+**. Comparisons here are made *within* each country; no
  cross-country unemployment ranking is implied.
- **Migration definitions differ:** the U.S. figure is total domestic +
  international net migration over a July-to-July year; the Japanese figure is
  inter-prefectural net migration for a calendar year and includes foreign
  residents. The two are therefore reported separately and are never merged
  into one cross-country migration indicator.
- BLS counts are published in thousands and multiplied by 1000; they remain
  rounded estimates, not exact head counts.
- The Japanese labour series is a *model-based estimate* for prefectures; all 12
  years come from the same release, so the series is internally consistent.
- The US labour series is assembled from 12 archived annual releases and keeps
  each year's **as-published** value; BLS revisions move state annual rates by a
  median of 0.1 pp and at most 0.7 pp (`bls_revision_check.csv`).
- US net migration spans two vintages: Vintage 2020 for 2011–2020 and Vintage
  2022 for 2021–2022, with the 2020 overlap exposing the revision.
- **Japanese migration has a definition break at 2017/2018.** The 2011–2017
  annual-report trend table is headed *日本人移動者* (Japanese movers only); the
  2018–2022 single-year tables are headed *移動者（日本人及び外国人）* and include
  foreign residents. Osaka 2017 is 2,961 under the first definition and 1,136
  under the second, so the two forms are **not chained**: the contract table
  carries migration for 2018–2022 only, and the Japanese-only 2011–2017 values
  are kept as a separate reference series (`jpn_migration_japanese_2011_2017.csv`).

## 4. Methods

1. Each region was assigned equal weight; no population weighting was used, so
   the figures describe regional variation, not national totals.
2. Pearson and Spearman correlations between the aging rate and the
   unemployment rate were computed **within each country**, on the 2022
   cross-section (n = 51 and n = 47). The two countries were not pooled.
3. Net migration is presented in absolute persons and shaded on a country-
   specific scale because magnitudes differ by an order of magnitude.
4. Regional cases were selected mechanically: pairs of regions whose aging
   rates differ by at most 0.5 percentage points while manufacturing shares
   differ by at least 8 percentage points.

## 5. Results

### 5.1 Labour-market profiles, 2022

| | United States (n = 51) | Japan (n = 47) |
|---|---|---|
| Aging rate, median (range) | 17.8 % (12.0–22.5) | 31.5 % (22.8–38.6) |
| Unemployment rate, median (range) | 3.4 % (2.1–5.4) | 2.2 % (1.3–3.2) |
| Employment, smallest / largest | 281 k (Wyoming) / 18,441 k (California) | 296 k (Tottori) / 8,332 k (Tokyo) |
| Net migration, lowest / highest | −221,634 (New York) / +444,484 (Florida) | −9,207 (Hiroshima) / +38,023 (Tokyo) |

Two contrasts stand out. First, the **dispersion of unemployment is much wider
in the United States** (3.3 pp between the lowest and highest state) than in
Japan (1.9 pp). Second, **U.S. net migration is roughly an order of magnitude
larger in absolute terms**, and unlike Japan it includes international moves;
the Japanese 47 values sum to zero by construction, so they describe internal
redistribution only.

### 5.2 Aging and unemployment (Figure 4)

Figure 4 plots the aging rate against the unemployment rate for every region,
shaded by net migration, with shared axes across countries. Point size encodes
the absolute change in the unemployment rate between 2011 and 2022, so the
2022 cross-section also carries a time dimension (no 2011 aging data are in the
shared tables yet, so the labour change is used instead).

- **United States:** essentially no association (Pearson r = −0.05,
  Spearman ρ = 0.02, n = 51). Older states are neither systematically tighter
  nor looser labour markets; Nevada combines the highest unemployment (5.4 %)
  with an average aging rate (16.9 %), while Maine is the oldest state (22.5 %)
  and sits at the national median unemployment (3.0 %).
- **Japan:** a clear negative association (r = −0.46, ρ = −0.44, n = 47).
  The oldest prefectures tend to have the *lowest* unemployment — Shimane
  (34.7 % aged 65+) has the lowest rate in the country (1.3 %), while Okinawa,
  the youngest prefecture (23.5 %), has the highest (3.2 %).

The sign reversal between the two countries is the section's main comparative
result. It is descriptive: aging and unemployment are both outcomes of long
structural processes, and a cross-section cannot separate them.

### 5.3 Migration and aging

Over the longer Japanese series the labour-market trend and the migration trend
tell different stories. The median prefecture unemployment rate fell almost
monotonically from **4.3 % (2011)** to **2.1 % (2018–19)**, then edged up to
2.3 % and 2.4 % in 2020–21 and back to 2.2 % in 2022 — a decade-long tightening
that dwarfs any single-year pandemic movement. Net migration, by contrast, is
dominated by short-run swings in the Tokyo metropolitan area: Tokyo received
**+79,844** net migrants in 2018 and **+82,982** in 2019, then **+31,125** in
2020 and only **+5,433** in 2021 (a 93 % fall), before recovering to **+38,023**
in 2022 (see `figures/jpn_panel_2011_2022.png`).

- In the U.S., the states with the largest net inflows (Florida +444 k,
  Texas +350 k, North Carolina +126 k) are not the oldest, and the largest
  outflow (New York −222 k) is mid-range in aging; the
  aging–migration correlation is weak (Section 5.2 shading).
- In Japan, net migration is overwhelmingly concentrated on the Tokyo
  metropolitan area: Tokyo +38,023, Kanagawa +27,564, Saitama +25,364, Chiba
  +8,568, against Hiroshima −9,207 and Aichi −7,910.
- **The Tokyo inflow roughly halved between 2019 and 2022** (+82,982 →
  +38,023, a change of −44,959 persons, the largest of any prefecture), while
  only 11 of 47 prefectures became net losers over the same period. The 2022
  pattern therefore should not be presented as a simple continuation of 2019;
  it is consistent with a pandemic-period compression of the urban inflow, but
  this is a descriptive observation, not a causal claim.
- Labour-market changes between the two years are small by comparison:
  unemployment-rate changes stay within −0.6 pp (Shimane) to +0.7 pp
  (Kanagawa), and employment moved by +237 k in Tokyo, −64 k in Hokkaido and
  −63 k in Kanagawa.

### 5.4 Regional cases

**United States — Indiana vs Nevada** (aging 16.91 % vs 16.89 %, i.e. 0.02 pp
apart):

| | Indiana | Nevada |
|---|---|---|
| Manufacturing share of GDP | 25.1 % | 4.4 % |
| Unemployment rate | 3.0 % | 5.4 % |
| Employment | 3,303 k | 1,466 k |
| Net migration | +20,720 | +30,944 |

The pair isolates industrial structure: with almost identical aging, Indiana is
a manufacturing state with a mid-range labour market, Nevada a
services/leisure state with the highest unemployment and a larger net inflow.

**Japan — Hokkaido vs Toyama** (aging 32.8 % vs 33.0 %):

| | Hokkaido | Toyama |
|---|---|---|
| Manufacturing share of GDP | 8.7 % | 31.5 % |
| Unemployment rate | 3.2 % | 1.8 % |
| Employment | 2,602 k | 553 k |
| Net migration | −3,476 | −1,275 |

Again aging is matched while industrial structure diverges sharply (22.8 pp);
the manufacturing-heavy prefecture has both lower unemployment and a smaller
net outflow. The pair is offered as an illustration of a pattern, not as
evidence of a mechanism.

Two-country trends over the full window are summarised in
`figures/two_country_trend_2011_2022.png`: the median US state unemployment
rate fell from 8.0 % to 3.5 % between 2011 and 2019, spiked to 7.3 % in 2020 and
returned to 3.4 % in 2022, while the Japanese median moved from 4.3 % to 2.1 %
and back to 2.2 % — the same direction, but roughly one third of the amplitude.
Regional employment in 2022 stood about **10 % above its 2011 level in the US
(median state)** and about **2 % above in Japan (median prefecture)**; US levels
around 2020–21 also carry a labour-force population-control break that should be
kept in mind when reading index levels across that boundary.

## 6. Systematic outlier screen

To choose "unusual regions" by a rule rather than by inspection, a linear trend
was fitted separately within each country for two relationships, and
standardised residuals with |z| ≥ 1.5 were flagged (`figures/outliers_2022.png`,
`outliers_2022.csv`).

| Relationship | Largest positive residual | Largest negative residual |
|---|---|---|
| US unemployment ~ aging | Nevada +2.6 SD (5.4 % vs 3.4 % fitted) | North Dakota −1.8 SD (2.1 % vs 3.5 %) |
| JP unemployment ~ aging | Hokkaido +2.8 SD (3.2 % vs 2.2 %) | Fukui −2.2 SD (1.4 % vs 2.3 %) |
| US manufacturing ~ aging | Indiana +3.1 SD (25.1 % vs 10.3 %) | District of Columbia −2.1 SD (0.2 % vs 10.2 %) |
| JP manufacturing ~ aging | Shiga +2.0 SD (41.8 % vs 23.4 %) | Okinawa −2.1 SD (4.0 % vs 23.2 %) |

Three observations follow. First, the regions used as cases in Section 5.4 are
themselves the strongest outliers (Indiana +3.1 SD on manufacturing, Nevada
+2.6 SD on unemployment, Hokkaido +2.8 SD on unemployment), which confirms that
the mechanical pairing rule lands on genuinely unusual regions rather than on
arbitrary ones. Second, capital and tourism regions (District of Columbia,
Okinawa) are structural outliers: their industry mix is dominated by government
or tourism, so an aging–manufacturing trend does not describe them. Third, the
residual standard deviations differ by a factor of two (US unemployment 0.76 pp
vs Japanese unemployment 0.38 pp), i.e. Japan's labour market is not only
tighter but also more homogeneous.

Residuals describe departures from a straight-line summary; they are not a
model-adequacy test and carry no causal content.

## 7. Interpretation and limitations

- Regional association is not causation; both aging and labour-market outcomes
  reflect long-run demographic and economic processes.
- U.S. labour values are the **as-published** annual averages of each year's
  release; BLS later revisions move state rates by a median of 0.1 pp and at
  most 0.7 pp, which is documented rather than smoothed away.
- Japanese labour covers 2011–2022, but Japanese migration covers only
  2018–2022: the earlier tables use a different population definition
  (Japanese movers vs all nationalities), so the two are never chained and the
  trend figures show migration from 2018 only.
- Labour-force universes (16+ vs 15+) and migration definitions differ across
  countries, so figures are read within countries, not across them.
- Small areas are noisy: several prefectures and states have labour-force
  estimates rounded to the nearest thousand, and Japanese prefectural labour
  statistics are model-based.
- The 2019→2022 comparison is a descriptive year check, not a COVID-19
  evaluation.
- Cases were selected by a stated rule and illustrate patterns; they do not
  establish mechanisms.

## 8. Reproduction

```bash
python member3_labor_migration/prepare_labor.py --download   # rebuild the 1,176-row table
python member3_labor_migration/fetch_us_inputs.py            # re-fetch the US inputs (2011-2022)
python scripts/validate_data.py                              # contract check
python member3_labor_migration/plot_figure4.py               # Figure 4
python member3_labor_migration/plot_two_country_trend.py     # two-country 12-year trends
python member3_labor_migration/plot_japan_trend.py           # Japan 12-year panel
python member3_labor_migration/plot_japan_labor.py           # Japan 2019/2022 panel
python member3_labor_migration/outliers_2022.py              # outlier screen
```

Files: `data/processed/labor_migration.csv`;
`member3_labor_migration/{jpn_labor_detail.csv, us_labor_detail.csv, outliers_2022.csv,
bls_revision_check.csv, figures/figure4_labor_2022.png|svg,
figures/two_country_trend_2011_2022.png|svg, figures/jpn_panel_2011_2022.png|svg,
figures/jpn_labor_migration_2019_2022.png|svg, figures/outliers_2022.png|svg,
sources.csv, summary.json}`.

## 9. Sources

1. U.S. Bureau of Labor Statistics, *Local Area Unemployment Statistics*, state
   annual averages 2011–2022, twelve archived releases
   (`srgune_02292012` … `srgune_03012023`) —
   <https://www.bls.gov/bls/news-release/>; the 2022 release is
   <https://www.bls.gov/news.release/archives/srgune_03012023.htm>
2. U.S. Census Bureau, *Population Estimates*, NST-EST2020-ALLDATA (Vintage
   2020, net migration 2011–2020) —
   <https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/state/totals/nst-est2020-alldata.csv>
   and NST-EST2022-ALLDATA (Vintage 2022, net migration 2021–2022) —
   <https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/totals/NST-EST2022-ALLDATA.csv>
3. Statistics Bureau of Japan / e-Stat, *Labour Force Survey*, prefectural
   model estimates, annual averages 2011–2022 —
   <https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031952605&fileKind=0>
4. Statistics Bureau of Japan, *住民基本台帳人口移動報告*, table 1 column U for
   2018–2022 —
   <https://www.stat.go.jp/data/idou/2022np/jissu/zuhyou/hyo1.xlsx>; and the 2017
   annual report, table 3 (net migration 2000–2017) —
   <https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031688387&fileKind=0>

