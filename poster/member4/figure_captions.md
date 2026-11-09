# Member 4 figure captions

## Figure 1. Pooled and within-country aging–manufacturing associations, 2022

One dot represents a U.S. state/DC or a Japanese prefecture. The sample is complete: 98 pooled, 51 USA, 47 Japan. Both variables are percentages on identical axes across panels; lines are descriptive least-squares fits restricted to observed aging ranges, with no extension across the gap between country supports. USA is blue and Japan purple, matching Members 1 and 2. Pooled Pearson r=0.644435 (Spearman 0.610267), compared with USA r=0.003224 (−0.012036) and Japan r=0.028647 (−0.084724). Pearson shows attenuation without reversal. Spearman has a nominal sign reversal, but weak within-country magnitudes and an unstable U.S. sign preclude a robust reversal headline. Each region is equally weighted. No region is omitted or imputed.

Population sources: [Census Vintage 2022, SC-EST2022-ALLDATA6](https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/asrh/sc-est2022-alldata6.csv) and [Japan Population Estimates 2022, table 12](https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040045498&fileKind=0). Industry sources: [BEA SAGDP2, September 30, 2026 release](https://apps.bea.gov/regional/zip/SAGDP.zip) and [Cabinet Office nominal prefectural accounts, FY2011–FY2022 release](https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2022/syuyo1.xlsx). U.S. population is July 1 and GDP CY2022; Japanese population is October 1 and GDP FY2022, April 2022–March 2023. Administrative scale and timing differ. Correlation is descriptive, not causal.

Files: `analysis/member4/figures/01_pooled_within_2022.svg` and `.png`. Data: `data/core_2022.csv`; results: `results/primary_summary.csv` and `associations.csv` under the same Member 4 directory.

## Figure 2. Year/method robustness and covariance decomposition

Left: Pearson (circles) and Spearman (squares), with open markers for 2019 and filled markers for 2022. Both years contain the same 98 regions, including 51 USA and 47 Japan, with equal weights. Pooled Pearson is 0.618710 in 2019 and 0.644435 in 2022; country-specific estimates remain weak. Marker offsets aid reading and have no quantitative meaning. These are point summaries, not significance tests.

Right: 2022 pooled covariance 46.113322 pp² equals within-country 0.416441 plus between-country 45.696881. Country contributions use n_c/N and covariance denominator N. Thus 99.0969% of the pooled covariance is between country means; this fraction is not R², a causal explanation or a confidence measure. Numerical reconstruction error is below 1e-12 pp².

Sources are those of Figure 1, plus [Census Vintage 2020 evaluation estimates for 2019](https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/state/asrh/SC-EST2020-ALLDATA6.csv) and [Japan historical population table 10](https://www.e-stat.go.jp/stat-search/file-download?statInfId=000013168610&fileKind=4). The industry workbooks also provide CY/FY2019. Census reference-base changes and Japan's rounded historical counts constrain temporal interpretation.

Files: `analysis/member4/figures/02_robustness_and_covariance.svg` and `.png`. Results: `associations.csv`, `covariance_components.csv`, `covariance_summary.csv`; exact samples in `data/analysis_samples.csv`.

## Figure 3. Similar-age regional cases selected by a transparent rule

We enumerate all within-country 2022 pairs whose aging shares differ by at most 0.5 percentage points, then select each country's largest and smallest manufacturing gaps. Points show manufacturing shares on common percentage axes; connecting lines only identify pairs. Labels report both displayed percentages. Eight distinct regions are shown, selected from all 98 primary observations. Largest-gap pairs: Indiana–Nevada (aging gap 0.014336 pp; manufacturing gap 20.677317 pp) and Hokkaido–Toyama (0.2 pp; 22.812522 pp). Smallest-gap contrasts are Kansas–Mississippi and Fukui–Saga, with manufacturing gaps of 0.125289 and 0.113397 pp. The eligible set contains 210 U.S. pairs and 102 Japanese pairs.

These deliberately selected examples are not representative estimates or matched causal controls. All eligible pairs are exported, so contrary cases remain visible. There is no cross-country overlap in aging values in either main year. The plot therefore compares regions within countries. Sources and statistical periods are the same as Figure 1; no labor or migration variable determines selection.

Files: `analysis/member4/figures/03_within_country_cases.svg` and `.png`. Data: `results/selected_cases.csv`; complete selection frame: `results/case_candidate_pairs.csv`.
