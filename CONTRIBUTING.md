# Contributing

Current local remediation (2026-11-09): the user explicitly authorized changes across Members 1–3 and shared interfaces. This task requires no issue, PR, commit or branch change; remote writes are prohibited. The general collaboration procedure below applies to later team development, not permission for remote actions in this repair. Current results: [repair record](docs/remediation/repair_report_zh.md).

1. Read `docs/data_contract.md` and `docs/team_tasks.md`.
2. Create your own feature branch: `git switch -c feature/member1-demographics` (change number).
3. Only edit your data-owned CSV and personal module; modifying shared contracts requires a documented issue and coordination.
4. Record actual sources in your own `memberX_*/sources.csv`; put original downloads under ignored `data/raw/`.
5. `python scripts/validate_data.py && python -m pytest -q` before opening a PR.
6. PR description must include: source dataset URLs, coverage by year/country, missingness, sample row / computed checks, 1–2 key findings, planned chart names, limitations.
7. Obtain at least one teammate review before merging. Prefer squash merge; never force-push shared `main`.
8. No AI-generated numerical research claims without rechecking the authoritative statistics.
