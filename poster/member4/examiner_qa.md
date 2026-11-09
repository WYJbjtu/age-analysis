# Five likely examiner questions

**1. Is this Simpson's paradox?**

We do not claim a robust direction reversal. In 2022 the pooled Pearson correlation is positive, 0.644435, and both country-specific coefficients are also positive but near zero: 0.003224 and 0.028647. Spearman has a nominal sign reversal: +0.610267 pooled versus -0.012036 USA and -0.084724 Japan. However, both within-country rank magnitudes are small; USA leave-one-out Spearman spans -0.071309 to +0.036927. In 2019 the country Pearson coefficients have different signs, again close to zero. The supported finding is aggregation-driven attenuation, with the weak rank-sign pattern reported openly. Source: `results/primary_summary.csv`, `influence_summary.csv`.

**2. What does “99.1% between countries” mean? Does country explain 99.1% of manufacturing?**

It is a decomposition of the covariance of aging and manufacturing share, not of manufacturing variance. Using denominator N, 2022 covariance is 46.113322 pp², of which 45.696881 is the between-country term and 0.416441 the within-country term. The weights are 51/98 and 47/98. This is arithmetic, not R² or causal attribution. Subtracting each country's means leaves r=0.021646; it does not remove all confounders or establish common slopes. Source: `results/covariance_components.csv`, `covariance_summary.csv`, `associations.csv`.

**3. Why equal weights, and does DC drive the result?**

The primary question concerns regional units, so each state/DC or prefecture has one observation. DC follows the established 51-unit U.S. contract and remains in the primary result. Without it, U.S. r changes from 0.003224 to −0.103162 (n=50), while pooled r remains 0.634653 (n=97). Population-weighted U.S./Japan correlations are −0.184342/+0.322449; these describe a different distribution of regional environments and are still ecological. We report them openly rather than selecting the strongest specification. Source: `results/associations.csv`.

**4. Are the data truly comparable across countries and years?**

The main pair uses resident 65+ shares and nominal manufacturing value added / nominal GDP, with all 98 regions in both 2019 and 2022 and verified primary inputs. Important differences remain: July versus October population, calendar versus fiscal GDP, industry classifications, regional scale and census benchmarks. Services are not pooled because the U.S. aggregate excludes government while Japan's includes public activities. Original U.S. total migration is preserved; our separate domestic measure still has different reference periods from Japan. Japanese migration before 2018 is Japanese-only in the source used here. Source: `audit_report.md`, `audit/source_record_checks.csv`, `data_dictionary.md`.

**5. Can these results show aging causes industrial change, or prove there is no within-country relationship?**

Neither. Near-zero equal-region correlations do not rule out nonlinear, weighted, individual-level or confounded relationships. Administrative regions are geographically dependent; we do not report conventional independent-sample significance tests. The 2019–2022 change correlations are only 0.100620 in the U.S. and 0.162627 in Japan, and contain benchmark/price effects. Similar-age case pairs are descriptive examples, not experiments. Urban concentration, industrial history and selective migration are hypotheses for further investigation. Source: `results/change_associations.csv`, `case_candidate_pairs.csv`, `analysis_plan.md`.
