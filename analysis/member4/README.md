# Member 4 audited delivery

**Current remediation entry:** [team presentation](../../poster/README.md) and [Chinese repair record](../../docs/remediation/repair_report_zh.md). The audit/data/results/figures below preserve the pre-repair snapshot. Member1–3 and the shared1176-row merge have now been repaired; this page's original completion record is historical. Current source verification and analysis entry points write to `data/cache/remediation/current_member4/`; report/delivery commands use the current repair verifier. The v1 and earlier repair locks are retained; the latest reviewed version protects current files plus the external pre-change backup. See the root README for the active version and reasons for each revision. Do not use the historical “163 unchanged” claim to describe this repair.

For current tests, use a new isolated `--basetemp` path as shown in the root README; do not overwrite the historical `audit/test_results.xml`. National WPP, all612 U.S. labor rows and existing U.S. boundaries now have additional verification evidence in the owning modules. Original status rows below remain a record of what the previous audit did.

Start with [findings.md](findings.md), [audit_report.md](audit_report.md), and [the English presentation package](../../poster/member4/README.md).

2022 aging/manufacturing Pearson correlations: pooled **0.644435** (98 regions), USA **0.003224** (51), Japan **0.028647** (47). The pooled association nearly disappears within countries. **No defensible direction-reversal headline.** Source and sensitivity limits are in the findings and audit.

## Files

| Path | Purpose |
| --- | --- |
| `audit/input_manifest.json` | Initial and baseline commits; hashes for all 163 protected original files |
| `audit/repository_inventory.csv` | Member code, docs, datasets, figures, commands and origin commits |
| `audit/readiness.csv`, `issues.csv` | Four audit dimensions; issue severity, evidence, correction and owner |
| `audit/download_manifest.json`, `primary_source_verification_log.csv` | Exact official URLs, retrieval times, SHA-256 and check scope |
| `audit/source_record_checks.csv` | 15,027 numerical checks against primary data |
| `audit/sample_flow.csv`, `join_coverage.csv`, `missingness.csv`, `exclusions.csv` | Coverage, joins and explicit exclusions |
| `audit/corrections.csv`, `source_registry.csv` | Transparent integration changes and clean citations |
| `audit/claim_checks.csv` | Existing member claims checked against current numerical evidence |
| `data/core_2019.csv`, `data/core_2022.csv` | Fully audited main samples, 98 rows each |
| `data/integrated_context_panel.csv` | 1,176 matched rows; original fields plus source definitions/status |
| `data/analysis_samples.csv` | Exact analysis membership and reasons for missing context |
| `results/associations.csv`, `analysis_ledger.csv` | All declared estimates, weights, n, ranges and definitions |
| `results/covariance_*`, `leave_one_out.csv`, `influence_summary.csv`, `overlap.csv` | Decomposition, influence and support checks |
| `results/case_candidate_pairs.csv`, `selected_cases.csv` | All eligible cases and contrasting selections |
| `results/change_associations.csv`, `data/changes_2019_2022.csv` | One endpoint change per region |
| `figures/01–03` | Three poster-ready SVGs and 300-dpi PNGs |
| `audit/test_results.xml`, `reproduction_checks.csv` | Offline tests and isolated regeneration evidence |

At the time of the original audit, shared `data/processed/merged_analysis.csv` was a2022-only output and Member1–3 files were unchanged. Those historical statements no longer describe the current working tree: see the repair manifest. The original integration additions remain documented in [data_dictionary.md](data_dictionary.md); current shared definitions are in [the data contract](../../docs/data_contract.md).

## Historical audit commands (retained for the original record)

Use the root README for current reproduction. The original commands below include historical output paths and must not overwrite the frozen audit XML/registers during remediation.

From `E:\5002_project\aging-across-economies`, the prepared `.venv` uses the existing pandas/numpy/matplotlib installation plus pytest, openpyxl and xlrd. For a fresh standard environment, create a venv, install the project with `python -m pip install -e '.[dev]'`, then install `analysis/member4/requirements-audit.txt`. The extra readers are for official Excel inputs, not a replacement project stack.

```powershell
.\.venv\Scripts\python.exe -X utf8 analysis/member4/freeze_inputs.py
.\.venv\Scripts\python.exe -X utf8 analysis/member4/verify_sources.py
.\.venv\Scripts\python.exe -X utf8 analysis/member4/run_analysis.py
.\.venv\Scripts\python.exe -X utf8 analysis/member4/build_reports.py
$env:PYTHONPATH='src'
New-Item -ItemType Directory -Force -Path data/cache | Out-Null
.\.venv\Scripts\python.exe -X utf8 -m pytest -q tests member2_industry --basetemp data/cache/member4-pytest --junitxml=analysis/member4/audit/test_results.xml
.\.venv\Scripts\python.exe scripts/validate_data.py
.\.venv\Scripts\python.exe -X utf8 analysis/member4/verify_delivery.py
```

Everything above is offline with the current cache. Essential tests also run offline directly from the checked-in canonical data and delivered audit outputs. `verify_delivery.py` redirects Member 1/2 source builders into `data/cache/member4-reproduction`, then compares fresh Member 4 tables and figures byte for byte. It never overwrites their production files. Static Markdown presentation documents are authored source artifacts; `build_reports.py` regenerates numerical findings and machine-readable audit reports.

For a fresh source cache, before `verify_sources.py` run:

```powershell
.\.venv\Scripts\python.exe -X utf8 analysis/member4/download_sources.py
```

Downloads use only public official URLs and write `data/raw/member4/`, which is ignored by Git. A source checksum change blocks verification; do not edit the expected hash to force success. BLS raw HTML returned HTTP 403 in this run: the delivered, explicitly sampled table transcription documents primary-page checks and permits offline replay. It does not claim an offline full BLS source reconstruction. The raw download manifest is acquisition evidence, so retrieval timestamps are not regenerated during analysis.

Input locking is deliberate: if a teammate later changes a protected input, the pipeline stops for a new reviewed snapshot. Do not silently refresh the lock. Exact output bytes are reproducible in the recorded environment; matplotlib versions/fonts can change figure bytes elsewhere. See `audit/environment.json`.

Verification completed on 9 November 2026: 51 offline tests passed (one external AnyIO/pytest deprecation warning), all three canonical contracts passed, and 52 isolated reproduction checks passed. All 15,027 official-source field comparisons passed; this count includes multiple checks per record and is not an observation count. All three PNGs received visual review, and the 364-word speaking script is about three minutes at 120 words per minute. Original UN source acquisition, other-year U.S. labor verification, and map-boundary rebuilding were not performed; see the scoped audit verdicts.

## Safety and ownership

Local branch: `codex/member4-audit-integration`. Original checkout `10c5a47`; selected current-main baseline `2bede5b`. Remote actions were repository reads and fetch only. No commit, push, GitHub write, PR, issue, upload, deployment or publication occurred. No credential-bearing revision script was executed.
