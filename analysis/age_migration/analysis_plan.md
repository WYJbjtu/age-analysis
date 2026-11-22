# Age-specific domestic migration: pre-analysis specification

Specified before inspecting any migration/aging correlations, 2026-11-10.
Scope: Japan's 47 prefectures and the United States' 50 states plus DC;
2022 primary, 2019 comparison. Countries are always analyzed separately.
Existing reviewed data, figures, historical evidence and v6 lock remain read-only.

## Estimates and samples

- Primary: ages 20–24 and 65+ net domestic migration per 1,000 current residents
  of the same age, versus Member 1's verified `age65_share_pct`.
- Supporting: ages 20–34; preserve 25–29 and 30–34 separately.
- Equal region weights. Report Pearson and rank-based Spearman, eligible/included/
  missing counts, exact membership, and the denominator for every comparison.
- No pooled-country estimate, ordinary significance headline, causal model,
  predictive model, industry variables, or forced migration sign.
- Keep all valid estimates, including negative net counts and uncertain ACS signs.
- Check all native bins against published totals; totals and overlapping derived
  aggregates must never be summed together.

## Planned sensitivity

For each country/year and all three analysis ages: omit Tokyo (Japan) or DC (US),
leave one region out, compare common regional samples across 2019 and 2022,
and use net age-specific migration per 1,000 total residents (a different estimand).
Where available, use same-year ACS B01001 age65+/all-age population as a separate
US outcome sensitivity. Report every comparison, not just favorable ones.
ACS ratio uncertainty must include numerator and denominator MOEs; unknown
covariances remain an explicit approximation, not assumed independence evidence.
No sampling MOE is invented for Japanese registration counts.

## Profiles and cases

Tokyo prefecture JP-13 is pre-specified. Show its full native age profile and the
published total in each year. All-other-ages excludes 15–24 and is not called 65+.
US profiles: select the minimum and maximum 2022 ages20–24 same-age net-rate
point estimates across the complete US sample (ties by region_id), then retain
those two regions for both years. This is an extremes-based descriptive selection,
with uncertainty visible, not proof of a population ranking or Tokyo analogy.
Scatter labels: Tokyo/DC and the within-country/year minimum and maximum
young-adult rates, with ties by region_id. No region is removed for convenience.

Two primary figure groups: complete regional associations (both ages and years),
then native-age Tokyo and US case profiles. One appendix group: country-separated
full-region heatmaps for the nonoverlapping ages20+ profile 20–24,25–29,30–34,
35–64,65+. Use existing country colors, SVG and 300-dpi PNG.

## Interpretation and integration

ACS one-year residence differences and Japan's calendar-year registered moves
have different coverage, time windows and counting units. ACS is not an age
decomposition of PEP. Same-year flow/stock associations cannot quantify the
fraction of aging caused by migration; two snapshots are not cumulative flows.
Rates and aging shares can share denominator structure. Optional denominator
availability must be documented before analysis; unavailable rates stay missing.
Propose replacing a Member3 segment with 90–120 seconds of English narration;
do not extend the 12-minute presentation or rewrite protected shared materials.
