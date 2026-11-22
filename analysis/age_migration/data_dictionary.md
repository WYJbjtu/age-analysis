# Data contract and comparability

All CSVs use UTF-8, commas, one header, decimal points, and empty cells for missing
values. IDs are strings from `data/reference/region_lookup.csv`; Japan leading
zeros remain in `JP-01` etc. Years are only 2019 and 2022. Counts are persons in ACS
estimation units and registered migration counts in Japan, not interchangeable
annual unique-person measures. Net values may be negative.

## Tables and keys

| Table | Key / scope | Meaning |
| --- | --- | --- |
| `data/native_migration.csv` | country,region_id,year,age_group | 3,606 rows: Japan 19 native bins + total + unknown residual, USA 15 bins + ages1+ total |
| `data/harmonized_migration.csv` | same key | 1,176 rows = 196 region-years × 6 age groups; **not** a 12-year panel |
| `data/population_denominators.csv` | country,region_id,year,age_scheme,age_group | Native and derived same-age populations; totals preserved separately |
| `data/population_structure_join.csv` | country,region_id,year,age_group | Harmonized flow, denominator, canonical aging stock and optional ACS aging sensitivity; all196 region-years retained |
| `data/acs_source_cells.csv` | country,region_id,year,role,variable | Selected published estimates/MOEs as original strings, decoded values and annotation/status fields |
| `data/acs_population_structure.csv` | country,region_id,year | B01001 all-age population and exact male+female65+ sum; separate sensitivity, not a canonical replacement |
| `results/variable_mapping.csv` | source_id,role,variable | Official labels/IDs, age bounds and worksheet/column selection; annotation IDs for ACS |
| `results/associations.csv` | country,year,age_group,variant | 54 preplanned comparisons; 12 full-sample same-age estimates (8 primary-question and 4 supporting-question), no pooled estimate |
| `results/leave_one_out.csv` | country,year,age_group,omitted_region | 588 diagnostics; coefficients and changes from the full sample |

Native Japan age bins are 0–4,5–9,…,85–89,90+. Native USA bins are
1–4,5–17,18–19,20–24,25–29,30–34,35–39,40–44,45–49,50–54,55–59,60–64,65–69,70–74,75+.
`age_lower`/`age_upper` are inclusive; an empty upper bound on a real age bin means
open-ended. Both bounds are empty for totals/unknown. `row_type` disambiguates them.
Unknown Japanese counts are the exact residual of published totals over all named
age bins, supported by the source footnote; they are not allocated to any age group.

Derived groups: primary 20–24 and65+; supporting25–29,30–34,20–34; profile35–64.
The non-overlapping **ages20+** profile is20–24,25–29,30–34,35–64,65+.
20–34 is an overlapping supporting aggregate and must never be added to its
components. All bins are aggregated exactly; no partial-bin apportionment.
Japan's15–19 and the USA's18–19 are never equated. Totals/unknowns are not silently
dropped when reconciling full-population flows.

## Semantic fields

| Fields | Definition / unit |
| --- | --- |
| `country`, `region_id`, `region_name`, `year` | JPN/USA, project ID/name, source reporting year |
| `age_group`, `age_lower`, `age_upper`, `age_scheme`, `row_type`, `native_components` | Exact published or derived age scope; `age_scheme` is native/harmonized |
| `in_migration`, `out_migration` | Nonnegative inter-prefectural/interstate gross counts; abroad/within-region moves excluded |
| `net_migration` | `in_migration - out_migration`; Japan also checked against its published net table |
| `in_moe90`, `out_moe90`, `net_moe90` | ACS 90% MOEs; net and multi-bin MOEs approximate; Japan missing, never zero |
| `*_annotation`, `*_status`, `estimate_raw`, `moe_raw` | Original special values and decoded missingness reasons retained, including controlled-total MOE |
| `uncertainty_method`, `uncertainty_status`, `rate_direction_status` | Exact formula/limitation and sign interpretation; interval-crossing-zero estimates remain included |
| `age_population`, `age_population_moe90` | Current resident count in the exact same age bin; ACS B07001 / Japan Population Estimates |
| `population_total`, `population_total_moe90` | All-age total, ACS B01001 / Japan Table10; **not** B07001 ages1+ total |
| `precision_persons` | Source count display precision: Japan1,000 persons, ACS1person. Aggregate Japanese rounding can accumulate over constituent bins |
| `net_per_1000_same_age` | `1000 * net_migration / age_population` |
| `net_per_1000_total` | `1000 * net_migration / population_total`; a different estimand, not interchangeable with the previous rate |
| `*_moe90_approx` | Derived ACS ratio uncertainty including denominator MOE; missing if a required MOE is unavailable |
| `age65_share_pct`, `canonical_population_total`, `aging_reference_date`, `aging_source_version` | Read-only Member1 values; primary stock outcome |
| `acs_age65_share_pct`, `acs_population_*` | Separate B01001 outcome sensitivity, exact65+ sex-age sum divided by all-age total |
| `migration_source_id`, `population_source_id`, `total_population_source_id`, `aging_source_id` | Resolve to source manifest or declared read-only project path |
| `reference_period`, `age_reference`, `population_reference_date`, `population_universe`, `quality_flag` | Statistical timing/coverage and limitations, not an inferred common universe |

The source-level B07001 total row is explicitly `total_1plus`, while its separately
attached `population_total` comes from B01001. Native Japan migration has separate
85–89 and90+ bins; population Table10 ends at85+, so no invented denominators for
those two finer native bins are exported. Their65+ aggregate is exact.

## Uncertainty arithmetic

ACS published margins use90% confidence. For a sum, `M_sum = sqrt(sum(M_i**2))`;
for net migration, `M_net = sqrt(M_in**2 + M_out**2)`. These are the official
general approximations when covariance estimates are unavailable; survey estimates
are **not known to be independent**. They can overstate or understate uncertainty.
For signed net N and positive denominator D, use the general ratio approximation:

`M_rate = 1000 / D * sqrt(M_net**2 + (N/D)**2 * M_D**2)`.

The numerator–denominator covariance is also unknown and omitted. This is not the
fixed-denominator shortcut and not an exact survey confidence interval. No limits
are clipped. Approximate interval = point estimate ±MOE. For Japan, no sampling
interval is supplied; registration coverage, coding and population estimation can
still be imperfect. Denominator-rounding compatibility is a deterministic check,
not a confidence interval.

ACS controlled B01001 total MOE (`-555555555`, `*****`) is recorded as unavailable,
not zero. Thus the total-population rate's MOE and ACS-aging-ratio MOE remain
unavailable here, even though point estimates are available. Same-age B07001
denominators have usable published MOEs for all required analytical rows.
Native total MOEs use the published total cells rather than pretending that their
MOEs must equal an RSS of all age-cell MOEs.

## Reporting and limitations

Associations give eligible/included/missing counts, explicit exclusions by each
sensitivity rule, exact region membership, equal weights and variable names.
`variant=primary` denotes the full-sample same-age estimand; `analysis_role`
distinguishes the primary questions (20–24,65+) from the supporting 20–34 question.
Pearson measures a linear association; Spearman is Pearson on average ranks.
No ordinary correlation p-values or confidence intervals are presented as if they
accounted for ACS sampling error, spatial dependence or all measurement errors.
Leave-one-region-out assesses influence of observed points, not survey uncertainty.

Japan uses calendar-year registered moves and October1 populations; ACS compares
each respondent's current address with their address one year earlier, throughout
the survey year, with age at interview. Japanese exact age-reference day is not
explicitly specified in the retrieved notes and remains **NOT EVALUATED**.
Published native categories are preserved; no cross-system re-aging is attempted.
All nationalities does not mean international migration. Repeated Japanese
registrations may count one person more than once; ACS is not an event history.

Japanese2019 denominators are the original annual2015-census-base release, whereas
Member1's2019 aging outcome is the later intercensal revision.2022 uses the2020-base
annual release. `results/population_vintage_comparison.csv` quantifies total
differences; the stock outcome was not overwritten. U.S. primary stock is PEP
July1, whereas the denominators are ACS current-residence estimates; B01001 aging
sensitivity is reported separately. ACS migration is not an age decomposition of
the project's PEP domestic series and is not rescaled to it.

Age rates and aging shares both involve population denominators, which can induce
relationships. Alternative total-denominator results are reported as a distinct
quantity. A same-year flow/stock association does not measure the accumulated
contribution of migration, distinguish mechanisms, prove causation or show that
a low-aging-share region's share is falling over time.
