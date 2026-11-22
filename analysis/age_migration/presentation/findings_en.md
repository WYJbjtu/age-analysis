# Age-specific domestic migration: findings for presentation

Status: **READY WITH LIMITATIONS**. Full samples: 47 Japanese prefectures and 51 U.S.
state-level regions in both 2019 and 2022. All primary/supporting rates and aging
outcomes are nonmissing. Equal regional weights; countries always separate.
The plan and case rule were saved before any migration/aging correlations were
inspected. No ordinary p-values or causal contributions are estimated.

## Verified descriptive findings

Japan has a strong negative cross-sectional association between ages 20–24 net
migration per 1,000 same-age residents and the share aged 65+: Pearson
-0.812 in 2019 and -0.820 in 2022. Removing Tokyo gives
-0.784 and
-0.796. All leave-one-region-out
young-adult coefficients remain negative. This is a robust *descriptive regional
association in these two snapshots*, not an estimated cause of accumulated aging.

The U.S. young-adult association is weaker: -0.337 and -0.362; without DC,
-0.155 and
-0.212. DC influences the coefficient,
and ACS sampling uncertainty is substantial. In 2022, 29
positive point estimates include only 8 with
positive intervals under the stated approximation; 35
of 51 intervals include zero. This is not evidence of one common cross-country slope.

Older-adult associations differ. Japan's Pearson is
-0.332 in 2019 and -0.048
in 2022; removing Tokyo changes the latter to
-0.381. Its 2022 leave-one-out
range crosses zero. The U.S. coefficients are
0.135 and 0.439.
Do not claim that all older regions lose young people, that every urban region
attracts all ages, or that the older-adult pattern is stable or identical across years.

Tokyo's 2022 total net migration is +38,023; ages 15–19 contribute
+13,795 and ages 20–24 contribute +57,153.
All other ages combined contribute -32,925. Each checkpoint
matches the independently parsed complete primary tables. Ages 65+ specifically
contribute -9,284; **all other ages is not older adults**.
Only Saitama, Tokyo, Kanagawa, Aichi and Osaka have positive 20–24 net counts in
2022. Tokyo's 2019 total was +82,982;
these annual snapshots are not cumulative migration over 2019–2022.

The pre-specified U.S. case rule selects New Hampshire and DC, the minimum and
maximum 2022 young-rate point estimates, retaining them in 2019. In 2022 New
Hampshire's total ACS net interstate estimate is +2,916 while its ages 20–24 net
estimate is -4,496; DC's total is -3,398 while its ages 20–24 estimate is +5,580.
These are total **point estimates**: both 2022 total intervals include zero.
Their total MOEs and intervals are in `results/case_totals.csv` and Figure 2.
The selected 2022 young-rate intervals exclude zero under the approximation.
New Hampshire's 2019 young interval includes zero. Selection is on noisy point
estimates; these are not proven population ranks or geographical equivalents to Tokyo.

## All planned primary and supporting comparisons

Rates use same-age current residents; outcome is Member 1's verified aging share.
Every Japanese row has 47 eligible/included regions and every U.S. row has 51.
Missing = 0. The 20–34 group is supporting and overlaps its constituent groups.

| country | year | age_group | included | pearson | spearman |
| --- | --- | --- | --- | --- | --- |
| JPN | 2019 | 20-24 | 47 | -0.812245 | -0.836147 |
| JPN | 2022 | 20-24 | 47 | -0.820295 | -0.820461 |
| JPN | 2019 | 65+ | 47 | -0.331999 | -0.522780 |
| JPN | 2022 | 65+ | 47 | -0.048128 | -0.269381 |
| JPN | 2019 | 20-34 | 47 | -0.775870 | -0.716235 |
| JPN | 2022 | 20-34 | 47 | -0.766268 | -0.709308 |
| USA | 2019 | 20-24 | 51 | -0.336607 | -0.257557 |
| USA | 2022 | 20-24 | 51 | -0.362190 | -0.254389 |
| USA | 2019 | 65+ | 51 | 0.134998 | 0.053303 |
| USA | 2022 | 65+ | 51 | 0.439167 | 0.359910 |
| USA | 2019 | 20-34 | 51 | -0.149296 | -0.117919 |
| USA | 2022 | 20-34 | 51 | -0.284913 | -0.249774 |

## Sensitivities, including weak and contrary results

The common-region sample is the full 47/51 in both years, so its coefficients are
identical to the primary results. Total-population-denominator rates are a
different estimand. B01001 aging is an explicitly separate U.S. outcome sensitivity.

| country | year | age_group | variant | pearson | spearman |
| --- | --- | --- | --- | --- | --- |
| JPN | 2019 | 20-24 | without_Tokyo | -0.784075 | -0.826457 |
| JPN | 2019 | 20-24 | alternative_total_denominator | -0.740802 | -0.771161 |
| JPN | 2022 | 20-24 | without_Tokyo | -0.795747 | -0.808488 |
| JPN | 2022 | 20-24 | alternative_total_denominator | -0.741498 | -0.741000 |
| JPN | 2019 | 65+ | without_Tokyo | -0.618748 | -0.618871 |
| JPN | 2019 | 65+ | alternative_total_denominator | -0.372682 | -0.539894 |
| JPN | 2022 | 65+ | without_Tokyo | -0.381206 | -0.354030 |
| JPN | 2022 | 65+ | alternative_total_denominator | -0.084791 | -0.293208 |
| JPN | 2019 | 20-34 | without_Tokyo | -0.737582 | -0.697811 |
| JPN | 2019 | 20-34 | alternative_total_denominator | -0.714313 | -0.614593 |
| JPN | 2022 | 20-34 | without_Tokyo | -0.716846 | -0.689923 |
| JPN | 2022 | 20-34 | alternative_total_denominator | -0.700258 | -0.617008 |
| USA | 2019 | 20-24 | without_DC | -0.155015 | -0.213157 |
| USA | 2019 | 20-24 | alternative_total_denominator | -0.343873 | -0.269683 |
| USA | 2019 | 20-24 | ACS_aging_outcome | -0.340040 | -0.248416 |
| USA | 2022 | 20-24 | without_DC | -0.212467 | -0.210180 |
| USA | 2022 | 20-24 | alternative_total_denominator | -0.368919 | -0.253213 |
| USA | 2022 | 20-24 | ACS_aging_outcome | -0.359549 | -0.233122 |
| USA | 2019 | 65+ | without_DC | 0.105448 | 0.020120 |
| USA | 2019 | 65+ | alternative_total_denominator | 0.117132 | 0.014389 |
| USA | 2019 | 65+ | ACS_aging_outcome | 0.131800 | 0.057466 |
| USA | 2022 | 65+ | without_DC | 0.371127 | 0.324178 |
| USA | 2022 | 65+ | alternative_total_denominator | 0.431321 | 0.405973 |
| USA | 2022 | 65+ | ACS_aging_outcome | 0.432497 | 0.360181 |
| USA | 2019 | 20-34 | without_DC | -0.049198 | -0.067563 |
| USA | 2019 | 20-34 | alternative_total_denominator | -0.182232 | -0.115656 |
| USA | 2019 | 20-34 | ACS_aging_outcome | -0.155567 | -0.111131 |
| USA | 2022 | 20-34 | without_DC | -0.201999 | -0.209700 |
| USA | 2022 | 20-34 | alternative_total_denominator | -0.327549 | -0.249774 |
| USA | 2022 | 20-34 | ACS_aging_outcome | -0.280929 | -0.226606 |

Leave-one-region-out diagnostics use point estimates, not survey-error simulation:

| country | year | age_group | loo_pearson_min | loo_pearson_max | most_influential_region | max_absolute_pearson_change |
| --- | --- | --- | --- | --- | --- | --- |
| JPN | 2019 | 20-24 | -0.857287 | -0.784075 | JP-47 | 0.045041 |
| JPN | 2022 | 20-24 | -0.857555 | -0.795747 | JP-47 | 0.037260 |
| JPN | 2019 | 65+ | -0.618748 | -0.245369 | JP-13 | 0.286749 |
| JPN | 2022 | 65+ | -0.381206 | 0.019931 | JP-13 | 0.333078 |
| JPN | 2019 | 20-34 | -0.793516 | -0.737582 | JP-13 | 0.038288 |
| JPN | 2022 | 20-34 | -0.789505 | -0.716846 | JP-13 | 0.049423 |
| USA | 2019 | 20-24 | -0.418186 | -0.155015 | US-DC | 0.181592 |
| USA | 2022 | 20-24 | -0.445301 | -0.212467 | US-DC | 0.149724 |
| USA | 2019 | 65+ | 0.011110 | 0.194844 | US-AK | 0.123888 |
| USA | 2022 | 65+ | 0.371127 | 0.482118 | US-DC | 0.068040 |
| USA | 2019 | 20-34 | -0.262260 | -0.049198 | US-AK | 0.112965 |
| USA | 2022 | 20-34 | -0.332867 | -0.201999 | US-DC | 0.082913 |

Complete Spearman influence ranges and all 588 deletions are in the CSV results.
Year-to-year rate correlations are in `results/year_comparison.csv`; persistence
across two snapshots is not a statement about all intervening years or a cohort.

## Interpretation and limits

**Plausible interpretation:** age selectivity helps describe how a positive or
negative total can coexist with opposing age-group balances. It is consistent with
different life-course mobility patterns, but motives were not measured here.

**Unmeasured mechanism/contribution:** education, employment, housing, retirement,
births, deaths, international movement, cohort aging and prior migration can all
matter. This design does not identify their causal roles or the fraction of aging
attributable to domestic migration. Low aging relative to other regions does not
mean a region's aging share is declining over time. Net-zero total migration does
not imply unchanged age composition.

Japan counts calendar-year registered inter-prefectural events; ACS estimates
residence changes over each interview's preceding year for ages 1+, including group
quarters. Exact Japanese age-reference day remains unverified. Japanese 2019
denominators use the original annual vintage; Member 1 retains revised aging
stocks. Japanese counts have no ACS-style sampling MOE; population denominators
are rounded. ACS MOEs for net and rates are approximate, include denominator MOE
where available, and omit unavailable covariances. Correlations are not corrected
for survey error, spatial dependence or shared-denominator relationships.

**Poster-safe:** the strong Japanese young-adult descriptive association in both
snapshots; the weaker and DC-sensitive U.S. result; distinct older-adult patterns;
and the age balances concealed by totals. **Not supported:** universal urban rules,
causal explanations, a percentage contribution to aging, or confident signs for
all positive U.S. point estimates. Keep the country-specific sources and limitations.
