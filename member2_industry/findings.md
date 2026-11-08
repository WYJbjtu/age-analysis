# Industry findings: United States CY2011–CY2022 and Japan FY2011–FY2022

## Sources and coverage
Data: [industry.csv](../data/processed/industry.csv), a balanced 12-year panel with 51 US states/DC and 47 Japanese prefectures in every year from 2011 through 2022. All **1,176 records** (612 US, 564 Japan) contain both industry shares, their nominal value-added numerators, nominal GDP and reference-period labels. There are no duplicate region/year keys or missing values. No interpolation, imputation or copying of 2022 values into earlier years is used.

All US years are extracted directly from the 2011–2022 columns of one pinned BEA SAGDP2 release. All Japanese years come from the corresponding annual worksheets in one Cabinet Office prefectural-accounts release; all 564 GDP denominators match its separate summary workbook. The 2022 monetary values are unchanged from the earlier delivery; shares are now consistently calculated to ten decimal places. The files, exact download URLs and hashes are recorded in [sources.csv](sources.csv) and [source_manifest.json](source_manifest.json). Annual medians and quartiles are in [trend_summary.csv](trend_summary.csv); [summary.json](summary.json) retains the 2022 cross-section summary.

## Finding 1: regional manufacturing medians diverged over 2011–2022

| Regional manufacturing share | 2011 median | 2022 median | Change in annual median |
| --- | ---: | ---: | ---: |
| United States (calendar years) | 11.17% | 9.65% | −1.52 percentage points |
| Japan (fiscal years) | 21.32% | 25.20% | +3.87 percentage points |

Figure: [manufacturing trend, 2011–2022](figures/manufacturing_trend_2011_2022.png), with [SVG](figures/manufacturing_trend_2011_2022.svg). The plot uses all 12 observed years, with one country-specific median per year and a shaded interquartile range. The endpoint comparison summarizes the overall direction, not a monotonic annual change. Differences are calculated before rounding.

Each region receives equal weight; these are not national manufacturing shares. The shaded bands show variation among regions, not confidence intervals. A difference between two annual medians is not the median of individual regions' changes. These descriptive trends do not establish a relationship with aging. Changes in nominal shares can reflect relative prices and changes in other GDP components, rather than changes in real production alone.

## Finding 2: the typical prefecture has a higher manufacturing share in 2022

The unweighted regional median manufacturing share is **25.20% in Japan** and **9.65% in the United States**, a difference of **15.54 percentage points** before rounding. These describe the 47 and 51 administrative units in this dataset; they are not national manufacturing shares or population/GDP-weighted estimates.

Figure: [manufacturing distribution](figures/manufacturing_distribution_2022.png), with [editable SVG](figures/manufacturing_distribution_2022.svg). Each dot represents one region; the band spans the middle 50% and the line marks the median. Vertical jitter only separates points; it has no statistical meaning.

Limitation: Japan uses FY2022, while the United States uses CY2022. Industry definitions and administrative-unit sizes differ. The comparison is descriptive and does not establish that aging explains the difference.

## Finding 3: substantial industrial variation exists within each country in 2022

Manufacturing shares range from **4.04% in Okinawa to 41.75% in Shiga** in Japan, and from **0.23% in the District of Columbia to 25.09% in Indiana** in the United States. The national label alone therefore hides considerable regional variation. DC is a federal district, not a state; its inclusion follows the team's 51-region contract.

Figures: [Japan composition](figures/jpn_industry_composition_2022.png) and [US composition](figures/usa_industry_composition_2022.png), both accompanied by same-name SVG files. All regions are shown and ranked within country by manufacturing share. The grey remainder is GDP minus manufacturing and the selected service aggregate; it is not a single homogeneous industry.

## Service-sector context: separate country interpretations

- **United States, private services:** regional median rises from **65.82% in 2011 to 68.99% in 2022**, a change of **+3.16 percentage points**. The 2022 range is **49.85% in North Dakota to 83.09% in New York**. This BEA aggregate includes utilities and excludes government and government enterprises. [US service trend](figures/usa_services_trend_2011_2022.png), with [SVG](figures/usa_services_trend_2011_2022.svg).
- **Japan, tertiary industries:** regional median falls from **69.90% in FY2011 to 67.28% in FY2022**, a change of **−2.62 percentage points**. The 2022 range is **52.09% in Shiga to 89.01% in Tokyo**. This published aggregate includes utilities, public administration, education and health/social services. [Japan service trend](figures/jpn_services_trend_2011_2022.png), with [SVG](figures/jpn_services_trend_2011_2022.svg).

These are different statistical aggregates. **Do not subtract the countries' service medians or changes, rank both countries together by services, or fit a pooled services relationship.** The service-trend and composition figures support within-country interpretation only. Manufacturing is the focus of the cross-country charts. All six figures are generated from the CSV by Python/Matplotlib, not manually drawn or generated by an image model.

## Definitions and limitations
Shares are `100 × nominal industry value added / nominal regional GDP`. US monetary values are millions of current USD; Japan values are millions of current JPY. Do not compare the currency amounts directly. Japan's GDP denominator includes import taxes/duties less consumption tax on gross capital formation, so the sum of industry value added can differ from GDP. The remainder explicitly retains these accounting adjustments.

The source values are revised estimates, not an untouched 2022 publication vintage. BEA is the September 30, 2026 revision, NAICS 2017; Japan is the 2008SNA / 2015-benchmark FY2011–FY2022 series downloaded on November 5, 2026. FY2022 is April 2022–March 2023. No claim is made that this Japanese series is the latest available vintage.

The US definition and official footnotes are in [BEA's SAGDP download](https://apps.bea.gov/regional/zip/SAGDP.zip). Japan's published tertiary aggregate is in [the Cabinet Office nominal industry workbook](https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2022/syuyo1.xlsx); its component list is also documented by [Osaka Prefecture](https://www.pref.osaka.lg.jp/o040090/toukei/gdp/area.html).

Update 2026-11-08: the population, industry and labor/migration tables now share the same 1,176 region/year keys for 2011–2022. A temporary run of the existing merge script matches all records without missing values. The stored shared merge and correlation figures remain owned by Member 4 and have not been overwritten. Matching the year key does not harmonize CY and FY timing: Japanese FY2022 runs from April 2022 through March 2023. A longitudinal association analysis also needs to account for repeated observations of each region; simply pooling all years does not identify a temporal or causal effect. No aging–industry causal effect or Simpson's paradox has been estimated here.

## Suggested presentation narration

“Our industry panel now covers the same 98 regions and 12 years as the population and labor modules. Between 2011 and 2022, the median manufacturing share declines from about 11.2% to 9.7% across US states and DC, while increasing from about 21.3% to 25.2% across Japanese prefectures. These are equal-weight regional medians, with substantial variation within each country. We measure shares of nominal regional GDP and retain the distinction between US calendar years and Japanese fiscal years. Services are shown separately because US private services exclude government, while Japan's tertiary aggregate includes public services. These patterns describe industrial structure and provide context for the team's aging analysis; they do not show that population aging causes the changes.”
