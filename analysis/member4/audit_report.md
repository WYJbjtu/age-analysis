# Member 1–3 audit and Member 4 readiness

Audit date: 9 November 2026. Audit the work, not its authors. Numeric source checks, coverage, reproducibility, and claims are assessed separately in `audit/readiness.csv`; individual issues are in `audit/issues.csv`.

## Repository and version decisions

The requested repository is `https://github.com/WYJbjtu/age-analysis`. The initial local branch was clean `main` at `10c5a4792a22abedd40347d019e879d848b61dd5`. Remote reads revealed current main `2bede5baa1c8dcc308ed29985cbccc20527d6d11`. A new local, nontracking branch `codex/member4-audit-integration` starts at that inspected main. Local main was not rewritten and no teammate branch was merged by this task.

All required teammate work was already merged into remote main. Demographics was last changed at `1d91bc099d0b900e8cd3843d94607b6383ca77b6`, industry at `9ca63420b9feb28e3a5e2b2bd46dea314522d403`, and labor/migration at `9f4f04660931f1fe69290791830614bda9016d88`. Accessible remote branches were main, feature/jpn-demographics-2022, feature/member1-complete, and feature/member2-industry-handover. Their latest work is included in the selected main. No local-only Member 3 inputs or ignored raw datasets were present in this working directory at the start. No inputs from unrelated workspaces were read.

`audit/input_manifest.json` locks all 163 previously tracked files by SHA-256. No shared contract or teammate-owned file was changed. The initial repository had no AGENTS.md, separate proposal, standalone course rubric, dependency lockfile, or newer scope agreement. README, CONTRIBUTING, data contract, team tasks, source manifests, lookup, Python code, tests, figures and findings were inspected. Course compliance beyond the supplied prompt and repository outline is **NOT ASSESSED**.

Current scope extends the old README's optional history to an actual 2011–2022 panel. This does not change the primary 2022 / comparison 2019 design. The team explicitly excludes pooled service comparisons. Historical README instructions to push, create issues and PRs conflict with this task's local-only restriction and were not followed. Shared ownership guidance is honored. The old shared merge and registry remain preserved; use the Member 4 paths in README for this audited delivery.

## Member 1

**Regional numerical data: PASS. Comparability: PASS WITH LIMITATIONS. Reproduction: PASS WITH LIMITATIONS. Claims/figures: PASS WITH LIMITATIONS, with national-source and map-geometry checks NOT ASSESSED.**

All 1,176 regional demographic rows were reconstructed from separately downloaded files matching the owner's pinned hashes. US Census records use resident population, both sexes, all origins, six mutually exclusive race groups and ages 0–85, with 85 denoting 85+. Ages 65–85 form the older numerator. Working age is 15–64; the dependency ratio is 100 × 65+ / 15–64. Japan uses total residents, not Japanese citizens alone. Published thousand-person counts retain their precision; 2021/2022 official one-decimal shares are not replaced by ratios of rounded counts. All canonical totals, aging shares, working-age shares and dependency ratios match their source calculations or published values within 1e-7 percentage point.

US population is July 1, Japan October 1. The US 2019→2020 transition changes census base and release. Japan's historical count-derived and later published rates have different precision. These are known, disclosed limitations, not grounds to invent corrections. The integration keeps source_version, population_reference_date, count_precision_persons and rate_method.

2022 US aggregate older / total population is 57,794,852 / 333,287,557 = 17.340837%; it is not the unweighted regional mean. Japan's summed rounded counts give 36,235,000 / 124,946,000 = 29.000528%, consistent with its 29.0% published context at source precision. The WPP national series is explicitly separate. Its supplied snapshot passed internal consistency checks, but the original approximately 240 MB UN workbook was not independently retrieved, so its external numerical accuracy is **NOT ASSESSED** here and it is not used for Member 4 findings.

The current regional ranked chart uses the same 0–45% scale and all region labels; it distinguishes regional medians from national rates. The legacy US map code uses FIPS joins, actual boundaries and a common normalization across its insets; primary input values were checked. Boundary geometry/download reproduction was not repeated, so map geometry is **NOT ASSESSED**, not silently passed. No existing member figures were regenerated in place.

## Member 2

**Numerical data and production code: PASS. Manufacturing cross-country comparability: PASS WITH LIMITATIONS. Pooled services: BLOCKED. Existing manufacturing claims: PASS.**

All 1,176 industry rows match the pinned BEA/Cabinet Office sources for nominal GDP, manufacturing value added, selected services and their shares. US amounts are millions of current USD; Japan millions of current JPY. Shares use same-country, same-year nominal numerators and denominators. No gross output, revenue, employment share, real chained addition, or currency conversion enters the primary measure.

BEA SAGDP2 line 12 is manufacturing (NAICS 31–33); line 1 is GDP. The source footnote identifies the September 30, 2026 revision. Japan uses column I manufacturing and BL GDP in the FY2011–FY2022, 2008SNA / 2015-benchmark release. The 564 Japanese denominators also match the separate soukatu1 workbook. Published tertiary sums and GDP = industry value added + import taxes − capital-formation consumption tax reconcile within announced rounding tolerances. No shares are rescaled to force 100%.

US services are line 92 private services, including utilities and excluding government. Japan BO is the official tertiary aggregate including public activities. Neither is 100% minus manufacturing. Within-country service results are retained; pooled services and cross-country service rankings are blocked. FY2022 means April 2022–March 2023, while US GDP is CY2022. Changes in nominal shares can reflect relative prices and denominator movements, not real production or manufacturing jobs.

Member 2's tests are explicitly included because default pytest discovery omits that directory. Its source builder is reused for read-only verification and rebuilt in a disposable directory. Existing chart validation checks full coverage, units, share arithmetic and bounds. No teammate output is overwritten.

## Member 3

**2019/2022 labor and migration context: PASS WITH LIMITATIONS. Continuous all-resident Japanese migration history, advertised full US raw rebuild, Figure 4 bounds, and reversal narrative: BLOCKED pending owner correction.**

All 564 Japanese labor rows and detailed counts match the retrieved official LFS workbook, including all 94 rows for 2019/2022. Six US states per year were sampled directly from BLS archived table 1 (California, Nevada, Indiana, DC, Maine, North Dakota), covering large, extreme and case-study observations. All 24 sampled employment/rate comparisons match. Direct BLS HTTP retrieval returned 403; primary tables were accessible through web reading. `bls_primary_table_sample.csv` is an explicitly derived transcription with original table/release IDs, not a claimed raw HTML copy. Other US labor years have supplied provenance but are **NOT ASSESSED** independently.

Employment is residence-based persons, not jobs. US LAUS covers civilian noninstitutional ages 16+; Japan LFS ages 15+. These are annual averages, not single months. Rounded labor-force, employment and unemployment counts are retained in persons after ×1,000 conversion. Every available detail record passes a rounding-interval check: counts rounded to 1,000 imply ±500 intervals, and rates rounded to 0.1 imply ±0.05 percentage point. Exact equality of a displayed rate to a ratio of rounded counts is not demanded. No labor-force participation rate is manufactured from total population.

The Japanese workbook notes that six prefectures use ratio estimates; other prefectural estimates use the model framework. It documents benchmark revisions, supplemented 2011 estimates for Iwate, Miyagi and Fukushima, and model support for earthquake-affected Kumamoto in 2016. These special observations are retained and flagged as methodological context; they are not ordinary exact headcounts. A shared release does not imply absence of statistical breaks.

All 612 US total net-migration values match official NETMIG columns. These include international moves. Member 4 adds separately named domestic_net_migration using official DOMESTICMIG for 2019/2022, preserving the original net_migration values. All 94 Japan values for those years match table 1 column U and in-migrants minus out-migrants; they cover all nationalities and sum to zero within year. US periods remain July-to-July, Japan calendar years. No migration rate or age-specific migration inference is made.

The historical Japanese table explicitly says **Japanese**, not all nationalities. All 329 values for 2011–2017 reproduce, but their claimed all-resident coverage does not. The 2018 scope transition must not be hidden by a continuous line. Japan migration for 2018/2020/2021 was not independently numerically checked in this audit; the two main years and 2011–2017 source were checked exhaustively.

Major issues are recorded with owner actions in `audit/issues.csv`: malformed source CSV; missing US raw-extract builders; unsafe/non-equivalent BLS revision checker; Akita clipped by the Figure 4 x-limit; and an unsupported labor “sign reversal” despite both Pearson correlations being negative. Smaller narrative errors and stale row counts are also recorded. The checker was not executed and no API key was read. No leak is asserted merely from inspecting the code.

The updated 2022 labor correlations are USA Pearson −0.054091 / Spearman +0.004942 (n=51) and Japan −0.460084 / −0.442502 (n=47). A near-zero coefficient does not prove no relation exists. Choosing cases and then fitting an outlier screen to the same data is not independent corroboration. Similar age does not isolate an industry's causal effect.

## Integration and acceptance

The lookup has exactly 51 US states/DC and 47 prefectures. Source records were mapped and checked against names/codes; national totals and Puerto Rico were excluded. All three canonical tables have exactly 1,176 unique matching region-year keys. The main and comparison samples are each 98, with zero exclusions; available and common-region samples coincide. The 1,176-row contextual panel keeps source limits visible. Optional domestic migration is independently populated for 196 rows only; missing context outside those years stays missing and never removes a primary row.

The audit performed 15,027 field comparisons and 564 Japanese GDP reconciliations. Field counts are not independent observations: some records contribute several fields and both detail/canonical checks. Download identity, checksum, retrieval time, check scope, and tolerances are exported. The official source log distinguishes unavailable raw downloads from accessible primary-page checks and unassessed sources.

No central numerical error was found in the primary pair. No Critical issue is recorded. Major limitations and specific blocked claims remain visible. Metadata corrections, a new domestic series and an independent source registry are the only integration corrections; no teammate numerical field was rewritten. No raw values are imputed or normalized.

Completed and usable: audited 2019/2022 cores, pooled/grouped statistics, common-sample/DC/rank/leave-one-out sensitivities, covariance decomposition, limited endpoint changes, three figures and English presentation sections. Completed with limitations: population weighting and optional within-country context. Blocked: pooled services, continuous all-resident historical migration, unsafe revision checker and selected Member 3 original claims/figure. Not attempted: full annual association series, large multivariable/panel models, original UN source download, independent re-audit of other US labor years, map-boundary rebuild, and a replacement group poster. These are not required for the valid cross-sectional delivery.

Test and reproduction outcomes are recorded in `audit/test_results.xml` and `audit/reproduction_checks.csv`. The first local test attempt exposed an absent temporary parent directory and a positional assumption in a new synthetic test; both were fixed. Research data and estimates were unaffected. No source-writing owner entry point was run in the shared project. Final protection checks cover all 163 baseline files.
