# Industry findings: United States CY2022 and Japan FY2022

## Sources and coverage
Data: [industry.csv](../data/processed/industry.csv), with 51 US states/DC and 47 Japanese prefectures. All 98 records contain both industry shares, their nominal value-added numerators, nominal GDP and reference-period labels. There are no duplicate region/year keys or missing required values. No imputation is used.

The 51 existing US records were rechecked against the original BEA SAGDP2 release and preserved. Japan values were extracted from the Cabinet Office's FY2022 nominal prefectural accounts and checked against its separate GDP summary workbook. The files, exact download URLs and hashes are recorded in [sources.csv](sources.csv) and [source_manifest.json](source_manifest.json). Results below are reproduced in [summary.json](summary.json).

## Finding 1: the typical prefecture has a higher manufacturing share

The unweighted regional median manufacturing share is **25.20% in Japan** and **9.65% in the United States**, a difference of **15.54 percentage points** before rounding. These describe the 47 and 51 administrative units in this dataset; they are not national manufacturing shares or population/GDP-weighted estimates.

Figure: [manufacturing distribution](figures/manufacturing_distribution_2022.png), with [editable SVG](figures/manufacturing_distribution_2022.svg). Each dot represents one region; the band spans the middle 50% and the line marks the median. Vertical jitter only separates points; it has no statistical meaning.

Limitation: Japan uses FY2022, while the United States uses CY2022. Industry definitions and administrative-unit sizes differ. The comparison is descriptive and does not establish that aging explains the difference.

## Finding 2: substantial industrial variation exists within each country

Manufacturing shares range from **4.04% in Okinawa to 41.75% in Shiga** in Japan, and from **0.23% in the District of Columbia to 25.09% in Indiana** in the United States. The national label alone therefore hides considerable regional variation. DC is a federal district, not a state; its inclusion follows the team's 51-region contract.

Figures: [Japan composition](figures/jpn_industry_composition_2022.png) and [US composition](figures/usa_industry_composition_2022.png), both accompanied by same-name SVG files. All regions are shown and ranked within country by manufacturing share. The grey remainder is GDP minus manufacturing and the selected service aggregate; it is not a single homogeneous industry.

## Service-sector context: separate country interpretations

- **United States, private services:** median **68.99%**; range **49.85% in North Dakota to 83.09% in New York**. This BEA aggregate includes utilities and excludes government and government enterprises.
- **Japan, tertiary industries:** median **67.28%**; range **52.09% in Shiga to 89.01% in Tokyo**. This published aggregate includes utilities, public administration, education and health/social services.

These are different statistical aggregates. **Do not subtract these medians, rank both countries together by services, or fit a pooled services relationship.** The two composition figures support within-country interpretation only. Manufacturing is the focus of the cross-country chart.

## Definitions and limitations
Shares are `100 × nominal industry value added / nominal regional GDP`. US monetary values are millions of current USD; Japan values are millions of current JPY. Do not compare the currency amounts directly. Japan's GDP denominator includes import taxes/duties less consumption tax on gross capital formation, so the sum of industry value added can differ from GDP. The remainder explicitly retains these accounting adjustments.

The source values are revised estimates, not an untouched 2022 publication vintage. BEA is the September 30, 2026 revision, NAICS 2017; Japan is the 2008SNA / 2015-benchmark FY2011–FY2022 series downloaded on November 5, 2026. FY2022 is April 2022–March 2023. No claim is made that this Japanese series is the latest available vintage.

The US definition and official footnotes are in [BEA's SAGDP download](https://apps.bea.gov/regional/zip/SAGDP.zip). Japan's published tertiary aggregate is in [the Cabinet Office nominal industry workbook](https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2022/syuyo1.xlsx); its component list is also documented by [Osaka Prefecture](https://www.pref.osaka.lg.jp/o040090/toukei/gdp/area.html).

Japanese demographic records are not yet in the shared population table at this handoff. Member 4 can merge the industry data after Member 1 supplies them. No Japanese aging–industry relationship, causal effect, or Simpson's paradox has been estimated here.

## Suggested presentation narration

“We measure industrial structure using value-added shares rather than comparing dollar and yen amounts. The median Japanese prefecture has a manufacturing share of about 25%, compared with about 10% across US states and DC. There is also substantial variation within each country: Shiga and Indiana are manufacturing-intensive, while Tokyo and DC have much smaller manufacturing shares. These differences provide context for the team's later aging analysis. We show services separately because the US measure excludes government, whereas Japan's tertiary aggregate includes public services. Our findings describe regional economic structure; they do not imply that population aging causes these patterns.”
