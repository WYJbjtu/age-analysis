# Age-specific domestic migration and regional aging

**READY WITH LIMITATIONS — both countries completed, 2019 and 2022 only.**
This additive module compares all 47 Japanese prefectures and 50 U.S. states plus
Washington, D.C. It never pools countries or changes the project's reviewed inputs.
The full-sample analysis precedes the illustrative cases. No industry or causal
analysis is part of this extension.

Start with [English findings](presentation/findings_en.md), the
[Chinese handoff](report_zh.md), and the [integration proposal](presentation/integration_proposal.md).
The latter proposes replacing the current Member 3 presentation slot, keeping the
group presentation within 12 minutes. Shared poster materials have **not** been rewritten.

## Figures for assembly

| Group | Main file | Use |
| --- | --- | --- |
| Figure 1 | [2022 regional associations](figures/figure1_regional_2022.png) | Main poster; all regions, ages 20–24 and 65+ |
| Figure 1 companion | [2019 associations](figures/figure1_regional_2019.png) | Explicit comparison-year evidence |
| Figure 2 | [Native age profiles](figures/figure2_native_cases.png) | Tokyo, New Hampshire, and DC; age detail and uncertainty |
| Appendix | [Japan](figures/appendix_profiles_jpn.png), [USA](figures/appendix_profiles_usa.png) | Complete ages20+ profiles; no omitted regions |

Each PNG is 300 dpi and has a same-stem editable SVG. Keep the source/uncertainty
footers and [captions](presentation/captions.md). The
[figure manifest](results/figure_manifest.json) records the inputs and intended use.
The appendix uses a separate color range for each country, shared across years.

## Sources, contracts and results

- [Source verification and definitions](sources/README.md), [exact URL catalog](sources/catalog.json),
  [retrieval timestamps and raw SHA-256](sources/manifest.json), [variable mapping](results/variable_mapping.csv).
- [Data dictionary and comparability limits](data_dictionary.md), [pre-analysis plan](analysis_plan.md).
- [Native flows](data/native_migration.csv), [harmonized flows](data/harmonized_migration.csv),
  [population denominators](data/population_denominators.csv), [joined analytical table](data/population_structure_join.csv).
- [All associations](results/associations.csv), [leave-one-out](results/leave_one_out.csv),
  [influence summary](results/influence_summary.csv), [case selection](results/case_selection.csv).
- [Coverage by actual valid/missing count](results/coverage.csv), [source/accounting checks](results/source_checks.csv),
  [Tokyo checkpoint comparison](results/reference_checkpoints.csv), [U.S. uncertainty](results/us_uncertainty_summary.csv).
- [Validation results](results/validation.json), [visual inspection](results/visual_inspection.json),
  [local extension integrity manifest](extension_manifest.json), [precise next-commit file list](next_commit_files.txt).

## Reproduce offline on Windows

From the repository root, use the existing environment if it satisfies
`requirements.txt`. A fresh environment needs `python -m pip install -r
analysis/age_migration/requirements.txt`; this dependency installation was not needed
for the completed native Windows run. No API credentials are required for offline reproduction.

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -X utf8=0 analysis/age_migration/verify_extension.py check
& $py -X utf8=0 analysis/age_migration/prepare.py
& $py -X utf8=0 analysis/age_migration/analyze.py
& $py -X utf8=0 analysis/age_migration/plot.py
& $py -X utf8=0 analysis/age_migration/build_docs.py
& $py -X utf8=0 analysis/age_migration/verify_extension.py check
```

`prepare.py` checks immutable cached raw bytes before parsing. All generated text
uses UTF-8/LF. Original source bytes, including Shift_JIS HTML and original file
line endings, are preserved by the module's `.gitattributes` rule.
The four declared read-only project inputs are the region lookup, Member 1 FIPS
mapping, Member 1 population detail, and repaired labor/migration table (Japan total
verification only); their exact paths/hashes are in the extension manifest. There
is no dependency on a private cache or an old branch.

Acquisition is a separate explicit command:

```powershell
& $py -X utf8=0 analysis/age_migration/acquire.py
```

With the delivered cache it performs hash checks, without network requests.
A missing file is fetched from the pinned official URL with timeout/size limits
and at most two attempts. Existing raw files are never replaced. Changed live
bytes fail the pinned check and require a separately documented source version.
The Census observation API redirected to a missing-key page during this task;
the official public Summary Files were successfully retrieved instead. This is
not claimed as a successful data-API request.

## Tests and protected-baseline checks

```powershell
$env:PYTHONPATH = 'src'
& $py -X utf8=0 -m pytest -q tests member2_industry analysis/age_migration/tests -p no:cacheprovider --basetemp data/cache/age-migration-new-test-run
& $py -X utf8=0 -X warn_default_encoding -m pytest -q tests member2_industry analysis/age_migration/tests -p no:cacheprovider --basetemp data/cache/age-migration-new-encoding-run
& $py -X utf8=0 scripts/remediation_state.py
& $py -X utf8=0 analysis/member4/freeze_inputs.py
& $py -X utf8=0 scripts/validate_data.py
& $py -X utf8=0 scripts/verify_remediation.py regression --no-write
& $py -X utf8=0 analysis/age_migration/verify_extension.py isolated
```

Choose previously unused `--basetemp` directories: pytest may clear its selected
temporary directory. The pre-freeze authoring validation runner uses UUID directories and
captures actual commands/results in `results/validation.json` and `results/logs/`.
After the extension is frozen, that runner refuses to overwrite the saved evidence;
use the listed read-only checks and isolated replay instead.
The isolated check copies the exact intended deliverables, including uncommitted
extension files, disables network access, and regenerates analytical tables,
results, figures and generated prose. It does not rely on `git archive` excluding
new work. It validates the four declared shared inputs as well as all extension files.

The old 315 tracked files and active v6 lock remain unchanged. `verify_extension.py
freeze` is an explicit, one-time authoring command which refuses to overwrite a
manifest; routine checks never refresh hashes. No successor shared lock is needed.
The original authoring-byte hashes remain in `results/baseline.json`.
`results/baseline_representation.json` separately declares UTF-8/LF representations
for portable verification, following v6's line-ending policy. Local validation
checks all 315 original byte hashes; isolated reproduction also tests LF copies.
This does not normalize original source bytes or rewrite any shared repository file.

## Interpretation boundaries

The primary rates use same-age current residents. Total-population-denominator
rates answer a different question. Japanese 2019 denominators retain the original
annual vintage; the canonical aging outcome retains Member 1's later revised
vintage. Japanese official-rate precision and exact age-reference-day limits are
recorded explicitly. ACS approximate uncertainty omits unavailable covariances;
ordinary correlations do not incorporate survey error or spatial dependence.
One year's migration flow does not explain the complete age structure or a causal
fraction of aging. Two snapshots are not cumulative 2019–2022 migration.

All work remains local. No commits, pushes, PRs/issues, uploads, or other remote
writes are part of this workflow.
