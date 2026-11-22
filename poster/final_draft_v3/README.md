# Poster version 3

This additive draft restores three independent vertical columns. It is ready for team review; the version and delivery status are deliberately absent from the poster itself. No new research, fitted models, samples, or scientific estimates were introduced.

## Open and edit

- `poster.pdf`: one-page A0 portrait print master; print at actual size.
- `poster.preview.png`: 4,245 × 6,000 pixel overview rendered from the PDF.
- `poster.html`: editable local preview with embedded vector figures.
- `poster.css`: page geometry and typography.
- `content.json`: approved authors, title, subtitle and affiliation.
- `build_poster.py`: editable English paragraphs, captions, findings and source-linked numerical claims. Rebuilding replaces `poster.html`.
- `plot_figures.py`: seven poster-specific SVG and 300-dpi PNG figure groups in `figures/`.
- `appendix/evidence_tables.html`: full manufacturing coefficients, all saved migration comparisons including 65+, industry summaries and detailed limitations. The original regional ranking and native-age case figures are retained alongside it.
- `HANDOFF_ZH.md`: concise Chinese handoff. `next_commit_files.txt`: exact repository-relative list of this draft's intended files; nothing was committed.

Only this directory is new. V1, V2, canonical datasets, original figures and reviewed locks remain untouched. This draft has not been made the shared poster entry point automatically.

## Layout and content decisions

The body has three 253 mm columns separated by 14 mm gutters, with independent top-to-bottom flow. Only the header and compact timing/interpretation footer span the page.

| Column | Contents in reading order |
| --- | --- |
| 1 | Background & Data; national trends; complete regional distribution; interpretation |
| 2 | Manufacturing trends; separate country service trends; pooled/USA/Japan manufacturing associations; interpretation and covariance note |
| 3 | Separate youth-migration panels with U.S. intervals; 2019/Tokyo/DC sensitivity note; Tokyo native-age profile; interpretation; Key Findings as the final block |

The V2 title scale and equally prominent author row are retained. Header time-window boxes, methods strip, duplicate question and visible workflow labels are removed. Their scientific scope is retained in the Data paragraph, local captions and footer. Full coefficient tables and optional older-adult tables moved to the appendix instead of shrinking the main figures.

Measured in the exported PDF: title 106/116 pt, authors 32 pt, IDs 21 pt, affiliation 23 pt, column headings 32 pt, body 24 pt, captions 20 pt and plot text approximately 18–22 pt. The nominal page is 841 × 1189 mm; Chromium's measured output is 840.994 × 1188.889 mm. No fit-to-page reduction was applied.

## Figures and scientific boundaries

| Asset | Existing validated input | Protection |
| --- | --- | --- |
| `A_national` | `inputs/national.csv` | All 46 UN WPP2024 country-years; national historical estimates |
| `B_distribution` | `inputs/population_2022.csv` | All 98 regions on a common percentage axis; equal-region median/IQR, not national weighted rates |
| `C_manufacturing` | `inputs/industry_trends.csv` | All 24 country-year median/IQR summaries; nominal manufacturing value added / GDP; U.S. CY / Japan FY |
| `D_services` | Same saved industry summaries | Two distinct panels; within-country interpretation only; 50–85% zoomed axes disclosed |
| `E_aggregation` | `inputs/manufacturing_2022.csv`, saved associations | Same 98/51/47 observations, saved coefficients and fitted-line parameters; common axes |
| `F_young_migration` | `inputs/migration.csv`, saved associations and uncertainty | All 47/51 regions; same-age denominator; all 51 U.S. approximate 90% ratio intervals, including 35 crossing zero |
| `G_tokyo` | `inputs/tokyo_native.csv`, saved decomposition | JP-13; 19 native bins plus unknown in each year; counts, not rates; totals reconcile |

U.S. private services include utilities but exclude government and government enterprises. Japan's published tertiary aggregate includes utilities, public administration, education, and health/social services. These are distinct aggregates: no pooled services, cross-country service-share gap, combined ranking or harmonized definition is produced. The existing comparability guard remains BLOCKED.

Migration remains descriptive. Japan's constructed rates use rounded population denominators; its exact migration age-reference day and the 2019 official-rate table remain unverified. The 2019 denominator and the canonical aging stock have different revision vintages. ACS measures prior-year residence differences and age at interview; Japanese registration events can include repeated moves. U.S. ratio intervals account for available denominator MOEs but omit unavailable covariances; same-survey estimates are not known to be independent. Detailed notes and complete saved sensitivity results are in the appendix. Tokyo's 65+ balance is already included in “all other ages” and is never added twice. The 99.1% statement is covariance accounting, not explained variance or causation.

## Provenance and validation records

- `initial_state.json`: initial branch, HEAD, status/diff and hashes of 577 existing files.
- `input_manifest.json`: 12 CSV snapshots, original paths/hashes, exact selections and row counts.
- `provenance_manifest.json`: original figure/script/policy paths and hashes.
- `figure_manifest.json`, `figure_checks.json`: each derivative's input/source/output hashes, actual points, coefficients, intervals and reconciliations.
- `content_manifest.json`: 13 dynamically selected numerical text claims, figure provenance and appendix mapping.
- `font_manifest.json`, `appendix_manifest.json`: font/license and unchanged supplementary SVG provenance.
- `qa/validation.json`, `qa/layout.json`: actual PDF, source, geometry and font checks.
- `qa/visual_review.json`: full-page and close-up inspection record for the final PDF.
- `qa/baseline_checks.json`: actual read-only baseline commands and test results.
- `qa/isolated_reproduction.json`: copied runtime file hashes, commands, warnings and output comparisons.

## Reproduce locally

Use the declared Python dependencies in `requirements.txt`, a local Chromium-compatible browser and Poppler's `pdftoppm`. Input CSVs, policy, fonts and original supplementary SVGs are included; no private data cache or network retrieval is required. From this directory:

```powershell
python -X utf8=0 -X warn_default_encoding plot_figures.py
python -X utf8=0 -X warn_default_encoding build_poster.py
python -X utf8=0 -X warn_default_encoding render_poster.py
pdftoppm -png -singlefile -scale-to 6000 poster.pdf poster.preview
python -X utf8=0 -X warn_default_encoding validate_poster.py --standalone
```

`render_poster.py --browser <executable>` accepts an explicit browser path. It otherwise detects local Windows Chrome/Edge, then falls back to Playwright's installed Chromium. All page HTTP(S) requests are blocked. Remove `--standalone` when validating inside the original repository to additionally check the 577-file baseline and original source copies. All generated text uses explicit UTF-8 and LF; byte-preserved input assets retain their source bytes.

Actual execution used Windows, Python 3.12.4 for plotting/building/rendering, and bundled Python 3.12.14 for PDF validation; both reported locale encoding cp936 and UTF-8 mode 0. Chrome was 157.0.8103.50. Package versions and execution details are recorded in `qa/render_environment.json` and the reproduction log. Local browser export required approved process execution outside the execution sandbox after sandboxed driver initialization stalled. This was a local rendering permission issue; it did not require network access or an account. Linux and cp1252 were not tested.

An isolated copy containing 34 explicitly listed runtime files, including required uncommitted input snapshots, rebuilt successfully with `-X utf8=0 -X warn_default_encoding`. Twenty generated outputs were byte-identical, including all fourteen figure files and the final 6,000-pixel PDF rendering. PDF text, page geometry and typography matched; PDF creation timestamps may differ. This is an isolated deliverable-file reproduction, not a Git clean-checkout claim. The plotting run reported a third-party Matplotlib `EncodingWarning`; project text decoding was explicit.

The following existing checks also ran from the repository root, with `PYTHONPATH=src` and `PYTHONDONTWRITEBYTECODE=1`:

```powershell
.\.venv\Scripts\python.exe -X utf8=0 scripts/validate_data.py
.\.venv\Scripts\python.exe -X utf8=0 scripts/verify_remediation.py regression --no-write
.\.venv\Scripts\python.exe -X utf8=0 scripts/remediation_state.py
.\.venv\Scripts\python.exe -X utf8=0 analysis/age_migration/verify_extension.py check
$testTemp = 'poster/final_draft_v3/qa/pytest-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -X utf8=0 -X warn_default_encoding -m pytest -q tests/test_remediation.py::test_pooled_services_blocked_before_any_figure_is_written member2_industry/test_industry.py::test_services_chart_requires_a_single_country -p no:cacheprovider --basetemp $testTemp
```

Results: three 1,176-row contracts passed; 38 high-precision main-analysis comparisons had maximum difference 0; reviewed lock v6 and age-migration integrity checks passed; two service-comparability tests passed. Pytest retained two third-party warnings (anyio API deprecation and Matplotlib default encoding). This focused poster task did not run the entire pytest suite, reacquire official data or execute historical unsafe scripts.

## Handoff

The working branch remains `codex/member4-audit-integration`, HEAD `a311a18748d676196b523668dab7ed6e17472635`. The original untracked age-migration module and V1/V2 drafts remain present; V3 is additional untracked work. All 577 frozen existing files are unchanged. No lock was refreshed.

The team still needs to select this version for final use and confirm the printer's actual-size/bleed requirements. Screen inspection is complete; a physical A0 print proof was not performed.

No commits, pushes, PRs/issues, uploads, or other remote writes were performed. All changes remain local.
