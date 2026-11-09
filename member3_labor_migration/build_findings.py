"""Generate the active Member 3 handoff and English text from the repaired panel."""
from pathlib import Path
import json
import pandas as pd
from plot_helpers import ROOT, MEMBER, load_panel, cross_section


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])


def main():
    panel=load_panel();sample=cross_section(panel)
    migration=pd.read_csv(ROOT/'data/processed/labor_migration.csv')
    stats=[];profiles=[]
    for country,g in sample.groupby('country'):
        r=g.age65_share_pct.corr(g.unemployment_rate_pct)
        rho=g.age65_share_pct.rank().corr(g.unemployment_rate_pct.rank())
        stats.append([country,len(g),f'{r:.6f}',f'{rho:.6f}'])
        lo=g.loc[g.domestic_net_migration.idxmin()];hi=g.loc[g.domestic_net_migration.idxmax()]
        profiles.append([country,f'{g.unemployment_rate_pct.median():.1f}%',
            f'{g.unemployment_rate_pct.min():.1f}–{g.unemployment_rate_pct.max():.1f}%',
            f'{lo.region_name}: {lo.domestic_net_migration:+,.0f}',f'{hi.region_name}: {hi.domestic_net_migration:+,.0f}'])
    tokyo=migration[migration.region_id=='JP-13'].set_index('year').domestic_net_migration
    jp=migration[migration.country=='JPN'].pivot(index='region_id',columns='year',values='domestic_net_migration')
    delta=jp[2022]-jp[2019]
    rev=pd.read_csv(MEMBER/'bls_revision_check.csv').difference_pp.abs()
    cases=sample[sample.region_id.isin(['US-IN','US-NV','JP-01','JP-16'])].sort_values(['country','region_id'])
    case_rows=[[r.region_name,f'{r.age65_share_pct:.2f}',f'{r.manufacturing_share_pct:.2f}',
                f'{r.unemployment_rate_pct:.1f}',f'{r.domestic_net_migration:+,.0f}'] for r in cases.itertuples()]
    definitions='''The United States uses annual LAUS estimates for the civilian noninstitutional population aged 16+; Japan uses annual Labour Force Survey prefectural estimates for ages 15+. Employment counts are residence-based persons, not establishment jobs. Unemployment uses the labor force as its denominator. Published counts are in thousands and are converted to persons; they retain thousand-person precision. Rates are published annual values, not averages of rounded monthly rates. No labor-force participation rate is calculated from total population or population aged 15–64.

U.S. domestic migration uses Census **DOMESTICMIG**. INTERNATIONALMIG and NETMIG are separate fields; domestic plus international equals total. Annual Census fields cover July 1 of the previous year to July 1 of the named year, not the cumulative Census-base period. Vintage 2020 supplies 2011–2020 and Vintage 2022 supplies 2021–2022; revisions remain a limitation. Japanese migration is inter-prefectural registration over January–December. The historical table is **Japanese nationals only** in 2011–2017; annual tables cover **all nationalities** in 2018–2022. These are separate columns and disconnected plotted series. All-nationality values before 2018 remain missing. No interpolation or carry-forward is used.

Migration is a net count, not a rate or a count of young adults. It does not identify gross inflows/outflows or migrants' ages. Countries have different reporting periods and populations; migration and labor results are interpreted within countries. Counts also depend on region size. Population dates are July 1 (United States) and October 1 (Japan); manufacturing is nominal manufacturing value added / nominal GDP in CY (United States) or FY April–March (Japan). Manufacturing's GDP share is not an employment share. Country-specific services are never pooled.'''
    coverage=f'''The canonical panel has **{len(panel):,} region-year rows**: 51 U.S. regions (50 states and Washington, D.C.) and 47 Japanese prefectures in every year, 2011–2022. All keys are unique. Employment and unemployment rates are complete. All-nationality domestic migration has **{migration.domestic_net_migration.notna().sum()} valid / {migration.domestic_net_migration.isna().sum()} missing observations**; the 329 missing entries are Japan 2011–2017 and have a separate Japanese-only field. International and total migration are available for the 612 U.S. rows; the 564 Japanese entries remain missing. The legacy `net_migration` field is retained for compatibility, with explicit original definitions, and is not used for domestic-migration plots.

`prepare_labor.py` rebuilds from official Census CSVs, Japanese XLS/XLSX files and checksum-locked BLS annual-page text snapshots. It never reads the existing processed panel as an input. All 612 U.S. annual employment and unemployment-rate records were independently read from official BLS archives and match the former published values. Direct HTML download returned HTTP 403; routine reproduction uses the traceable full-state text snapshots and does not claim fresh HTML/API retrieval. Japanese labor is reproduced from the pinned official workbook. All 196 domestic-migration observations in 2019 and 2022 agree exactly with Member 4's independently verified adapter, which is used only as a validation reference. Source URLs and source hashes are in `sources.csv`, `summary.json` and `source_snapshots/manifest.json`.'''
    figures='''| File under `figures/` | Scope and selection | Use |
| --- | --- | --- |
| `figure4_labor_2022.png` / `.svg` | All 98 regions; domestic-migration color; bubble area encodes absolute 2011–2022 unemployment change | Main labor context |
| `jpn_labor_migration_2019_2022.png` / `.svg` | All 47 scatter points, including Akita; eight largest increases and eight largest decreases selected from all 47 | Japan context |
| `jpn_panel_2011_2022.png` / `.svg` | Labor: all 47; migration: Tokyo, Kanagawa, Saitama, Osaka, Aichi retained from the original five-case selection; nationality break shown | Appendix |
| `two_country_trend_2011_2022.png` / `.svg` | Medians of 51 or 47 region-level values; employment indexed separately to each region's 2011 value | Appendix; vintage limitations |
| `outliers_2022.png` / `.svg` | Within-country residual screen, all 98 regions; labels show up to four largest absolute standardized residuals ≥1.5 per panel | Appendix; exploratory |

Each figure has a JSON sidecar with input hashes and sample membership. Root-level image aliases are compatibility copies of the repaired images; use the `figures/` paths. The pre-repair versions are superseded and retained in the external backup, not approved for presentation.'''
    results=f'''## Results supported by the repaired data

{table(['Country','Regions','Pearson r: aging × unemployment','Spearman rho'],stats)}

In the 2022 cross-section, the U.S. Pearson coefficient is close to zero and Japan's is negative. Both Pearson coefficients are negative: this comparison does **not** demonstrate a directional reversal. These descriptive linear/rank summaries neither identify a mechanism nor rule out other relationships.

{table(['Country','Regional median unemployment','Regional unemployment range','Lowest domestic net migration (persons)','Highest domestic net migration (persons)'],profiles)}

These are regional medians and ranges, not national population-weighted rates or a harmonized cross-country labor ranking. Tokyo's all-nationality domestic net migration was {tokyo[2019]:+,.0f} in 2019 and {tokyo[2022]:+,.0f} in 2022, a difference of {tokyo[2022]-tokyo[2019]:+,.0f} persons. Of all 47 prefectures, {int((delta<0).sum())} had a lower net value and {int((delta>0).sum())} a higher net value. A decline does not necessarily mean a region became a net loser. Each annual Japanese domestic total sums to zero; the observations cannot establish a pandemic effect or an age-specific migration mechanism.

## Regional examples

{table(['Region','Aged 65+ (%)','Manufacturing GDP share (%)','Unemployment (%)','Domestic net migration (persons)'],case_rows)}

These retained examples compare Indiana with Nevada and Hokkaido with Toyama within their own countries. They are the largest manufacturing-share gaps among pairs whose aging rates differ by at most 0.5 percentage points, using the full 2022 sample; Member 4 also presents the smallest-gap contrasting pairs. All candidates are disclosed in Member 4's case table. The cases illustrate coexistence of similar aging and different industrial shares; they do not isolate industry's effect or control confounding. Cross-country aging ranges do not overlap, so no cross-country aging-matched case is constructed. The residual screen reuses the same observations and is not independent confirmation of selection.

## Relation to the project's main result

The pooled sample shows a positive association, but within-country Pearson correlations are close to zero in both the United States and Japan for the examined years. The pooled relationship should not be interpreted as a shared regional pattern within either country. This statement concerns aging and **manufacturing GDP share** in 2019 and 2022, not aging and unemployment. It does not establish a stable reversal, no role for industrial structure, or a pattern in every year of the twelve-year panel.

## Vintage and rounding checks

The safe `check_bls_revision.py` compares {len(rev)} annual state values with the prior-year annual column of the next official release. Absolute unemployment-rate revisions have median {rev.median():.1f} pp, 90th percentile {rev.quantile(.9):.1f} pp and maximum {rev.max():.1f} pp. This is an adjacent-archive check, not current-API validation. The former credential/proxy/monthly-average checker has been replaced. All 1,176 labor-force, employment, unemployment and rate rounding checks pass. Japanese model/ratio estimates, disaster-year notes and benchmark revisions remain relevant; a single retrieved workbook does not remove those breaks.
'''
    (MEMBER/'findings.md').write_text('# Member 3 findings — repaired 2026-11-09\n\n'+coverage+'\n\n'+results+'\n## Figure captions and selection\n\n'+figures+'\n\n## Definitions and limitations\n\n'+definitions+'\n',encoding='utf-8')
    (MEMBER/'report_section.md').write_text('# Member 3 — labor, domestic migration and regional examples\n\n'
        'Current English report text; generated by `build_findings.py`. The population–manufacturing sample is formed before this optional context is left-joined. Missing labor or migration cannot exclude a core observation.\n\n'
        '## Data and reproduction status\n\n'+coverage+'\n\n## Definitions\n\n'+definitions+'\n\n'+results+
        '\n## Figures\n\n'+figures+'\n\nReproduction commands and source files: [module README](README.md). Current team presentation entry point: [poster README](../poster/README.md).\n',encoding='utf-8')
    (MEMBER/'README.md').write_text('''# Member 3 — repaired labor and migration pipeline

Current delivery: 2026-11-09. The active findings, report text and all five figure generators have been repaired in this module. [Team presentation entry point](../poster/README.md) · [Chinese repair record](../docs/remediation/repair_report_zh.md).

'''+coverage+'''

## Reproduce locally

Use the repository virtual environment. Acquisition is separate from parsing; cached runs are offline and never require a BLS key, proxy or Excel conversion.

```powershell
$py = '.\\.venv\\Scripts\\python.exe'
# Optional public-source acquisition; bounded attempts and cache reuse:
& $py -X utf8 scripts/fetch_remediation_sources.py --group member3
# Offline rebuild from pinned raw files / traceable BLS page snapshots:
& $py -X utf8 member3_labor_migration/prepare_labor.py
& $py -X utf8 member3_labor_migration/check_bls_revision.py
& $py -X utf8 member3_labor_migration/plot_figure4.py
& $py -X utf8 member3_labor_migration/plot_japan_labor.py
& $py -X utf8 member3_labor_migration/plot_japan_trend.py
& $py -X utf8 member3_labor_migration/plot_two_country_trend.py
& $py -X utf8 member3_labor_migration/outliers_2022.py
& $py -X utf8 member3_labor_migration/build_findings.py
```

Dependencies: the project stack plus `openpyxl` and `xlrd` for official XLSX/XLS files. Downloaded files live under ignored `data/raw/member3/`; BLS text representations and their provenance are versioned under `source_snapshots/`. A changed official source fails hash validation rather than silently switching vintages. `--output-root data/cache/NAME` rebuilds into an isolated project directory. Shared data validation and tests are listed in the root README.

## Outputs and field meanings

- `../data/processed/labor_migration.csv`: 1,176 unique region-year rows. Original six columns are retained; explicit migration components, populations, dates, vintages and labor provenance are added.
- `jpn_labor_detail.csv`: 564 annual prefectural rows; `us_labor_detail.csv`: 612 annual state/DC rows. The former U.S. 2022 employment-population-ratio column is retained from official Table 2; earlier years remain missing and are not used in this study. Its denominator is civilian noninstitutional population aged 16+, not total population.
- `coverage.csv`, `rounding_validation.csv`, `domestic_migration_comparison.csv`: indicator-specific missingness, quantity/rate checks and 196 independent comparisons.
- `bls_revision_check.csv`: 561 neighboring annual-release comparisons, replacing the invalid monthly-API comparison.
- `sources.csv`: quoted, UTF-8, ten-field source registry; `summary.json` records the exact raw sources and reproduction status.
- `build_findings.py`: computes the numerical claims in [findings.md](findings.md) and [report_section.md](report_section.md) from current canonical inputs.

'''+figures+'\n\n## Comparability\n\n'+definitions+'\n\nThe all-nationality Japanese migration history before 2018 remains **BLOCKED** for continuous comparison. Presentation-safe alternatives are the labeled split series or the verified all-nationality 2019/2022 comparison. Direct BLS HTML retrieval is **not reverified**; the official text snapshots support a complete, traceable offline rebuild. No unresolved source gap is filled with fabricated observations.\n',encoding='utf-8')
    print('Generated Member 3 README, findings and English report from current inputs.')


if __name__=='__main__':main()
