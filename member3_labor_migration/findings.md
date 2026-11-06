# Member 3 findings — labor market, migration and regional cases

## Sources and coverage

`data/processed/labor_migration.csv` has **1,176 rows** = 98 regions × 12 years
(51 US + 47 JP, 2011–2022), all keys unique and no empty cells. US labour comes
from the archived BLS state annual-average releases (one release per year, the
current-year column); US net migration from Census Vintage 2020 for 2011–2020
and Vintage 2022 for 2021–2022. Japanese labour is the prefectural model
estimate release; Japanese migration comes from the annual reports
(2018–2022 workbooks, 2011–2017 from the annual-report trend table 3). Raw
counts (labour force, employment, unemployment) are in `jpn_labor_detail.csv`.
Sources, tables and reference periods: `sources.csv`; rebuild with
`prepare_labor.py --download` (US labour is filled from
`data/raw/member3/bls_us_labor_2022.csv`).

## USA 2022 — net migration and labour market

1. Annual net migration (persons): minimum **US-NY = -221,634**; maximum
   **US-FL = 444,484**. Median across the 51 equally weighted regions =
   **10,330** (median of regions, not a population-weighted national figure).
2. **US unemployment ranged from 2.1 % to 5.4 %** in 2022 (North Dakota and
   South Dakota lowest, Nevada 5.4 %, District of Columbia 4.7 %), median
   **3.4 %** — nearly twice the Japanese median (2.2 %) and far wider spread
   (3.3 pp vs 1.9 pp). Employment spans 281 thousand (Wyoming) to 18,441
   thousand (California).
3. **Aging and unemployment are essentially unrelated in the 2022 US
   cross-section** (Pearson r = **-0.05**, Spearman rho = **0.02**, n = 51), so
   older states are neither systematically tighter nor looser labour markets.

## Japan 2022 — employment, unemployment, migration

4. **Net migration is extremely concentrated in the Tokyo metropolitan area.**
   Largest net inflows: Tokyo **+38,023**, Kanagawa **+27,564**, Saitama
   **+25,364**, Chiba **+8,568**, Osaka **+6,539**. Largest net outflows:
   Hiroshima **-9,207**, Aichi **-7,910**, Fukushima **-6,733**, Niigata
   **-5,830**, Hyogo **-5,625**. The 47 values sum to 0 in each year, so this is
   internal redistribution, not national growth.
5. **Employment is as concentrated as population.** Tokyo **8,332 thousand**
   employed persons against **296 thousand** in Tottori — roughly a 28-fold
   spread across prefectures.
6. **Unemployment is low and spatially flat.** Prefectural rates run from
   **1.3 % (Shimane)** to **3.2 % (Okinawa)**, median **2.2 %**. The highest-rate
   prefecture has only a modest net outflow, so unemployment alone does not
   explain regional migration in Japan.

## Japan 2019 vs 2022 — does the 2022 pattern depend on the year?

7. **The Tokyo inflow roughly halved between the two years.** Tokyo net
   migration fell from **+82,982 (2019)** to **+38,023 (2022)**, a change of
   **-44,959 persons** — by far the largest movement of any prefecture
   (next: Aichi -5,979). Only **11 of 47** prefectures had a smaller net inflow
   (or a larger net outflow) in 2022; the other 36 *improved*, mostly because
   less population was drawn toward Tokyo. The 2022 cross-section therefore
   should not be presented as a continuation of the 2019 pattern.
8. **Labour-market changes between the years are small compared with the
   migration shift.** Unemployment-rate changes stay within **-0.6 pp
   (Shimane)** to **+0.7 pp (Kanagawa)**, while employment rose by **237
   thousand in Tokyo** and fell by 64 thousand in Hokkaido and 63 thousand in
   Kanagawa. Migration moved far more than the unemployment rate did.

9. **An outlier screen independently confirms the case choices.** Fitting a
   linear trend within each country and standardising the residuals (|z| ≥ 1.5)
   flags Indiana **+3.1 SD** on manufacturing (25.1 % vs 10.3 % fitted), Nevada
   **+2.6 SD** on unemployment (5.4 % vs 3.4 %), Hokkaido **+2.8 SD** on
   unemployment (3.2 % vs 2.2 %), District of Columbia **-2.1 SD** and Okinawa
   **-2.1 SD** on manufacturing (0.2 % and 4.0 %). The three case regions are
   therefore the statistical outliers themselves, not arbitrary picks.

10. **Japan's labour market tightened for a decade, then stalled.** The median
    prefecture unemployment rate fell from **4.3 % (2011)** to **2.1 %
    (2018 and 2019)**, edged up to **2.3 % (2020)** and **2.4 % (2021)** and
    returned to **2.2 % (2022)**. The 2011–2019 decline is almost monotonic
    (−2.2 pp in eight years), far larger than any year-to-year move during
    COVID-19.

11. **Tokyo's migration inflow collapsed in 2020–21 and only partly recovered.**
    Tokyo net migration was **+79,844 (2018)**, **+82,982 (2019)**, then
    **+31,125 (2020)**, **+5,433 (2021)** — a 93 % drop from 2019 — and
    **+38,023 (2022)**. The 2021 value is below the 2018 level by more than
    74,000 persons, while the other large metropolitan prefectures (Kanagawa,
    Saitama, Osaka) moved much less.

12. **The two countries' 12-year labour cycles have very different
    amplitudes.** The median state unemployment rate in the US ran **8.0 %
    (2011) → 3.5 % (2019) → 7.3 % (2020) → 3.4 % (2022)**, a 4.5 pp fall and a
    3.8 pp pandemic spike; Japan's median prefecture rate moved **4.3 % →
    2.1 % → 2.3 % → 2.2 %**, i.e. a similar long decline but a pandemic bump of
    only about 0.3 pp. Regional labour markets in the US are both higher and far
    more volatile across the cycle.

13. **Vintages matter, and the size is measurable.** Comparing each state-year
    with the prior-year column of the next release (561 pairs), BLS revised the
    annual state unemployment rate by a **median of 0.1 pp, 90th percentile
    0.2 pp, maximum 0.7 pp** (Alabama 2013, Alaska 2019, Nevada 2020). The
    current API revision differs from the archived values by a median of
    0.1 pp and at most 0.94 pp, part of which is the rounding of monthly
    values. The table keeps the **as-published value for each year** and
    documents the vintage in `sources.csv`; the comparison is saved in
    `bls_revision_check.csv`.

## Figures

- `figures/jpn_panel_2011_2022.png` / `.svg` — (a) median prefecture
  unemployment rate 2011–2022; (b) net migration 2018–2022 for the five largest
  migration regions. Script: `plot_japan_trend.py`.
- `figures/figure4_labor_2022.png` / `.svg` — Figure 4: US and Japan aging ×
  unemployment shaded by net migration, shared axes. Script: `plot_figure4.py`.
- `figures/two_country_trend_2011_2022.png` / `.svg` — 12-year median unemployment
  and employment index, US vs Japan. Script: `plot_two_country_trend.py`.
- `figures/outliers_2022.png` / `.svg` — residual outlier screen; data in
  `outliers_2022.csv`. Script: `outliers_2022.py`.
- `figures/jpn_labor_migration_2019_2022.png` / `.svg` — (a) 2022 aging rate ×
  unemployment rate shaded by net migration; (b) largest net-migration changes
  2019 → 2022. Script: `plot_japan_labor.py`.
- Existing US age/manufacturing maps and ranked plots:
  `../handover/us_2022/deliverables/figures/`.

## Definitions and limitations

- **Japan employment** — Labour Force Survey prefectural model estimates,
  annual average, thousand persons × 1000; rounded estimates, not exact counts.
  One release is used for all 12 years so the series is internally consistent.
- **Japan unemployment rate** — same release, percent (0–100).
- **Japan net migration** — 住民基本台帳人口移動報告, `転入超過数`, calendar
  year, includes foreign residents, 2011–2022. 2011–2017 come from the
  annual-report trend table 3 (2000–2017), which reproduces the single-year
  workbooks exactly where they overlap (Hokkaido 2011 = -2,482 in both).
- **US net migration** — Census Vintage 2022, domestic + international,
  2021-07-01 → 2022-07-01.
- The two migration measures are **not harmonised** (period; foreign residents;
  internal vs internal + international). Report countries separately.
- Labour-force universes differ: US LAUS is 16+ civilian noninstitutional,
  Japan's survey is 15+. No cross-country unemployment ranking is claimed.
- The 2019→2022 comparison is a **descriptive year check**, not a COVID causal
  test; 2022 is a single pandemic-affected year and the full 2011–2022 panel is
  still to be built.
- Cross-sectional association is not causation; regional cases illustrate
  patterns rather than mechanisms.



