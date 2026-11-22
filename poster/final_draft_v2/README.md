# Poster version 2

**READY FOR TEAM REVIEW**. Open [poster.html](poster.html) for the editable local
layout, [poster.pdf](poster.pdf) for the one-page A0 vector export, or
[poster.preview.png](poster.preview.png) for the 3000-pixel-long-edge preview.
The earlier `../final_draft/` remains unchanged.

This is a presentation revision of validated project results. There are no new
data downloads, fitted models, or changes to scientific input data. All files
needed to rebuild this draft are inside this directory; original repository
paths in the manifests are provenance references.

## Layout and evidence

Three horizontal research bands give the wider figures room to breathe. The
warm cream, deep red rules, serif body and blue/purple country encoding are
retained. Four equal author blocks now sit below the subtitle. The research
question and design strip distinguish national 2000-2022 context, the regional
2011-2022 panel, and the 2019/2022 association and migration snapshots.

| Element | Effective size measured in the PDF |
| --- | ---: |
| Title, first / second line | 106 / 116 pt |
| Four author names / student IDs | 32 / 21 pt |
| Subtitle / affiliation | 29 / 23 pt |
| Section headings / explanatory body | 34 / 24 pt |
| Captions / plot axes | 20 / 20 pt |
| Figure source notes and smallest footer text | 18 pt |

Chromium's measured page is 840.994 x 1188.889 mm, within 0.2 mm of nominal A0.
No fit-to-smaller-page scaling is used. The header and transition occupy about
11% of the height. The measured non-chart body budget is 491 words (headings,
header, figure titles, SVG text and table cells excluded).

| Figure | Poster-specific treatment and safeguards |
| --- | --- |
| [A: National aging](figures/A_national.svg) | All 46 saved country-year estimates; UN WPP2024 national series remains distinct from regional estimates. |
| [B: Regional distribution](figures/B_distribution.svg) | All 51 U.S. and 47 Japanese regions. Shared percentage scale, median and IQR. Country minima/maxima label Utah, Maine, Tokyo and Akita; vertical offsets only separate points. |
| [C: Manufacturing trend](figures/C_manufacturing_trend.svg) | Saved regional medians/IQRs, all 12 years. U.S. CY and Japan FY retained; GDP shares, not employment shares. |
| [D: Aggregation](figures/D_aggregation.svg) | Pooled panel above two country panels with matching axes. Saved slopes/intercepts, no refitting, lines only over observed country ranges. Companion 2019/2022 table reads saved CSV coefficients. |
| [E: Young-adult migration](figures/E_young_migration.svg) | Both complete regional samples. All 51 U.S. approximate 90% ratio intervals, including denominator uncertainty under the existing approximation; 35 hollow points include zero. Country scales differ explicitly. |
| [F: Tokyo native-age profile](figures/F_tokyo.svg) | Both years, all 19 native age bins plus unknown age, 40 bars total. Counts reconcile to each published total. Tokyo is prefecture JP-13; 65+ is already included in the other-age aggregate. |

Each figure also has a 300-dpi PNG. The unchanged original
[full regional ranking](appendix/full_regional_ranking.svg) and
[full native-age cases](appendix/full_native_cases.svg) remain in the appendix.

The added 65+ table reports descriptive Pearson point summaries for both years:
Japan -0.332 / -0.048 and USA 0.135 / 0.439. The Tokyo deletion sensitivity
(-0.381 for Japan in 2022) and temporal instability are printed beside it.
No confidence intervals or country-difference significance claims are invented.
The 99.1% covariance statement is explicitly covariance accounting, not explained
variance or a causal contribution. No pooled service-sector or migration model
is introduced.

## Editable sources and provenance

- `content.json`: credits, scientific title, typography targets and reference-figure provenance.
- `poster.css`: physical page geometry, typography and screen fit/100% controls.
- `build_poster.py`: English narrative, evidence tables and relative inline-SVG assembly.
- `plot_figures.py`: poster-only renderings from the declared snapshots.
- `content_manifest.json`: figure inputs and 21 numerical table/text claims, with row selectors, fields, raw values, formatting and SHA-256.
- `input_manifest.json`: 12 source snapshots, original repository paths/hashes and exact selections. The migration snapshot selects the two displayed age groups; Tokyo selects JP-13. Original CSV cell strings are preserved.
- `figure_manifest.json` and `figure_checks.json`: physical dimensions, source files, all-region counts, saved fit parameters, uncertainty bounds and age-total reconciliation.
- `appendix_manifest.json`: byte-identical appendix copies and original paths/hashes.
- `font_manifest.json`: four small DejaVu font subsets, provenance and hashes; license in `assets/fonts/`. They ensure self-contained layout without copying the full font library.
- `initial_state.json`: before-work branch, HEAD, status and hashes of 460 existing files.
- `qa/`: actual PDF measurements, local runtime versions, isolated-rebuild results and visual review. Large intermediate crops and isolated test copies are ignored.

## Rebuild locally

Use Python 3.12 with `requirements.txt`, a local Chromium browser (Chrome/Edge or
Playwright Chromium), and Poppler `pdftoppm` on PATH. Dependency installation is
separate from reproduction; the build needs no network or official-source fetch.
From this directory, after dependencies are available:

```powershell
python -X utf8=0 plot_figures.py
python -X utf8=0 build_poster.py
python -X utf8=0 render_poster.py
pdftoppm -png -singlefile -scale-to 3000 poster.pdf poster.preview
python -X utf8=0 -X warn_default_encoding validate_poster.py --standalone
```

`render_poster.py --browser <path>` accepts an explicit local Chromium executable.
All HTTP(S) page requests are blocked during export. Local figure links are
available in HTML and removed from PDF so that it contains no machine-local links.
When this folder is in its original repository location, omit `--standalone` to
also verify the original source files, branch/HEAD and all 460 protected hashes.
Standalone validation checks the supplied bundle; it does not pretend to inspect
a repository that is absent.

## Checks actually performed

The rendering commands above ran on Windows with project Python 3.12.4, cp936,
UTF-8 mode 0, NumPy 2.4.3, pandas 2.3.3, Matplotlib 3.11.2 and Playwright 1.58.0.
PDF validation used bundled Python 3.12.14, cp936, UTF-8 mode 0, pypdf 6.10.0 and
pdfplumber 0.11.9. Chrome was 157.0.8103.50. No claim is made for Linux or cp1252.

The isolated rebuild copied 32 explicitly declared runtime files, including all
uncommitted input snapshots, to an ignored test directory. Plot, HTML, PDF and
validation steps all ran with `-X utf8=0 -X warn_default_encoding`. All 17 compared
outputs (12 SVG/PNG figures, HTML, three generated manifests and PDF-derived
preview) matched byte for byte. Extracted PDF text matched; binary PDF timestamps
are allowed to differ. This is an isolated bundle reproduction, not a Git
clean-checkout claim. See `qa/isolated_reproduction.json` for exact commands.

Actual PDF checks passed: one A0 page, effective type sizes, glyph boundaries,
source-mapped values, complete region samples, no layout overflow/overlap, no
missing SVG references, all four font faces loaded, and zero network requests.
Full-page and readable header, population, economics, migration and footer
renderings were visually inspected. This was a screen proof, not a physical print.

Relevant existing read-only entry points also passed from the repository root:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -X utf8=0 scripts/validate_data.py
.\.venv\Scripts\python.exe -X utf8=0 scripts/verify_remediation.py regression --no-write
.\.venv\Scripts\python.exe -X utf8=0 scripts/remediation_state.py
.\.venv\Scripts\python.exe -X utf8=0 analysis/age_migration/verify_extension.py check
```

Results: three 1,176-row contracts; 38 main-analysis comparisons with maximum
difference 0; v6 integrity checks passed; age-migration extension integrity
passed. The 460 before-work files, including all 33 v1 files, remain byte-identical.
No historical unsafe script or full scientific-generation pipeline was executed.
No pytest result is claimed for this layout-only revision.

## Handoff

See [Chinese handoff](HANDOFF_ZH.md) and the exact
[next-commit file list](next_commit_files.txt). Do not commit automatically.
Keep the whole listed v2 bundle together. The older poster and the current shared
poster entry point are preserved; this additive draft awaits team selection.

Print at A0/100%, with browser headers/footers disabled and background graphics
enabled. The exported PDF already follows those settings. Confirm institutional
submission/bleed requirements and make a paper proof before submission. The
supplied author spellings/order/IDs are used exactly; no author decision is pending.

No commits, pushes, PRs/issues, uploads, or other remote writes were performed.
All work remains local.
