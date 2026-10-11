# Polaris R001 — offline host gate

## Purpose

Provide **one reproducible command** that checks the R001 domain slice without an Android SDK. It must never confuse locally tested repository contracts with B01–B05 Android runtime acceptance.

The script is at `scripts/r001/run_host_gate.py`. From a **full Git checkout** of `Hailton-Reis/Polaris` branch `r001/multisource-foundation`:

```bash
python3 scripts/r001/run_host_gate.py --evidence-dir /tmp/polaris-r001-host-evidence
```

Prerequisites: Python 3 (stdlib), Bash, Java 21, `kotlinc`, and a Kotlin installation exposing `lib/kotlinx-coroutines-core-jvm.jar`. The Kotlin compiler and JAR paths are resolved by `scripts/r001/test_spike001_host.sh`. No Android SDK, Gradle, credentials, extensions, network access or backend server is needed **after the full repo has been checked out and the prerequisites are installed**.

## Gate matrix

| Gate | What is executed | Required test count |
| --- | --- | ---: |
| `python` | `python3 -m unittest discover -s scripts/r001 -p 'test_*.py' -q` | **54** |
| `sqlite` | `python3 -m unittest discover -s spikes/spike001/host-sqlite -p 'test_*.py' -q` | **10** |
| `kotlin` | `bash scripts/r001/test_spike001_host.sh` | **30** |

Counts were discovered in the checked-in test files on 2026-10-08: 54 Python test methods across six `scripts/r001/test_*.py` files, 10 SQLite methods, and 30 Kotlin `test(...)` registrations. Update minimum thresholds when expanding these tests.

`run_host_gate.py` captures combined output for each gate as `python.log`, `sqlite.log`, `kotlin.log`, and writes `host-gate-report.json` containing per-gate exit status, reported counts, minimum count and, if available, the Git commit hash. It returns nonzero unless **all three** return exit code 0 and their log summaries report the minimum count; both Python and SQLite must emit `OK` and Kotlin must emit `SPIKE001_HOST_INVARIANTS_PASS (30 scenarios); NOT_ANDROID_RUNTIME`.

Check the JSON `scope` field: always `HOST_ONLY_NOT_ANDROID_RUNTIME`. Missing tests, missing compiler, incomplete checkout or absent log markers are not PASS. The gate never claims an APK build, database engine in Android, original Yomotsu source extension, Cloudflare access, chapter pages, or migration-15 acceptance.

## Verified here vs still pending

On 2026-10-08 the **actual new runner code and its seven regression tests** were executed with Python 3 and passed **7/7**; Git blobs were verified byte-identical to local files. The new runner was also invoked against an **intentionally partial local workspace**, which proved its fail-closed behavior: SQLite **10/10 PASS**, while Python and Kotlin were explicitly `MISSING_OR_INVALID_TEST_SUMMARY`, final status `FAIL_OR_INCONCLUSIVE`, and process exit code 1. The complete 30-scenario suite and total 54 Python tests have **not** been run in this current container, because the full Polaris Git checkout is unavailable.

One GitHub Actions job was retried via the connected GitHub app: `Domain spikes` run [37838795183](https://github.com/Hailton-Reis/Polaris/actions/runs/37838795183), attempt 2. It again failed with `runner_id=0` and `steps=[]`. No Gradle or Kotlin test step executed on that runner. Owner-side diagnostics are in `ACTIONS_RUNNER_TRIAGE_2026_10_08.md`; avoid repeated CI retries until the account-side cause is found.

GitHub CI `.github/workflows/domain-spikes.yml` separately executes the same **Python and SQLite** suites and the **Gradle** host Kotlin/domain tasks when a runner is provisioned. It does not invoke `run_host_gate.py`, since a Kotlin CLI installation is not guaranteed on the standard hosted runner. Both paths provide complementary evidence, not Android acceptance.

**Next gate:** construct the latest APK from pinned Yomotsu with `scripts/r001/build_issue002.sh` and verify the real two-source Android B01/B02/B03/B04 and supplementary B05. Preserve the existing 24 spike decisions, keep issue #2 open, PR #1 draft, and SQLDelight migration 15 unapplied until device evidence is captured.

## Verified full three-suite run — 2026-10-09 (supersedes earlier partial-workspace note)

Reconstructed and hash-checked the **34 exact source files** required for this offline gate from the connected GitHub branch. The first complete attempt found a genuine unescaped-quote SyntaxError in spikes/spike001/apply_spike001.py, fixed as commit 4d699352. After the fix, the exact committed code passed the unified gate: **Python 54/54; SQLite 10/10; Kotlin 30/30; overall 94/94 PASS**.

Environment: JDK 21.0.12.1, kotlinc 1.9.0, Python 3.13.5, Kotlin coroutines jar. The report's repo_commit=null is honest because the validated environment was a source subset rather than a full git checkout. The Git blob SHA manifest enables independent re-verification.

Evidence ZIP (logs, JSON report, manifest): https://drive.google.com/file/d/11ELrmUrOK_EaoQ-B_Gty0HWijtzdVc6S/view ; SHA-256 b0077bafbd4aabfc7ea84f925346c5cbed2cf6eaa0febc3853ce88a698474772.

**Host PASS does not change the blocked Android B01–B05 status.** Read RESUME_2026_10_09.md before requesting additional fixture-only tests.


## 2026-10-09 updated minimums and new optional source API check

The active `run_host_gate.py` requires **62 Python**, **10 SQLite**, and **30 Kotlin** tests. The new 8 Python cases verify source-ID filtering in both pinned `LibraryUpdateJob` and `MetadataUpdateJob`; the full gate ran **102/102 PASS** with exit 0 and an explicit host-only scope. Older 54-case/94-total counts in this document describe an earlier successful run and are **superseded**, not current gate thresholds.

An additional, independent `MergedSource : Source` compiler check runs against the **exact pinned upstream API interface** using:

```bash
bash scripts/r001/test_merged_source_api_host.sh /path/to/pinned-yomotsu
```

This suite passed **8/8** with the pinned `Source.kt` and production `MergedSource.kt` classes; lightweight model/Rx types alone are stubs. See `spikes/spike001/host-source-api/README.md` for provenance and limits. It is not included in the 102-case unified gate because the full Yomotsu checkout is an additional prerequisite.

Actual baseline and patched Yomotsu automatic worker patch checks:

```bash
python3 scripts/r001/check_spike001_background_patch.py /path/to/pinned-yomotsu --mode baseline
python3 scripts/r001/check_spike001_background_patch.py /path/to/patched-yomotsu --mode patched
```

Both passed against hash-verified pinned source files on 2026-10-09. These source checks do not prove on-device library background refresh; user-facing behavior must be checked before release.

## 2026-10-11: full application contract and expanded host minimum

Active full-offline `scripts/r001/run_host_gate.py` now requires **72 Python + 10 SQLite + 30 Kotlin = 112 passing tests**. The added 10 Python tests validate the *entire* Spike-001 applicator against a synthetic pinned-signature source tree. A second check used seven genuine hash-verified pinned Yomotsu files and demonstrated **28/28 edits plus 18/18 added files** and exact interactor replacement.

Run the real end-to-end patch contract with a pristine pinned upstream and its already-patched copy:

```bash
python3 scripts/r001/check_spike001_full_apply.py /path/to/pristine-pinned-yomotsu /path/to/spike001-applied-yomotsu
```

The Android build script now runs this automatically after the pre/post checks and before Gradle. The check does **not** invoke Gradle, load an APK or certify B01–B05. Evidence archive: https://drive.google.com/file/d/1pEwZyiiJeuh4vGXfAAyyEYLdBR5venmr/view (SHA256 `cb73fca51f8c45cf77616304bc68500e5f7951ecda4691a0931da7016bb12702`).
