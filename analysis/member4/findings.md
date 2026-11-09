# Member 4 numerical findings

## Main result

The strong positive pooled aging–manufacturing association is almost absent within each country. This is aggregation-driven attenuation, not a robust direction reversal. All 98 regions are present in 2019 and 2022, with no primary exclusions. Each region has equal weight.

Pearson does not reverse direction in 2022. Spearman has a nominal sign reversal (+0.610267 pooled versus -0.012036 USA and -0.084724 Japan), but both within-country magnitudes are below 0.10 and the USA rank sign changes under omission. This weak rank pattern is explicitly retained; it does not support a robust Simpson-paradox headline.

| year | group | n | pearson | spearman | slope | x_min | x_max | y_min | y_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | Pooled | 98 | 0.618710 | 0.581062 | 0.806249 | 11.392956 | 36.831276 | 0.170056 | 43.663808 |
| 2019 | USA | 51 | 0.040097 | 0.021357 | 0.097864 | 11.392956 | 21.192403 | 0.170056 | 25.267702 |
| 2019 | JPN | 47 | -0.009533 | -0.118062 | -0.027857 | 22.093023 | 36.831276 | 4.232736 | 43.663808 |
| 2022 | Pooled | 98 | 0.644435 | 0.610267 | 0.868783 | 11.985329 | 38.600000 | 0.230998 | 41.750933 |
| 2022 | USA | 51 | 0.003224 | -0.012036 | 0.007432 | 11.985329 | 22.537716 | 0.230998 | 25.085347 |
| 2022 | JPN | 47 | 0.028647 | -0.084724 | 0.079762 | 22.800000 | 38.600000 | 4.035634 | 41.750933 |

The x variable is the percentage of total residents aged 65+. The y variable is manufacturing nominal value added as a percentage of nominal regional GDP. Slopes measure percentage points of manufacturing share per percentage point of aging. No inferential p-values or intervals are used. Administrative units are geographically dependent and not assumed to be independent random draws.

## Aggregation

| n | denominator | pooled_covariance | within_covariance | between_covariance | reconstruction_error | between_fraction | year | classification_method | classification | spearman_classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 98 | N | 41.490493 | 0.079793 | 41.410701 | 0.000000 | 0.998077 | 2019 | Pearson | weak within-country estimate; no strict reversal headline | weak within-country estimate; no strict reversal headline |
| 98 | N | 46.113322 | 0.416441 | 45.696881 | -0.000000 | 0.990969 | 2022 | Pearson | weak within-country estimate; no strict reversal headline | nominal sign reversal; weak estimate requires caution |

Using denominator N, pooled covariance equals the sum of country-count-weighted within-country covariance and covariance of country means. For 2022, 46.113322 = 0.416441 + 45.696881 pp², up to numerical precision. The between-country share is 99.0969%. This is an arithmetic description, not causal attribution or R². Country-demeaned Pearson is 0.021646 (slope 0.057240). Additive country indicators remove mean differences, not all confounding and not slope heterogeneity.

## Robustness

| year | group | variant | n | pearson | spearman | slope |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | Pooled | population_weighted | 98 | 0.568006 |  | 0.746839 |
| 2019 | Pooled | without_DC | 97 | 0.608260 | 0.568352 | 0.789649 |
| 2019 | USA | population_weighted | 51 | -0.139877 |  | -0.300718 |
| 2019 | USA | without_DC | 50 | -0.060073 | -0.036158 | -0.147356 |
| 2019 | JPN | population_weighted | 47 | 0.287766 |  | 0.828611 |
| 2019 | Country-demeaned | country_adjusted | 98 | 0.004491 | -0.078694 | 0.012471 |
| 2022 | Pooled | population_weighted | 98 | 0.591728 |  | 0.816877 |
| 2022 | Pooled | without_DC | 97 | 0.634653 | 0.598508 | 0.853695 |
| 2022 | USA | population_weighted | 51 | -0.184342 |  | -0.383511 |
| 2022 | USA | without_DC | 50 | -0.103162 | -0.071309 | -0.240348 |
| 2022 | JPN | population_weighted | 47 | 0.322449 |  | 0.875192 |
| 2022 | Country-demeaned | country_adjusted | 98 | 0.021646 | -0.073149 | 0.057240 |

Available and common-region samples are identical (98, including USA 51 / Japan 47). Excluding DC is a sensitivity, not the primary specification. Population weighting changes the estimand toward the regional environment of residents; it is still ecological and does not estimate an individual-level relation. Weighted 2022 correlations are -0.184342 USA and +0.322449 Japan, so near-zero equal-region results must not be presented as universal absence of association.

| year | group | pearson_min | pearson_max | spearman_min | spearman_max | slope_min | slope_max | positive | negative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | JPN | -0.154797 | 0.071648 | -0.192599 | -0.071230 | -0.469474 | 0.200824 | 12 | 35 |
| 2019 | Pooled | 0.607263 | 0.643531 | 0.568352 | 0.611587 | 0.784656 | 0.847517 | 98 | 0 |
| 2019 | USA | -0.060073 | 0.092784 | -0.036158 | 0.071501 | -0.147356 | 0.233236 | 49 | 2 |
| 2022 | JPN | -0.098781 | 0.095995 | -0.156935 | -0.038740 | -0.278725 | 0.261135 | 44 | 3 |
| 2022 | Pooled | 0.634533 | 0.667046 | 0.598508 | 0.633671 | 0.848699 | 0.909313 | 98 | 0 |
| 2022 | USA | -0.103162 | 0.050544 | -0.071309 | 0.036927 | -0.240348 | 0.114605 | 35 | 16 |

Both within-country signs change when individual regions are omitted. These leave-one-out ranges are influence diagnostics, not confidence intervals. The pooled sign remains positive in every omission. No outliers were deleted from the primary analysis.

## Observed support

| year | variable | USA_min | USA_max | JPN_min | JPN_max | overlap_min | overlap_max | gap_if_disjoint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | age65_share_pct | 11.392956 | 21.192403 | 22.093023 | 36.831276 |  |  | 0.900620 |
| 2019 | manufacturing_share_pct | 0.170056 | 25.267702 | 4.232736 | 43.663808 | 4.232736 | 25.267702 | 0.000000 |
| 2022 | age65_share_pct | 11.985329 | 22.537716 | 22.800000 | 38.600000 |  |  | 0.262284 |
| 2022 | manufacturing_share_pct | 0.230998 | 25.085347 | 4.035634 | 41.750933 | 4.035634 | 25.085347 | 0.000000 |

The aging intervals do not overlap in either year. A nearest cross-country pair is not a common-support matched-age design. All selected cases are within-country. Industry ranges do overlap. Lines are restricted to each observed aging interval.

## Context and limited change analysis

| year | group | y | n | pearson | spearman | slope |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | JPN | services_share_pct | 47 | -0.159472 | -0.055389 | -0.409202 |
| 2019 | JPN | unemployment_rate_pct | 47 | -0.264707 | -0.286240 | -0.032246 |
| 2019 | JPN | domestic_net_migration | 47 | -0.540778 | -0.380550 | -2546.506888 |
| 2019 | USA | services_share_pct | 51 | 0.220070 | 0.242534 | 0.720349 |
| 2019 | USA | unemployment_rate_pct | 51 | -0.193386 | -0.063610 | -0.079236 |
| 2019 | USA | domestic_net_migration | 51 | 0.075749 | 0.029683 | 2114.274427 |
| 2022 | JPN | services_share_pct | 47 | -0.218856 | -0.053899 | -0.565807 |
| 2022 | JPN | unemployment_rate_pct | 47 | -0.460084 | -0.442502 | -0.060567 |
| 2022 | JPN | domestic_net_migration | 47 | -0.552758 | -0.380071 | -1480.509960 |
| 2022 | USA | services_share_pct | 51 | 0.214760 | 0.223167 | 0.779152 |
| 2022 | USA | unemployment_rate_pct | 51 | -0.054091 | 0.004942 | -0.019555 |
| 2022 | USA | domestic_net_migration | 51 | 0.075851 | 0.014570 | 3367.088961 |

Services remain country-specific. US private services exclude government; Japan's tertiary total includes public activities. Labor populations are USA civilian noninstitutional 16+ and Japan 15+. Unemployment rates use labor force, not total population, as their denominator. Domestic migration is an annual person count, not a rate; no population denominator has been invented. US migration is July-to-July, Japan calendar-year registration. Large-region scaling can affect migration correlations. None of these variables is used as an automatic regression control or as evidence about migrants' ages.

| group | period | n_input | n | excluded_missing | x_min | x_max | y_min | y_max | pearson | spearman | slope | intercept | covariance | weighting | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JPN | 2019 to 2022 | 47 | 47 | 0 | 0.082787 | 1.768724 | -2.572793 | 5.431321 | 0.162627 | 0.098867 | 0.676946 | 0.276684 | 0.091399 | equal regions | ok |
| USA | 2019 to 2022 | 51 | 51 | 0 | 0.378103 | 1.580863 | -3.610494 | 2.353726 | 0.100620 | 0.020271 | 0.352596 | -0.511975 | 0.027251 | equal regions | ok |

Change analysis uses one 2019–2022 difference per region: Pearson 0.100620 USA and 0.162627 Japan. US population reference-base changes and nominal share price effects limit interpretation. A pooled independent-observation panel regression and country-clustered inference were not attempted.

## Evidence and interpretation

Observed: country means account for most of the pooled covariance, while country-specific equal-region linear relationships are near zero and unstable. Interpretation: the cross-country gap should not be read as a common regional gradient. Hypotheses for future investigation: urban concentration, industrial history, and selective migration might jointly influence these regional patterns. These hypotheses are not tested mechanisms or causal conclusions.

Principal figure: figures/01_pooled_within_2022.svg. Robustness/decomposition: figures/02_robustness_and_covariance.svg. Cases: figures/03_within_country_cases.svg. All have 300-dpi PNG companions and captions in poster/member4/figure_captions.md. Exact results are in results/associations.csv, covariance_summary.csv, influence_summary.csv, selected_cases.csv and case_candidate_pairs.csv. Every analysis has a ledger entry and sample membership in data/analysis_samples.csv.

Provenance: canonical input hashes and commits in audit/input_manifest.json and repository_inventory.csv; official URLs, retrieval times and hashes in audit/download_manifest.json; 15,027 field-level source checks in audit/source_record_checks.csv, all passed within source-precision tolerances. These include exhaustive regional population and industry checks, exhaustive Japanese labor and selected migration years, all US migration years, and a six-state BLS sample in each main year. National WPP and remaining US labor years are not independently verified.
