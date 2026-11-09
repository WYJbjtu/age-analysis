# Integration and regional associations

We integrated the canonical demographic, industry, and labor/migration tables using unique country–region–year identifiers. The project contains 50 U.S. states and Washington, D.C., plus 47 Japanese prefectures. All three tables contain 1,176 matched observations over 2011–2022. Our primary aging–manufacturing analysis uses 2022, with 2019 as the declared comparison. Each cross-section contains all 98 regions; the common-region sample is identical to the available sample. National totals are excluded. Optional contextual indicators do not determine inclusion in the primary sample.

The main variables are residents aged 65 and over as a percentage of total residents, and nominal manufacturing value added as a percentage of nominal regional GDP. We independently checked all regional population and industry records against pinned official source files. U.S. population refers to July 1 and Japan to October 1. U.S. GDP uses calendar years; Japan FY2022 spans April 2022–March 2023. Shares use same-unit nominal numerators and denominators. They measure output composition, not manufacturing employment or real-output growth.

Each region receives equal weight in the primary analysis. We report Pearson and Spearman correlations and descriptive linear slopes. We do not interpret administrative regions as independent random draws, and report no significance tests or confidence intervals.

| Year and sample | n | Pearson r | Spearman ρ | Slope, pp per pp |
| --- | ---: | ---: | ---: | ---: |
| 2022 pooled | 98 | 0.644 | 0.610 | 0.869 |
| 2022 United States | 51 | 0.003 | −0.012 | 0.007 |
| 2022 Japan | 47 | 0.029 | −0.085 | 0.080 |
| 2019 pooled | 98 | 0.619 | 0.581 | 0.806 |
| 2019 United States | 51 | 0.040 | 0.021 | 0.098 |
| 2019 Japan | 47 | −0.010 | −0.118 | −0.028 |

The positive pooled pattern nearly disappears within countries (Figure 1). In 2022 the Pearson coefficients have the same positive sign, while both within-country estimates are close to zero. In 2019 the within-country directions differ, again with very small Pearson coefficients. These results support aggregation-driven attenuation, not a robust Simpson-type direction reversal.

The 2022 Spearman coefficients do have opposite pooled and within-country signs. We retain this nominal rank reversal, but its country magnitudes are small and the U.S. rank sign changes under leave-one-out checks. It does not support a robust paradox headline.

To explain the aggregation arithmetically, we decomposed pooled covariance using denominator N and weights 51/98 and 47/98. In 2022, pooled covariance is 46.113322 pp²: the within-country component is 0.416441 and the between-country component 45.696881. Thus 99.0969% of pooled covariance is between country means (Figure 2). This is neither a causal attribution nor a percentage of variance explained. Removing additive country means from both variables leaves Pearson r=0.021646. This adjustment does not remove all confounding or demonstrate identical country slopes.

The common sample, comparison year and rank correlations support the main interpretation. Dropping DC changes the U.S. 2022 Pearson coefficient to −0.103 (n=50), while the full sample remains primary. Leave-one-region-out correlations range from −0.103 to 0.051 in the United States and −0.099 to 0.096 in Japan. These are influence ranges, not uncertainty intervals. Population weighting changes the estimand and yields −0.184 and +0.322, respectively; weak equal-region associations therefore do not prove that all forms of relationship are absent. A limited 2019–2022 change analysis gives Pearson r=0.101 for the United States and 0.163 for Japan, with census-base and nominal-price caveats.

The countries' aging ranges do not overlap: 11.985–22.538% in the United States versus 22.8–38.6% in Japan in 2022. We therefore select cases within countries. Among all pairs within 0.5 percentage points in aging, Indiana–Nevada and Hokkaido–Toyama have the largest manufacturing gaps, 20.677 and 22.813 percentage points. We also show the smallest-gap pairs as contrasts (Figure 3). These cases demonstrate heterogeneity; they do not isolate industrial structure as a causal mechanism.

Services, labor and domestic migration are contextual analyses within countries. Service definitions differ, labor populations cover ages 16+ versus 15+, and migration periods differ. We preserve the original migration fields and add a separately verified domestic measure for 2019/2022. Japan's 2011–2017 migration source covers Japanese nationals only, preventing a continuous all-resident history. Migration totals do not identify migrants' ages.

Our observed result is that national grouping strongly changes the interpretation of regional aging–manufacturing associations. Industrial history, urban concentration and selective migration are plausible future research hypotheses, not mechanisms established by this study.

Evidence: `analysis/member4/results/primary_summary.csv`, `covariance_summary.csv`, `associations.csv`, `influence_summary.csv`, `selected_cases.csv`; input and source hashes in `analysis/member4/audit/`. Exact source URLs and releases are in the figure captions and verification log.
