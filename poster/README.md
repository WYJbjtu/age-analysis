# Current poster and presentation entry point

Use this selection after the 2026-11-09 remediation. The [figure-and-text manifest](presentation_manifest.csv) records owner, exact inputs/version, readiness, superseded paths and replacement reasons. The [Chinese repair report](../docs/remediation/repair_report_zh.md) records validation and remaining limits. A standalone final poster/PPTX was not present in this repository; these are the repaired assets and text for assembly.

## Main message

“The pooled sample shows a positive association, but within-country Pearson correlations are close to zero in both the United States and Japan for the examined years. The pooled relationship should not be interpreted as a shared regional pattern within either country.”

This concerns population aging and nominal manufacturing GDP share in 2019 and 2022, with 98 regions in each year. Do not claim a stable directional reversal, a causal effect, no role for industrial structure, control of all confounders, or the same relationship in every year of the 2011–2022 panel.

## Figures and English text approved for assembly

| Owner | Main selection | Text and limits to keep |
| --- | --- | --- |
| Member 1 | [National UN aging trend](../member1_demographics/figures/01_national_aging_trends_2000_2022.png), then [all-region aging comparison](../member1_demographics/figures/02_regional_aging_comparison_2022.png) | [Population findings](../member1_demographics/findings.md). WPP2024 both-sex July1 historical estimates; regional medians are not national rates. |
| Member 2 | [Manufacturing trend](../member2_industry/figures/manufacturing_trend_2011_2022.png); [2022 distribution](../member2_industry/figures/manufacturing_distribution_2022.png) as backup | [Industry findings and narration](../member2_industry/findings.md). USA CY / Japan FY; nominal value added/GDP, not employment share. |
| Member 3 | [Repaired labor/domestic-migration Figure 4](../member3_labor_migration/figures/figure4_labor_2022.png) | [Repaired findings/captions](../member3_labor_migration/findings.md), [English report](../member3_labor_migration/report_section.md). All98 regions including Akita; country-specific migration colors and labor universes. |
| Member 4 | [Pooled and within-country main figure](../analysis/member4/figures/01_pooled_within_2022.png), [robustness and covariance](../analysis/member4/figures/02_robustness_and_covariance.png) | [Report text](member4/report_section.md), [poster copy](member4/poster_text.md), [captions](member4/figure_captions.md), [speaking script](member4/speaking_script.md), [Q&A](member4/examiner_qa.md). Main numerical results remain regression-checked. |

Each linked PNG has a same-stem SVG. Keep the caption/source/footer when placing the figure. Scientific plots are generated from actual data. Final placement and page size remain the team's assembly decision; no fabricated complete deck is implied.

## Appendix choices

- [Within-country case pairs](../analysis/member4/figures/03_within_country_cases.png): largest-gap and contrasting smallest-gap pairs; ≤0.5pp aging difference; no cross-country aging matching because ranges do not overlap.
- [Japan 2019/2022 domestic migration](../member3_labor_migration/figures/jpn_labor_migration_2019_2022.png): all47 scatter points; right panel explicitly selects eight largest increases and decreases.
- [Japan history with a nationality break](../member3_labor_migration/figures/jpn_panel_2011_2022.png), [regional labor trends](../member3_labor_migration/figures/two_country_trend_2011_2022.png), [residual screen](../member3_labor_migration/figures/outliers_2022.png): descriptive context; a same-data residual screen is not independent case validation.
- Member2 [U.S. private services](../member2_industry/figures/usa_services_trend_2011_2022.png) and [Japan tertiary industries](../member2_industry/figures/jpn_services_trend_2011_2022.png): **within-country only**. Shared code blocks pooled service comparisons.
- Existing U.S. [aging map](../handover/us_2022/deliverables/figures/02_aging_map.png) and [manufacturing map](../handover/us_2022/deliverables/figures/03_manufacturing_map.png): verified original Census2022 boundaries, 51 regions, AK/HI/DC insets; generalized display, inset scales differ. There is no supplied Japanese map. Use the Member1 ranked chart for a common-scale country comparison.

## Required wording boundaries

2022 Pearson is 0.644435 pooled, 0.003224 USA and 0.028647 Japan; 2019 is 0.618710, 0.040097 and −0.009533. If quoting 2022 Spearman's nominal reversal, include the weak within-country coefficients (−0.012036 USA, −0.084724 Japan) and U.S. leave-one-out sign sensitivity. The 99.0969% figure is a **covariance accounting share** with denominator N and weights51/98 and47/98, not R², explained variance or a causal contribution.

U.S. population is July1 and GDP CY; Japan population is October1 and GDP FY April–March. Labor covers U.S. civilian noninstitutional16+ and Japanese LFS15+. U.S. domestic migration is July-to-July; Japan is calendar-year registration. Net counts do not reveal migrants' ages, gross flows or causation. Japanese all-nationality migration before2018 remains **BLOCKED** as a continuous comparable history; use the split figure or2019/2022 comparison.

## Superseded and historical material

All pre-repair Member3 Figure4/Japan-history/labor-context/residual plots and old `README.md`, `findings.md`, `report_section.md`, `prepare_labor.py`, `check_bls_revision.py` are superseded by the current files at those same paths. The old bytes are in the external pre-change backup named in the change manifest. Root-level Member3 image aliases now contain repaired bytes but are superseded as presentation entry paths; use `figures/`.

The former98-row shared merge has been replaced by the1176-row current merge. Original Member4 audit reports and registers remain historical evidence of pre-repair problems; their “not assessed”/“owner to fix” statuses are superseded by the new repair record, not erased. Historical plans/handover documents are not current presentation copy. No pooled service-sector display is approved. The previous unsafe BLS checker and its monthly-mean interpretation must not be reused.
