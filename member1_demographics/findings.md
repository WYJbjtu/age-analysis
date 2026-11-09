# Member 1 Population findings

## Coverage and sources
Completed: 98 regions × 12 years (2011–2022) = 1,176 regional observations; separate 2019 and 2022 extracts each98 rows. National background: 2 countries × 23 years (2000–2022) = 46 observations, UN WPP2024 Estimates. No national totals in the regional panel. No imputation. Core fields and all count-detail fields are nonmissing. Exact URLs, file hashes and periods are in sources.csv and population_source_manifest.json.

## Finding 1: national aging trajectories diverge
- USA: aged65+ share 12.19% in2000 to 16.92% in2022, +4.73 percentage points (UN WPP2024).
- JPN: aged65+ share 17.44% in2000 to 29.40% in2022, +11.96 percentage points (UN WPP2024).
Figure: figures/01_national_aging_trends_2000_2022.png (SVG/PDF also available). Purpose: establish common-source national context, before regional analysis. The chart shows annual percentages, not counts, and does not establish a cause of aging.

## Finding 2: national labels hide regional heterogeneity
- JPN: 47 regions; median 31.50%; range Tokyo 22.80% to Akita 38.60%.
- USA: 51 regions; median 17.81%; range Utah 11.99% to Maine 22.54%.
Figure: figures/02_regional_aging_comparison_2022.png (SVG/PDF). Purpose: compare within-country regional spread using the same0–45% scale. Medians weight each administrative unit equally; they are not national population-weighted rates. US states/DC and Japanese prefectures differ in geographic scale.

## Finding 3: regional aging also increased over time
- JPN: median region-level2011–2022 increase 6.61 percentage points; all47 regions increased.
- USA: median region-level2011–2022 increase 4.23 percentage points; all51 regions increased.
Figure: figures/03_regional_aging_change_2011_2022.png (SVG/PDF). Each point compares the same region at two dates. Above-diagonal points indicate increases. Census benchmark/version effects are present; do not label the differences as pure demographic change or causal effects.

## Interpretation boundaries
- USA2011–2019: Census Vintage2020 evaluation estimates (2010 census base). USA2020–2022: fixed Vintage2022 (blended2020 base). Do not treat the2019→2020 break as perfectly continuous. No attempt to interpolate or rescale it.
- Japan2011–2020: official long-term table10, published2022-07-20; includes census benchmarks and intercensal revisions. Japan2021/2022: annual estimates. Dates are October1 versus July1 for USA.
- Japan counts are rounded to1000 persons. Historical2011–2020 rates are calculated from these rounded published counts;2021–2022 rates and dependency ratios use officially published one-decimal values. Tiny rounding differences are expected.
- WPP national rates differ from national-statistics aggregates: in2022 WPP gives USA16.92% and Japan29.40%, while this project's Census aggregate is17.34% and Japan's published rate29.0%. Sources, methods, vintages and reference dates differ. Keep WPP as a separate national context series; do not splice or force agreement.
- Working age=15–64, not employment. Migration/labor, industrial histories, association analysis and poster integration remain with other members.

## Presentation handoff (Member1, approximately3 minutes)
Research question → common-source national trend → within-country regional spread → numerical findings → source/benchmark caveat → transition to Member2 industrial structure. Each figure should be introduced by goal, place, content and message. Final spoken script remains to be tailored to the selected poster and timing.

## Source verification update, 2026-11-09

The original full UN WPP2024 F06 workbook has now been independently retrieved and hash-matched to the original release. All 46 national observations and 276 age-percentage checks pass; findings and figures above remain numerically unchanged. Both-sex de facto population aged 65+ is divided by total population at July1; 2000–2022 uses historical Estimates, not projections. The original product publishes percentages; independent reconstruction from population-count products was not performed. See [verification evidence](independent_verification.json).

Existing U.S. map boundaries and 51 code/name joins are verified against the original Census2022 1:20m file, with 14 multipart regions retained and all 102 population/manufacturing values checked. Insets show Alaska, Hawaii and DC at different scales. These generalized boundaries are suitable for display, not precise geographic analysis. No Japanese boundary map was supplied; the full prefectural ranked chart is the presentation-safe comparison. Keep the source and inset notes if using the U.S. maps in an appendix. Current team selection is in [poster/README.md](../poster/README.md).
