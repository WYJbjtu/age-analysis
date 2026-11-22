# Aging Across Economies - poster draft

**READY FOR TEAM REVIEW.** Additive A0 portrait draft, nominally **841 x 1189 mm**.
This directory is the assembled review copy for the requested three-column story.
It does not supersede the protected scientific sources or rewrite `poster/README.md`.

- [Print PDF](poster.pdf): one page, vector figures, embedded fonts. Print at 100% on A0.
- [Editable/local HTML](poster.html) with [CSS](poster.css): open locally; click a chart to inspect its complete unchanged source SVG.
- [PDF-rendered preview](poster.preview.png): 2400-pixel long edge, for review, **not the print master**.
- [Chinese handoff](handoff_zh.md), [precise poster file list](next_commit_files.txt).
- [Content and credits](content.json); [source figures and hashes](figure_sources.json).

## Structure and figure selection

Cream paper, deep-red outer frame and inner rule, black serif prose, oversized
two-line headline. Country colors remain blue for the United States and purple
for Japan. Fonts are locally bundled DejaVu Sans/Serif with their license; no
cover artwork, stock images, remote fonts or generated scientific graphics are used.

The left column covers national aging and all-region variation. The center covers
manufacturing trends and the pooled/within-country contrast. The right covers
young-adult migration and Tokyo's complete age profile. The footer contains
**exactly three** findings, a quieter limitations block and source notes.

All source paths below are relative to the repository root. Each full SVG is
copied byte-for-byte into `assets/`; the originals remain untouched.

| Panel | Owner | Exact source | Display in this draft |
| --- | --- | --- | --- |
| A | Member 1 | `member1_demographics/figures/01_national_aging_trends_2000_2022.svg` | WPP2024 national historical 65+ shares, 2000-2022 |
| B | Member 1 | `member1_demographics/figures/02_regional_aging_comparison_2022.svg` | Both ranked panels, stacked; all 51 U.S. and 47 Japanese regions |
| C | Member 2 | `member2_industry/figures/manufacturing_trend_2011_2022.svg` | Regional median and IQR, 2011-2022; U.S. CY / Japan FY |
| D | Member 4 | `analysis/member4/figures/01_pooled_within_2022.svg` | Pooled, U.S. and Japan panels, stacked with the same numeric axes |
| E | Age-migration extension | `analysis/age_migration/figures/figure1_regional_2022.svg` | Ages 20-24 panels only, all 47/51 regions, retaining U.S. MOEs |
| F | Age-migration extension | `analysis/age_migration/figures/figure2_native_cases.svg` | Tokyo prefecture, both years, all 19 known-age bins plus unknown age |

The layout uses ten viewports from these six exports. `layout_views.json` records
each viewport. Wide figures are reflowed by selecting original axes, not by
replotting data. Original shared SVG definitions are retained, including markers
defined in another source panel. Original shared y-axis **text** is repeated for
the U.S./Japan manufacturing panels; their existing grids and ticks are retained.
The source figures remain available in full beside the HTML.

Only layout typography is adjusted: small labels in B are enlarged; C's small
labels are enlarged, its second legend entry is spaced farther right, and its
y-axis title is moved left to avoid overlap. Point coordinates, data paths,
numeric labels, axis scales and underlying observations are unchanged. Original
large figure titles/footers outside the viewports are replaced by the adjacent
poster titles and source/method captions. The PDF omits HTML's local file links
so it does not carry computer-specific broken hyperlinks.

## Evidence and interpretation

`build_poster.py` reads existing saved CSV rows; it does not fit models, calculate
new correlations or generate scientific plots. `claim_checks.json` records the
exact row filters, fields, values and source hashes for 13 inserted numerical
claims. Source-figure labels are preserved and protected by the original hashes.

| Poster statement | Existing evidence |
| --- | --- |
| 2022 pooled/within-country manufacturing contrast; 2019 comparison | `analysis/member4/results/associations.csv`, `poster/member4/poster_text.md`, source figure D |
| 99.1% between-country covariance component | `analysis/member4/results/covariance_summary.csv`, `year=2022`, `between_fraction` |
| Japan young-adult r: -0.820; without Tokyo -0.796; 2019 -0.812 | `analysis/age_migration/results/associations.csv` |
| U.S. young-adult r: -0.362; without DC -0.212; 2019 -0.337 | Same association table; all 51 regions retained in the primary plot |
| 35/51 U.S. young-rate intervals include zero | `analysis/age_migration/results/us_uncertainty_summary.csv`, 2022, ages 20-24 |
| Tokyo 2022 total +38,023; ages 15-19 +13,795; 20-24 +57,153; other ages -32,925; 65+ -9,284 | `analysis/age_migration/results/tokyo_decomposition.csv` |

Regional medians are not population-weighted national rates. Manufacturing means
nominal manufacturing value added / nominal regional GDP, not employment share.
The covariance percentage is **not** R-squared, explained variance or a causal
contribution. The main manufacturing statement concerns the examined snapshots,
not every year in the trend panel. No stable directional-reversal claim is made.

Migration rates use same-age populations; Tokyo's bars use counts (thousands on
the axis). Japanese registered inter-prefectural events and ACS prior-year
residence differences are distinct measures. The U.S. rate MOEs are approximate,
include denominator uncertainty and omit unavailable covariances. Correlations
do not incorporate survey uncertainty or spatial dependence. Japan uses constructed
rates from rounded population denominators; its 2019 official age-rate table and
exact age-reference day remain unverified. These limits remain visible on the poster.

Omitted from the main page: service-sector comparisons, labor participation,
maps, the older-adult companion panels, U.S. case profiles and the full heatmap
appendix. These omissions keep the page readable; they are not deleted evidence.
The complete original E/F assets retain the older-adult and U.S. case panels.
2019 is explicitly reported in text and in Tokyo's two-year profile.

## Build, render and validate

From the repository root, building needs only the Python standard library and
the declared repository sources above. HTML/PDF viewing and PDF rendering are
self-contained within this folder. No private cache or network source is needed.

Automated rendering needs Playwright 1.58.0 and a local Chromium browser.
Validation needs pypdf 6.10.0; dependencies are declared in `requirements.txt`.
Poppler `pdftoppm` is used for the final PDF preview. The existing environment
already supplied these tools across two local Python installations; no dependency
installation or browser download was performed for this task.

Actual successful commands (PowerShell):

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -X utf8=0 poster/final_draft/build_poster.py
& $py -X utf8=0 poster/final_draft/render_poster.py
pdftoppm -scale-to 2400 -png -singlefile poster/final_draft/poster.pdf poster/final_draft/poster.preview

$pdfPy = 'C:/Users/15811/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $pdfPy -X utf8=0 -X warn_default_encoding poster/final_draft/validate_poster.py

& $py -X utf8=0 scripts/remediation_state.py
& $py -X utf8=0 analysis/age_migration/verify_extension.py check
git diff --check
```

For another machine, use any Python with this folder's requirements installed;
the bundled Python path above records the actual run, not a runtime dependency
hardcoded into the source. `render_poster.py --browser PATH` accepts a local
Chromium executable. It otherwise finds Chrome/Edge on Windows, then falls back
to an already installed Playwright Chromium. It never downloads a browser.

The renderer uses the local HTML page and blocks HTTP(S) requests. Browser print
is used to preserve the existing SVG vectors; no scientific plotting workflow is
rerun. Authors/course text are in `content.json`; prose/layout assembly is in
`build_poster.py`; type and physical page dimensions are in `poster.css`.
If size changes, revise CSS, configuration and the dimension check together and
repeat visual QA. Scaling this A0 page down to A1 makes the regional labels too small.

## Actual validation and protection

- `validation.json`: PASS; all 427 pre-existing files byte-identical, six original
  SVG copies match, 13 numerical claims match saved results, and every selected
  source graphic group retains its geometry. Seven regional scatter/rank views
  contain 51, 47, 98, 51, 47, 47 and 51 markers respectively.
- `layout_check.json`: no unresolved SVG references, duplicate IDs, column
  overflows, sibling overlaps, JavaScript errors or page network requests;
  all five bundled font faces loaded.
- PDF: one A0 page, nominal 841 x 1189 mm (Chromium's PDF box rounds to about
  840.994 x 1188.889 mm). Four authors and IDs survive text extraction; no local
  file hyperlinks are embedded.
- `visual_review.json`: final PDF preview and 120-dpi detail crops inspected for
  complete labels, axes, markers, legends, whitespace and footer readability.
- `isolated_render.json`: all 15 required HTML/CSS/render/assets files copied to a
  new isolated folder; offline rendering succeeded and nine layout/content fields
  matched. This is render-only reproduction, not a new scientific-data replay.
- Shared v6 integrity check passed (282 current files, 229 archived originals,
  163 v1 records, 46 immutable audit files); the age-migration manifest passed
  (111 files, 43 raw sources). No reviewed lock was refreshed.

Build/render used Python 3.12.4, Windows cp936, UTF-8 mode 0; PDF validation used
Python 3.12.14, cp936, UTF-8 mode 0 with default-encoding diagnostics. Chrome was
157.0.8103.50. No cp1252/Linux execution, full statistical test rerun, new source
retrieval or new statistical analysis is claimed by this poster task.

## Team decisions and next commit

Confirm the course's required print size, bleed/margins, institution/course
branding and final editorial approval. Author spelling, order and IDs use the
supplied text, including `WANGYUCHENG` without an inserted space.

Use the right column to replace/emphasize the existing Member 3 migration segment
within the 12-minute talk, rather than adding a new talk segment. Retain the full
age-migration figures as Q&A backup.

`next_commit_files.txt` lists **only the new poster deliverables**; it is not a
command to stage or commit. The pre-existing untracked `analysis/age_migration/`
module is unchanged and has its own exact list at
`analysis/age_migration/next_commit_files.txt`. Include that module as a separately
reviewed prerequisite before, or together with, this poster if the source rebuild
is to be reproduced from a future checkout. The assembled HTML/assets and PDF
remain viewable/renderable without that module.

No commits, pushes, PRs/issues, uploads, or other remote writes were performed.
All new work remains local.
