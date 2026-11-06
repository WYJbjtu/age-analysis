# USA 2022 findings

## Sources and coverage
51 states/DC; JPN not provided. Exact sources and reference periods: sources.csv. Data: ../data/processed/merged_analysis.csv.

## Finding 1
65+ population share: minimum US-UT = 11.9853; maximum US-ME = 22.5377.

## Finding 2
Median 65+ population share across 51 equally weighted regions = 17.8076. This is not a national population-weighted statistic.

## Figures
Existing age/manufacturing maps and ranked plots: ../handover/us_2022/deliverables/figures/. Migration case figure and cross-country trend are pending; no migration figure claimed.

## Definitions and limitations
Population date July 1, 2022; working age 15-64; old-age dependency ratio = 100*65+/15-64. Economic amounts are millions of current USD, CY2022, BEA September 30, 2026 revision. services_share_pct = SAGDP2 line 92 / line 1 * 100: private services including utilities, excluding government. It is not an agreed harmonized US-Japan tertiary-sector measure; Japan definition must be aligned before cross-country service comparisons. Net migration is total domestic plus international net migration over July 1, 2021–July 1, 2022, not population change. Employment and unemployment remain missing because no verified labor input was supplied. No causal interpretation. National UN trends, Japanese records and case selection remain pending.


## Japan 2022 completion
47 prefectures; no missing demographic core fields. Published age65 shares range from 22.8% in Tokyo to 38.6% in Akita; unweighted median 31.5%. National benchmark: 124,947,000 total residents; 36,236,000 aged 65+; published national share 29.0%. Official counts are rounded to thousands; official published rates and dependency ratios are used instead of recomputing from rounded counts. Working-age definition 15–64. Reference date October 1, 2022; US reference July 1.

Figure: figures/jpn_aging_ranked_2022.png (SVG also provided). Script: plot_japan_population.py. Counts and dates: jpn_population_detail_2022.csv. Preparation: python member1_demographics/prepare_japan.py --download. Japanese migration and labor indicators are not provided; national UN time series remain pending.
