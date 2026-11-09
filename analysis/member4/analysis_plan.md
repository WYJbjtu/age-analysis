# Member 4 execution plan

Recorded 2026-11-09 before new relationship calculations. This is an execution plan, not formal preregistration.

Primary question: does the descriptive association between population aged 65+ (%) and manufacturing nominal value added / nominal regional GDP (%) change when the 2022 regional sample is separated by country?

Use canonical 98-region lookup (51 USA including DC, 47 JPN), unique country/region/year keys. Exclude national totals. Primary results give regions equal weight. Join optional context on the left and use separate complete-case samples. No imputation, rescaling or interpolation. Retain Japan FY GDP versus October population and US CY GDP versus July population.

Calculate pooled and country-specific Pearson, rank-based Spearman, OLS descriptive slopes, sample sizes and ranges. Decompose covariance with denominator N into count-weighted within-country and between-country components; numerically verify their sum. Report country-demeaned correlation as an additive-country-adjusted description, not causal identification or equal-slope evidence. No p-values or confidence intervals: these administrative units are not independent random samples.

Sensitivities: 2019; common-region versus available samples; Pearson versus Spearman; USA without DC with full sample primary; leave-one-region-out; population-weighted Pearson/slope as a different regional estimand using canonical resident counts. Keep all results, including weak and contrary ones. Check overlap before making any cross-country matched-age comparison. A strict reversal requires pooled sign opposite both country signs; also flag correlations below 0.10 magnitude as weak and report sign stability under leave-one-out. The 0.10 flag is a communication rule, not a significance threshold.

Optional extensions: within-country services only (definitions differ); within-country aging/unemployment and domestic migration only where source audit passes. Do not use these as automatic regression controls. Annual industry/aging relationships and 2019–2022 changes may be reported if sources support them; never treat repeated region-years as independent draws. Census benchmark breaks remain limitations.

Cases: within each country enumerate every 2022 pair within 0.5 percentage points in aging. Select the pair with largest manufacturing gap and a contrasting pair with smallest gap (tie-break by region IDs). Export all eligible pairs to expose selection. These are illustrations, not controls or evidence of mechanisms.

All teammate-owned files remain unchanged. Audit and adapters live in analysis/member4; presentation sections in poster/member4. Original checkout: 10c5a4792a22abedd40347d019e879d848b61dd5. Clean branch created from inspected origin/main 2bede5baa1c8dcc308ed29985cbccc20527d6d11; all teammate feature work already merged upstream. No automatic commits or remote writes.
