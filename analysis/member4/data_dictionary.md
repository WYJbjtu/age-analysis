# Member 4 integration additions and sample rules

The original contract names remain unchanged. Key = `country, region_id, year`; country is USA/JPN. National rows are excluded. Percent fields use 0–100; changes use percentage points. Count and monetary fields stay numeric. CSV empty cells denote unavailable values, never zero.

| Field | Definition |
| --- | --- |
| `age65_share_pct` | Total residents aged 65+ as % of total residents; official one-decimal Japan rates retained for 2021/22 |
| `manufacturing_share_pct` | 100 × nominal manufacturing value added / nominal regional GDP |
| `total_population` | Canonical Member 1 resident count; person units, Japan precision 1,000 |
| `population_0_14`, `population_15_64`, `population_65plus`, `population_total` | Preserved Member 1 detail counts; population_total duplicates the canonical count with its original name |
| `population_reference_date`, `source_version`, `count_precision_persons`, `rate_method` | Original Member 1 metadata |
| `gdp_reference_period` | CYyyyy USA; FYyyyy Japan (April through following March) |
| `industry_source_id`, `industry_amount_unit` | Pinned release and local nominal money units; no international amount comparison |
| `services_definition` | Country-specific selected aggregate; not cross-country harmonized |
| `employment`, `unemployment_rate_pct`, `net_migration` | Original Member 3 values, unchanged; net_migration remains US total / Japan domestic with historical citizenship break |
| `labor_population`, `labor_period`, `labor_verification` | Age/universe, annual averaging and numerical verification scope |
| `migration_original_definition` | US domestic+international; Japan Japanese-only through 2017; later all-nationalities source claim with 2019/22 verified |
| `domestic_net_migration` | Separate official domestic person count; 98 regions in each of 2019 and 2022 only |
| `migration_reference_period`, `migration_population`, `migration_source` | Metadata for the new domestic measure; country periods remain different |
| `population_verification` | All regional canonical rows independently checked against pinned sources |
| `population_industry_match`, `labor_match` | One-to-one merge indicators; optional labor is a left join |
| `core_eligible` | Both required records and nonmissing aging/manufacturing values; never depends on optional context |

Analysis files retain these metadata. `analysis_samples.csv` records every admitted or missing-context row under an analysis ID. Full pooled/grouped, common-region, without-DC and population-weighted variants use the same variable pair. Weighted Pearson/slope are a separate estimand; Spearman is left blank for weighted rows. Country-demeaned estimates use each country's mean subtraction on both variables before correlation/slope; their rank correlation is a rank correlation of residuals, not a partial Spearman coefficient. Endpoint differences use one row per region and retain the original endpoint values.

Primary complete-case requirements are only aging and manufacturing. Context requires aging and the selected contextual field. All 2019/2022 core records are present. Negative net migration is valid. No missing value is interpolated, carried forward or replaced with a denominator from a different population.

Covariance is computed with denominator N throughout: within = Σ(n_c/N)cov_c; between = Σ(n_c/N)(mean_xc−mean_x)(mean_yc−mean_y). Sum equals pooled covariance. Country weights are 51/98 and 47/98, not one-half. Correlations of less than 0.10 absolute magnitude are flagged for communication, not tested for significance. Even nominal opposing signs do not justify a reversal headline if small or influence-sensitive.
