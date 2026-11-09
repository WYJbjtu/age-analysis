# Integrity verification and CI portability

This is a portability-only continuation of the 2026-11-09 remediation. The scientific data, figures, methodology and presentation narrative are unchanged. The previous remediation records remain historical. See `report_zh.md` for actual validation results and the next-commit inventory.

The 2026-11-10 encoding follow-up uses reviewed **v6**, retaining v5 and the same historical evidence ZIP. UTF-8 repository text is read explicitly; CI and the encoding regression run with `-X utf8=0`. Project-owned `EncodingWarning`s fail diagnostic tests; third-party warnings are not suppressed. See [the encoding repair record](encoding_fix_zh.md) for actual locale and test results. Explicit successor-lock creation now extends the active lock named by the authorized delta, rather than returning to v4.

## Four verification layers

1. **Current reviewed deliverables:** `docs/remediation/input_manifest_v6.json` protects the previous inventory, the authorized encoding code/configuration/test delta, and required portable evidence. Verification always checks these files; a missing lock/file or checksum mismatch is an error.
2. **Immutable historical audit artifacts in the repository:** Member4's audit, data, result and figure files are independently compared with the original bytes preserved in the ZIP. Only the explicitly declared repository text line-ending representation may differ.
3. **Original pre-remediation bytes:** `docs/remediation/historical_evidence.zip` contains exactly the 229 files in the original prechange manifest, plus the original prechange manifest and v2/v3/v4 lock files. Every original file is verified against the unchanged original SHA-256; the 163-file v1 manifest is checked separately. The JSON inventory records each member, provenance, size and the archive SHA-256. Archived scripts, including the unsafe historical BLS checker, are evidence only: never import or execute them.
4. **Additional local backup:** the old absolute Windows location is metadata only. Normal verification never opens it. An explicit `--local-backup PATH` checks `PATH/files/` against all 229 original hashes and fails if missing or corrupted; it never falls back silently.

The ZIP and inventory are normal deliverable files, not Git-ignored caches or Git LFS pointers. Paths resolve from the module's repository root, not the shell's working directory. Verification reads members directly, never extracts them, and rejects absolute/traversal/backslash/drive paths, duplicate entries, unsafe links, encrypted members and excessive sizes. Normal verification has no network or manifest-writing operation.

## Byte representation and prior locks

The original Windows working tree contained CRLF in some files, while Git stored LF. `.editorconfig` alone did not control Git checkout. `.gitattributes` now declares `text=auto eol=lf`, with binary formats and the evidence ZIP explicitly `-text`.

Each v5 entry explicitly states `utf8-lf` or `bytes`. For `utf8-lf`, the verifier validates UTF-8 and replaces **only CRLF with LF**. Lone CR is rejected; spaces, encoding, content and final-newline presence are not changed. Binary files are hashed exactly. This permits both pre-existing Windows CRLF copies and LF fresh checkouts without rewriting numerical inputs or historical files. The per-file authoring-byte hash and previous-v4 hash document the mapping; `line_endings_before.json` records comparison with Git objects.

Inside the ZIP, all original bytes and hashes remain exact, including CRLF. The original prechange and v1/v2/v3/v4 manifests are never rewritten. Prior lock-chain hashes are validated against the preserved original bytes, while their repository copies are checked against the explicit LF representation. v5 exists because the integrity implementation, workflow, test scope and evidence delivery changed—not because a failed scientific expectation was relaxed.

`build_portable_integrity.py` is an explicit local authoring tool. `package` refuses to replace existing evidence; `lock --version N --delta PATH` refuses to replace existing locks, requires an exact authorized delta and rejects changes to data, figures or immutable artifacts. It is never called by CI or tests. Ordinary `freeze_inputs.py` is now a read-only compatibility entry point and cannot create a replacement lock when evidence is missing.

## One offline test suite

The old default was `testpaths = ["tests"]`: 40 collected tests. The previous local command additionally selected `member2_industry`: 25 more cases, yielding 65. Those 25 tests use delivered tables, pure parsers and isolated synthetic fixtures; none downloads official sources or needs private caches. The default now includes both directories, plus the new portability tests under `tests/`. The same `python -m pytest -q` command is used locally and on both Linux and Windows CI with Python3.11.

Install `python -m pip install -e '.[dev]'` in a fresh environment. The selected suite needs the declared pandas, NumPy, Matplotlib and pytest dependencies; it does not need the optional source-download/XLS/map stack. Full source reacquisition and figure regeneration remain explicit research workflows, outside routine offline CI. Their earlier results are not rerun or relabeled by this fix.

```sh
python scripts/remediation_state.py
python analysis/member4/freeze_inputs.py
python -m pytest -q
python scripts/validate_data.py
python scripts/verify_remediation.py regression --no-write
```

From another working directory, invoke the integrity scripts by absolute path. The regression check computes the existing 38 high-precision comparisons without rewriting its saved table. CI never creates archives, updates locks or runs source acquisition.

All modifications in this task remain local: no commit, push, PR, issue, upload, deployment or other remote write is authorized.
