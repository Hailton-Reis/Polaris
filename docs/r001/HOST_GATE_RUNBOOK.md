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

## 11/10/2026 — Atualização da auditoria

O gate vigente requer **72 Python + 10 SQLite + 34 Kotlin = 116 testes**, com resultado host-only. Foram acrescentados 4 cenários Kotlin para validar argumentos de criação, prioridade/deduplicação e zero assinado; novo algoritmo de deduplicação usa mapa linear em vez de busca quadrática.

`python3 spikes/spike001/audit/reproduce_known_gaps.py` é um **diagnóstico de dois defeitos ainda presentes** (#9 e #10), não integra o gate verde. Detalhes e prioridades no novo `docs/r001/AUDIT_GAPS_2026_10_11.md`. Android B01–B05 permanecem sem evidência.

## 2026-10-11 revised Kotlin host threshold

Current unified host gate requires **72 Python, 10 SQLite and 38 Kotlin scenario assertions = 120 total**. Four added tests assert reference normalization in the real `GetMergedChaptersByMangaId` implementation:
- repeated source links produce a single set of chapters even in NO_DEDUPE mode;
- rows belonging to another merged parent cannot leak into its chapters;
- a malformed parent-as-real-child reference cannot load a virtual parent as a real child;
- duplicate/cross-work priorities cannot override the selected source.

Source was first run against unpatched reader code (failure reproduced), then corrected and all 38 Kotlin scenarios passed, alongside 72 Python and 10 SQLite. These are host tests; Android/SQLDelight runtime and SQL persistence still require device validation. Evidence: https://drive.google.com/file/d/1x4NA1OAadA23NaWQpYfVDy08zsLt_El9/view.


## 2026-10-11 — SQLite idempotency regression extension

The **current** host gate has **72 Python + 20 SQLite + 38 Kotlin = 130 total cases**. Ten new SQLite contract cases execute both actual `merged.sq` insert statements, validating no duplicate writes across retries (including a 4-connection file-backed SQLite race), null/orphan fallback identity, source settings preservation, multi-parent membership and explicit unlink/relink. Prior 120-test/10-SQLite counts in this runbook are superseded.

Execute `python3 -m unittest discover -s spikes/spike001/host-sqlite -p 'test_*.py' -v` for SQLite alone, or `python3 scripts/r001/run_host_gate.py --evidence-dir /tmp/r001-host-evidence` for the combined host gate.

**This is DML-only mitigation and not a SQLDelight-generated Kotlin or Android runtime proof.** A true schema UNIQUE key, existing duplicate repair and two concurrent parent creations await issue #10's tested upgrade path. Evidence: https://drive.google.com/file/d/1Ii4t2QUChADw6KjTIVG82dDbe1XMkIS3/view.


## 2026-10-11 — merged work selection SQL regression and 27-case SQLite minimum

Active `run_host_gate.py` thresholds: **72 Python, 27 SQLite, 38 Kotlin**. New `spikes/spike001/host-sqlite/test_merge_select_integrity.py` ensures selection of one manga object per linked manga ID despite legacy duplicate rows, stable priority/tie order, cross-parent separation, missing child behavior, and priority updates. The two production queries in `merged.sq` now use explicit ordering and a grouped `manga_id` subquery.

In this checkpoint the full **27/27 SQLite**, **72/72 Python**, and **38/38 Kotlin/JVM** suites each passed when invoked independently using hash-matched source files. The **unified** gate exceeded tool duration during the Kotlin step and produced no final report; it is therefore not labeled `PASS` for this checkpoint. Evidence ZIP: https://drive.google.com/file/d/1rpLs10hlX343u0HlSTldyp6O27NBjRRA/view. SQLDelight Android generator and runtime remain unverified.


## 2026-10-11 — source-scoped virtual work deletion

Current minimum host gate: **72 Python + 36 SQLite + 38 Kotlin**. Nine new test cases in `test_merge_delete_lifecycle.py` plus a revised existing assertion cover deletion of the **virtual parent row** through `deleteByMergeId`, preserving real child rows with FK cascade; single-reference unlink remains separate. On original staged SQL, the new tests failed **6/8**. On corrected SQL, SQLite **36/36 PASS**; Python **72/72** and Kotlin **38/38** passed in separate full executions. Unified orchestration was inconclusive due tool timeout during Kotlin, not reported as PASS.

The repository's Kotlin implementation passes the constant `MERGED_SOURCE_ID` to the source-guarded SQL query. SQLDelight generator output and bundled SQLite Android runtime **have not been compiled/executed**. The Yomotsu remove-from-library UI normally only changes favorite state and is not this explicit deletion path; integration acceptance remains issue #8.

## 2026-10-11 — issue #11 backup contracts added to the mandatory offline gate

`run_host_gate.py` now has **five mandatory stages**. Minimum expected cases: **72 Python + 36 SQLite + 38 Spike-001 Kotlin + 14 backup SQLite + 24 backup Kotlin = 184**. The actual Python suite now includes 3 additional parser regression cases, so counts can exceed the minimum. The total **184 is a configured minimum, not a claim of a completed unified run**.

New stages:
- `backup-sqlite`: `python3 -m unittest discover -s spikes/spike001/backup -p 'test_*.py' -q`, 14 cases.
- `backup-kotlin`: `bash spikes/spike001/backup/run_tests.sh`, 24 scenarios, validated by its unique `MERGED_BACKUP_RESTORE_PLANNER_PASS 24` marker.

`test_run_host_gate.py` checks that incomplete, duplicate or low-count markers and nonzero exit codes cannot be recorded as PASS. All **10/10** parser/self-tests passed using the exact published file (`a89699db702a02127d594247de417a11b9b3a6ba`). The Python runner file itself matched Git blob `bb473647aaca5528ecafd452d2d2ef1d3c00e01f` after local execution.

**Actually executed now:** both backup stages under the real `run_all()` aggregator in a hash-checked partial checkout: `backup-sqlite=14/14 PASS`, `backup-kotlin=24/24 PASS`, 0 exit code; `repo_commit=null` is expected because this was not a full Git checkout. The other three stages were *not* run in this checkpoint, therefore **NO combined 184-case PASS** is claimed. Scope remains `HOST_ONLY_NOT_ANDROID_RUNTIME`.

CI integration:
- `spikes/domain-lab/build.gradle.kts` compiles `spikes/spike001/backup/*.kt` in the test source set and adds `spike001Backup` as a dependency of `checkSpikes`; no Kotlin CLI installation is needed in that Gradle job.
- `.github/workflows/domain-spikes.yml` independently runs the 14-case backup SQLite suite before Gradle and triggers on `scripts/r001/**` changes as well as the spike code.
- CI jobs still failed *before any steps*: domain run [38181256441](https://github.com/Hailton-Reis/Polaris/actions/runs/38181256441) and Android run [38181256434](https://github.com/Hailton-Reis/Polaris/actions/runs/38181256434) each show `runner_id=0`, `steps=[]`. This does **not** prove success or failure of Gradle builds. Recheck runner provisioning before declaring build acceptance.

Run the full gate only from a full source checkout with all prerequisites:
```bash
python3 scripts/r001/run_host_gate.py --evidence-dir /tmp/polaris-r001-host-evidence
```

Production backup protobuf serializer, SQLDelight code generation, Android issue #2 B01–B05, and migration15 remain **pending**. The candidate SQL relink is tested only on host SQLite, and is **not** applied to `merged.sq`.

## 2026-10-11 — three new backup SQL regressions: 187-case configured minimum

The current SQLite backup suite is **17 tests**, not 14. Its three new RED-then-GREEN cases ensure:

- a source ID + URL shared by two real `mangas` rows is not arbitrarily relinked;
- a malformed `merged.merge_id` pointing to a real manga is never treated as a virtual parent;
- a resolved edge whose stored source URL does not match the actual child never authorizes deleting the pending reference.

`run_host_gate.py` and `test_run_host_gate.py` were raised to minimum `backup-sqlite=17`. Parser suite **10/10 PASS**. In a hash-matched source subset, the real runner's two backup stages returned `backup-sqlite 17/17 PASS` and `backup-kotlin 24/24 PASS` with `HOST_ONLY_NOT_ANDROID_RUNTIME`. The five-stage mandatory minimum is now **187** (72+36+38+17+24), but a complete five-stage run has **NOT** been executed in this checkpoint.

Preserved failure-before-fix and green evidence, logs and Git hashes: [Polaris Issue11 hardening ZIP](https://drive.google.com/file/d/1XPMcRYO4LHs35xySldVu8k-IDXb8_DNg/view?usp=drivesdk) (SHA256 `0da0bca28355833160a328575540e21b351e7b1b12f94728f9351a7c9719c363`). The candidate does not touch the production Yomotsu SQLDelight schema or migration14/15; Android B01–B05 and protobuf backup round-trip are still blocked on the build/runtime environment.

## 2026-10-11 — backup exporter gate +207 configured minimum

The backup Kotlin stage now compiles and runs **both** the original 24-scenario restore planner and the new 20-scenario export planner in the same `run_tests.sh`. `extract_count("backup-kotlin")` fails closed unless there is **exactly one** standalone marker for each suite:
- `MERGED_BACKUP_RESTORE_PLANNER_PASS 24`
- `MERGED_BACKUP_EXPORT_PLANNER_PASS 20`

The backup-kotlin minimum is therefore **44**, with backup-sqlite **17**. The five mandatory configured minimums are **72 + 36 + 38 + 17 + 44 = 207**. The minimum is a threshold, not a passing full-project result.

From a hash-verified local source subset, **both backup gates passed together** through the actual offline `run_all` function: SQLite **17/17**, Kotlin **44/44**, exit 0, `scope=HOST_ONLY_NOT_ANDROID_RUNTIME` and `repo_commit=null` because the checkout was partial. The gate parser regression file also completed **11/11 PASS**, including rejecting missing, duplicate, spoofed or undercounted success markers.

`spikes/domain-lab/build.gradle.kts` requires `spike001BackupExport` alongside `spike001Backup` in `checkSpikes`. CI Gradle compilation **was not executed** here (no Android SDK or Gradle CLI / active Actions runner). The full five-stage 207-case gate was not executed. This validates portable backup selection/restore planning, not serialization of an actual Yomotsu backup nor on-device data recovery.

Evidence: [Polaris R001 — exported child backup test ZIP](https://drive.google.com/file/d/14x40OxzeY3JO0uIpV9DfIBYiBMeWTD8B/view?usp=drivesdk), SHA256 `137acb0181c17026ead2a60f9f3773e352e2b1c64e23efd7735085e1dd3defce`. Backed up in the project Drive folder.

## 2026-10-11 — supplemental protobuf format candidate checks (#11)

A **separate** staged protobuf candidate exists at `spikes/spike001/backup/proto-candidate/`. It is deliberately outside the current `apply_spike001.py` and the normal five-gate offline runner. The **full gate minimum is still 207**, not 244.

Host validations (independent): **7/7** pinned-source patch tests, **18/18** Kotlin DTO validation tests compiled against annotation/BackupManga **stubs**, and **12/12** dynamic `google.protobuf` wire-compatibility simulations (old→new/new→old data and gzip), totaling 37 additional PASS. Real Yomotsu `kotlinx.serialization.protobuf.ProtoBuf`, Gradle, Android, actual `.tachibk` export and database restore **remain unverified**.

To reproduce staging against the pinned `Backup.kt`, run:
```bash
python3 -m unittest discover -s spikes/spike001/backup/proto-candidate -p 'test_proto_apply.py' -v
python3 spikes/spike001/backup/proto-candidate/apply_backup_proto_candidate.py \
  --pinned-backup /absolute/path/to/pinned/Yomotsu/app/src/main/java/eu/kanade/tachiyomi/data/backup/models/Backup.kt \
  --output-dir /tmp/polaris-backup-proto-stage-new-dir
bash spikes/spike001/backup/proto-candidate/run_model_validation.sh
```
The GitHub `domain-spikes.yml` CI now **requires the 7 Python staging tests** when a runner is allocated; it does not execute real Kotlin serialization. Complete 12-test protobuf simulation sources and logs are archived in [Polaris Drive evidence](https://drive.google.com/file/d/1dicLCIZXa-DJWW8OaR8J852fryD6Qpdx/view?usp=drivesdk), SHA-256 `704b3f3f261a576821744baca27babdd0b6638b0d0d9d02ed73c385063cb3bd5`.

No migration15, original backup serializer or Android APK was changed, and there is **no complete updated unified-gate PASS claim**. Issue #11 remains P0 open. See [proto candidate README](../../spikes/spike001/backup/proto-candidate/README.md).

## 2026-10-15 — persistent UUID candidate is now part of the backup JVM gate

New candidate: `spikes/spike001/backup/uuid-candidate/YomotsuMergedWorkUuidStore.kt`.
It uses the **existing** pinned Yomotsu `Manga.memo` JSON and
`MangaRepository.update(MangaUpdate(id, memo))` APIs to persist a
canonical per-virtual-parent UUID (`polaris.merge.work.uuid`).
No migration 15 or app runtime files were modified.

`ensure` reuses/persists a UUID for source 6969 virtual parents;
`ensureDistinct` prevents repeated work IDs and conflicting UUIDs
in the export selection; `assignArchived` preserves the actual UUID
from a backup when restoring a new virtual parent, and refuses to overwrite
a conflicting local UUID. Saves are verified through repository readback.

**Exactly executed (standalone Kotlin host, 2026-10-15):**
- Restore planner: 24/24
- Export planner: 20/20
- New UUID store/restore: 21/21
- **Combined `bash spikes/spike001/backup/run_tests.sh`: 65/65 PASS**,
  code, host stubs, test mains and runner hash-matched to the GitHub blobs.

`run_host_gate.py` now requires three unique distinct Kotlin markers,
`MERGED_BACKUP_RESTORE_PLANNER_PASS 24`,
`MERGED_BACKUP_EXPORT_PLANNER_PASS 20`,
`POLARIS_PERSISTED_MERGE_UUID_PASS 21`; duplicate or absent markers
fail closed. The configured five-gate minimum is
**72 Python + 36 SQLite + 38 main Kotlin + 17 backup SQLite +
65 backup Kotlin = 228**. **This is not a claim of a completed
228/228 unified gate.** The new Python parser tests were updated, but not
independently executed as a full suite in this checkpoint.

`spikes/domain-lab/build.gradle.kts` has a `spike001UuidStore`
JavaExec task required by `checkSpikes`, but the Gradle/Android
tests did NOT execute successfully in GitHub Actions. The 2026-10-15
runs [Domain Spikes 38799775389](https://github.com/Hailton-Reis/Polaris/actions/runs/38799775389)
and [Android 38799775637](https://github.com/Hailton-Reis/Polaris/actions/runs/38799775637)
each have `runner_id=0` and `steps=[]` — a blocked CI infrastructure
gate, **not** verified application compilation failure.

[JSON/hash-manifest/log evidence](https://drive.google.com/file/d/1KyLLuGPBziDX4hMbudXEpE5pLlDua0Li/view)
SHA-256 `e057ed04c44b9325072c6a329874bd5feb678264afc411ce5a8bacd5809ac303`.
[Handoff dated 2026-10-15](RESUME_2026_10_15.md).

**Limits:** tests use Yomotsu API-shaped stubs (not the real Android DB or
`kotlinx.serialization.json` library), no physical UNIQUE or CAS on memo;
the exporter/restorer app adapters, actual protobuf codec and Android
B01–B05 are still required before #11 can be closed.

## 2026-10-15 — Gradle backup lab split and TOCTOU fail-closed checks

Static audit found a **real task graph error**: `spikes/domain-lab` exposed
`spike001ProtoModel`, `spike001ProtoBuilder` and `spike001UuidStore`
JavaExec tasks without adding their nested source files to the compiled
source set. Even with a runner, those main classes would not be available.
Blindly adding test doubles into the domain module would risk interfering
with unrelated spikes.

The fix is the separate `spikes/backup-lab` module: five explicit test
source roots, five independent JavaExec mains and a `checkBackup` aggregate.
`domain-lab` no longer advertises backup tasks it cannot compile.
`domain-spikes.yml` triggers on the new module and invokes
`gradle -p spikes/backup-lab checkBackup --no-daemon --stacktrace`
**before** running the unrelated domain tests. A new
`scripts/r001/test_backup_lab_structure.py` provides offline Python
preflight against missing paths, ghost tasks and CI drift.

An additional candidate race was reproduced: if the underlying virtual
work changed a `localMangaId` to/from `NULL` between export planning
and protobuf bundle assembly, the old builder trusted the new
`isPending` flag without comparing it to the original association.
`MergedBackupExportPlan.plannedVirtualWorks` now stores defensive
per-parent snapshots; `BackupPolarisBundleBuilder.build` refuses
archive assembly unless the complete current parent and its links match
the saved plan. Changes to parent ID/UUID or child pending state
trigger a **retry, not a silent incomplete backup**.

**Verified actual local compiler execution:** all five test mains
compiled together under host `kotlinc`; **102/102 PASS**:
24 restore + 20 export + 18 proto DTO + 19 builder + 21 UUID.
New builder tests fail on old source at scenario 17 (RED) and pass
19/19 on corrected source (GREEN). The three changed Kotlin files in
the actual runner matched GitHub blob SHAs
`d55b227e16b09b35659690e118a54ebd04fd3043`,
`c2f93019f858f95283f08dcd0cbc4b54ad403af6`,
`a7140737fd9aadb8ba8ae38edc02e075c6640b90`.
Additional seven direct GitHub-source CI/task structure assertions all
passed. No successful **Gradle CLI** execution, Kotlin protobuf runtime
validation or Android tests were performed.

[Evidence ZIP in Polaris Drive](https://drive.google.com/file/d/1jd9Et9pOZMqDhFd7TL9kMk2qlYwM953D/view),
SHA256 `380bace69264e44cd634ab91bc41de24a79e1f89a6cb8890362eebe4b62ae5d6`.
The configured five-gate minimum remains **228**, which is NOT a
reported completed full gate; `checkBackup` is a separate host
compiler gate. Latest Actions [domain 38803383325](https://github.com/Hailton-Reis/Polaris/actions/runs/38803383325)
and [Android 38803383316](https://github.com/Hailton-Reis/Polaris/actions/runs/38803383316)
had `runner_id=0`, `steps=[]`. This remains an infrastructure
block rather than evidence of code compile failure.

No production `BackupCreator`, `BackupRestorer`, migrations or
Android B01–B05 changed. PR #1 remains draft; issues #2/#10/#11 open.
