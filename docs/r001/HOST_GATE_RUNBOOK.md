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

## 2026-10-15 — sixth offline gate: Yomotsu API-linked backup export adapter

Sixth configured offline suite: `backup-adapter` runs
`bash spikes/spike001/backup/yomotsu-candidate/run_tests.sh`, which compiles
the **actual committed** `PolarisYomotsuBackupExporter`,
`YomotsuMergedWorkUuidStore`, the two portable planners and the optional
protobuf DTO/builder with explicit **host-only** Yomotsu API-shaped doubles.
It requires a single exact `POLARIS_YOMOTSU_EXPORT_ADAPTER_PASS 12` marker
and exit 0; missing, repeated, incorrect or below-threshold markers fail.

**12/12 adapter JVM PASS verified** with Git-blob-identical 16 source and
host fixture files, including original latest planner and UUID code. Tests:
nonfavorite child snapshots, shared child deduplication, options forwarding,
pending links, invalid virtual root, wrong source identity, mid-export state
mutation, parent title mutation, disabled library backup and persisted UUID.

The six configured minimums are
**72 Python + 36 SQLite + 38 main Kotlin + 17 backup SQLite + 65 backup Kotlin
+ 12 Yomotsu adapter Kotlin = 240**. These are minimums, and a **complete
six-stage run was NOT executed**. The Gradle backup-lab explicitly excludes
`**/yomotsu-candidate/**` to prevent host fake classes from conflicting
with its other stubbed source sets; new candidate tests run in a separate
`kotlinc` subprocess.

**Separately staged, not production-applied:**
`spikes/spike001/backup/yomotsu-candidate/BackupCreator.staged.kt`
from exact pinned original Git blob
`98036c09002b6058a36520a82ac889fbaa9e93cb`; reproducible
`apply_backup_creator_candidate.py` and **10 configured Python staging tests**.
The pinned patched creator forwards options to the exporter, adds source
metadata for supplementary real Manga, and retains old automatic backups
until AFTER the new one has been written and validated. Validator failures
are fatal for archives with a Polaris bundle. The 10 Python source-staging
tests were **not locally executed** in this checkpoint (CI pending).

[2026-10-15 evidence ZIP](https://drive.google.com/file/d/1_L5Xw5NEcEseNVoTcccx2RIlIWyvGvhH/view)
SHA256 `9006b19e3a3c47652968554f17ae06faa4050454081421fe141bb318f8ddfe6f`.
See [new Yomotsu candidate README](../../spikes/spike001/backup/yomotsu-candidate/README.md).

**No real Gradle/Android or Kotlin protobuf round trip, SQLDelight migration,
runtime test B01–B05, restored virtual links or complete six-gate verification.**
Keep PR #1 DRAFT, issues #2/#10/#11 OPEN, migration15 untouched.

## 2026-10-15 — seventh offline gate: child-first Yomotsu restore candidate

The new `backup-restore` stage runs
`bash spikes/spike001/backup/restore-candidate/run_tests.sh`, using
the actual staged `PolarisRestoreCoordinator.kt` with explicit
host-only ports and `BackupManga`/serialization annotation doubles.
It requires **one** exact marker
`POLARIS_YOMOTSU_RESTORE_COORDINATOR_PASS 20`, count >=20 and exit 0.
The code enforces archive preflight before writes, a verified ordinary
`MangaRestorer` completion barrier, all supplemental source snapshots
restored before parent work creation, unambiguous source+URL lookup,
NULL preserved for explicitly pending links, and one call to a **required**
atomic parent/UUID ledger port (its Android implementation is pending).
A failure or inconsistency aborts before parent associations are committed.

**Locally executed:** 20/20 scenario assertions through host Kotlin/JVM.
The coordinator source matched GitHub Git blob
`89ef78974d85f7b1770ddbd0baa22e253745cf6d`.
A locally run test harness preceded a reformatted GitHub-committed test file;
the *exact published test and runner* still await CI. Never conflate the
fake atomic port with an implemented SQLDelight transaction.

Seven configured minimum thresholds:
**72 Python +36 SQLite +38 core Kotlin +17 backup SQLite +
65 backup Kotlin +12 Yomotsu export +20 child-first restore =260**.
No complete seven-stage run or Android B01–B05 was executed.

[Evidence ZIP, including source/harness provenance caveat](https://drive.google.com/file/d/1uwitwsFhcPNj3OoTvhld9YKOqaC9nL08/view),
SHA256 `46077610e28e9675dfb210fe4cedc6f69a4380dc1ace6f04ecf79402cbec88ab`.
[Restore candidate README](../../spikes/spike001/backup/restore-candidate/README.md).
CI workflow has a standalone coordinator test job step, but pending/failed
runner allocation is not evidence of passing tests.

Production `BackupRestorer.kt`, `MangaRestorer`, `merged.sq`,
migrations 14/15 and APK remain untouched. Issues #2, #10 and #11 open;
PR #1 remains draft.

## 2026-10-15 — eighth host gate: atomic SQLite source-link and UUID restore

`backup-atomic-sqlite` now runs:
```bash
python3 -m unittest discover -s spikes/spike001/backup/restore-candidate/atomic-sqlite -p 'test_*.py' -q
```
The gate requires **31** tests, exit code 0 and the Python `unittest`
`OK` marker. The same step is in `.github/workflows/domain-spikes.yml`.

Locally **31/31 PASS**, including concurrent separate SQLite database
connections, duplicate constraints, idempotent same-archive import and
rollback of both virtual parents on injected failure. GitHub source blob
hashes matched all three locally executed files. Evidence:
https://drive.google.com/file/d/1CXZnrf-uIjtURQBV3HvRL8DRW5H1M14H/view ,
SHA256 `d2c2aa1a9eb575231bfaae59cb3e09584bfaf42362cae7ac97bc0b4c1648a15a`.

**Eight configured minimums are now 291**:
72 Python + 36 merged SQLite + 38 domain Kotlin + 17 backup SQLite +
65 backup Kotlin + 12 Yomotsu export + 20 child-first restore + 31
atomic SQLite. This is NOT a single completed 291-test gate.

Reference implementation `spikes/spike001/backup/restore-candidate/atomic-sqlite`
is **Python/SQLite host-only**, not yet a compiled SQLDelight migration or
Kotlin `PolarisAtomicVirtualWorkPort`. The trial ledger and unique indexes
are NOT installed in Android; migration15, `merged.sq` and production
`BackupRestorer.kt` untouched. Review legacy duplicates and confirm
`merged://polaris/<uuid>` URL compatibility with the real reader first.

## 2026-10-15 — two new candidate SQLDelight port gates

Staged only: `spikes/spike001/backup/restore-candidate/sqldelight-port/`.
Runs in CI and `scripts/r001/run_host_gate.py`:

```bash
bash spikes/spike001/backup/restore-candidate/sqldelight-port/run_kotlin_host.sh
python3 -m unittest discover -s spikes/spike001/backup/restore-candidate/sqldelight-port/tests -p 'test_*.py' -v
```

`backup-sqldelight-port`: one unique exact
`POLARIS_SQLDELIGHT_PORT_PASS 19` marker, exit 0, minimum 19.
`backup-sqldelight-sqlite`: Python `Ran 10 tests` and `OK`,
exit 0, minimum 10. The complete **ten-stage configured minimum becomes 320**
(72+36+38+17+65+12+20+31+19+10); **320/320 is NOT an execution result**.

**Host evidence:** 19/19 compiled Kotlin candidate / mocked `Database`
and 10/10 SQLite SQL syntax, uniqueness/FK and metadata settings cases.
Both are independent suites, not Android codegen or runtime validation.
The locally executed Kotlin source and fixtures all hash-match committed
GitHub blobs. [Evidence ZIP](https://drive.google.com/file/d/1BJBwYtub_1lYH07C1h8YByAVJLn2Jgjp/view)
SHA256 `06a6aa52bfa007f1484deb61236517cfcebc41fe5b34deb1758419841d15cde1`.
The GitHub Python 10-case suite is slightly shorter than the locally
executed 10-case test file; do not equate that remote Python test invocation
with a completed local or CI run.

**No changes to production migration15, SQLDelight generated code, installed
unique indexes or real app BackupRestorer.** PR #1 remains DRAFT; issues #2,
#10, #11 remain open.

## 2026-10-15 — eleventh mandatory host gate: read-only legacy migration audit

`backup-migration-audit` requires **20** passing Python/SQLite test cases:
```bash
python3 -m unittest discover -s spikes/spike001/backup/restore-candidate/migration-audit -p 'test_*.py' -v
```
**20/20 PASS locally**, published code and tests Git blob-identical to executed sources. Source key/root/UUID collision preflight deliberately writes NO database rows, CLI opens the supplied database snapshot in `mode=ro`. The host-only eleven-stage **configured** threshold becomes **340**; the full 340 checks were not executed. [Evidence ZIP](https://drive.google.com/file/d/1_rEGkzRc1WbJRBNsODkDf8tUliGZmUzZ/view) SHA256 `76cb74f9cd7e8a6332b4d7d0fb46760d1dfcf7e9e9eb635df23233d0a678cdb6`. Before Android migration, perform a consistent database backup, review reported legacy conflicts, compile actual SQLDelight/Gradle and test on devices; migration15 remains unchanged.

## 2026-10-15 — safe in-memory migration rehearsal and report no-clobber

The mandatory `backup-migration-audit` stage now contains **40** tests
(20 legacy audit + 20 `:memory:` DDL rehearsal, report overwrite safety).
The verified candidate checks all staged UNIQUE indexes, FK/PK ledger,
SQLite integrity and row hashes without applying migrations to the
original DB. Both CLI report paths are guarded by `O_EXCL` and 0600:
cannot truncate an existing SQLite file or a report symlink.

**40/40 PASS locally** against exact GitHub blob-matched sources;
eleven-stage *configured* minimum is **360**, not an executed full
360/360. [Evidence ZIP](https://drive.google.com/file/d/1yDAhdjx4tpoItj-NfbjmfjYO7Ay70QaO/view)
SHA256 `140b2c192a2ccfbf4d9efe765148b0f0db63c8aad6f89f22e6fa40851ae7adb2`.
No actual Gradle SQLDelight generation or Android database migration.

## 2026-10-15 — conservative legacy reconciliation planner, 62 host checks

The existing `backup-migration-audit` group adds 22 regression tests
for a new **read-only** `plan_legacy_reconciliation.py`. It groups
conflicts transitively across both proposed UNIQUE keys, refuses
to choose settings for pending-vs-resolved, mismatching priorities or
synthetic virtual root, and creates no production DELETE statement.
`--simulate-exact` makes *hypothetical* exact-duplicate removals
in `:memory:` only; survivor rows and candidate DDL are checked
without touching the input SQLite copy.

Executed **22/22 new** and **62/62 complete migration-audit group** locally.
Git blob hashes verified identical for both new source/test files.
[Evidence ZIP in Polaris Drive](https://drive.google.com/file/d/1sBlgoCNOSQYCLnjDirQNJJDJLlq5OTLU/view)
SHA256 `f21374ce7373f54ab16154c9e25a69c7e1ca33a146e8226d62931ccf48145d35`.

`backup-migration-audit` threshold is **62**; combined eleven-stage
configured minimum is **382** (previous 360+22). A completed
`62/62` audit **does not imply `382/382` host**. Gradle,
Android APK, ProtoBuf serialization and actual DB migration still
unverified. Migration15 and installed DB unaffected.

## 2026-10-16 — reviewed undo-only migration simulation: 85 host checks

`migration-audit/rehearse_reviewed_reconciliation.py` adds an **explicit human-approved JSON manifest** for exact duplicate groups only, bound to the entire original `mangas`+`merged` content fingerprint and each group's SHA256. A successful SQLite clone rehearsal recreates all removed `merged` rows with original `_id` and flags and proves byte-value identity before discarding the clone. Unknown foreign keys to `merged` and table triggers force review. Pending/resolved and settings conflicts remain ineligible.

**23/23 new, 85/85 whole audit group PASS** locally on Python3.13.5 / SQLite3.46.1; two exact new Git blobs equal locally tested files. `backup-migration-audit` now requires **85** (formerly 62). **405 is the minimum configured across 11 groups, NOT an executed 405-case run**. No production DELETE or Android migration; installed migration15 intact.

[Source, tests and usage](../../spikes/spike001/backup/restore-candidate/migration-audit/README_REVIEWED_UNDO.md).
Local evidence ZIP `Polaris_R001_Reconciliacao_Reversivel_2026-10-16.zip`, SHA256 `17562de0426f9c9011222c14944824b7fda9425bfdecac46fbea7079343c56c2` (also saved under Library `/Polaris/R001/`).

## 16/10/2026 — 35 Kotlin checks using real portable model + coordinator

`sqldelight-port/run_kotlin_host.sh` compiles actual
`BackupPolarisBundle.kt`, `PolarisRestoreCoordinator.kt` and
the Kotlin atomic SQLDelight candidate together, instead of an
invented portable settings model. Only SQLDelight DB and protobuf
serialization/BackupManga are host stubs.

It executes two separate mains with unique markers:
`POLARIS_SQLDELIGHT_PORT_PASS 19` and
`POLARIS_REAL_MODEL_END_TO_END_PASS 16`. The parser requires
both suites to meet their own minima, not merely a sum.
**35/35 PASS locally.** Exact executed Kotlin blobs match GitHub.

11-stage configured minimum **421**, NOT a completed 421-test run.
Evidence ZIP SHA256 `8d5db7cee61ec6145691cf6dc00cc3c98a4a18cb062aa9d73ca9c510f9f6b287`
is in Library `/Polaris/R001/`. Actual SQLDelight generation,
ProtoBuf roundtrip and Android B01-B05 remain untested.

## 17/10/2026 — verified Yomotsu child restore barrier, 37 new Kotlin cases

Pinned `BackupRestorer.restoreManga()` catches failed individual manga
restorations without throwing; domain `GetChaptersByMangaId.await()`
also swallows errors. The staged `yomotsu-source-port/` adapter invokes
the real `MangaRestorer.restore()` signature directly and then checks
every required backed-up chapter via typed SQLDelight query (without
the error-catching domain interactor).

`PolarisYomotsuStrictRestoreSequence` preflights the real portable
bundle and coordinator, then strictly retries only the ordinary manga
needed by resolved Polaris links AFTER stock jobs complete, before
committing any virtual parents. Supplemental children are restored
strictly and verified. Exceptions block virtual parent association.

```bash
bash spikes/spike001/backup/restore-candidate/yomotsu-source-port/run_tests.sh
```

**23/23 +14/14 =37/37 Kotlin/JVM PASS**, also rerun under the actual
repository directory layout. Two independent exact success markers
are required; stage `backup-yomotsu-children` minimum 37 raises
twelve-stage *configured* threshold to **458**, NOT a completed full
458-suite execution. Sources and GitHub blobs exactly match local
compiled files. [Evidence ZIP](https://drive.google.com/file/d/1PjToUKEOZMSG8RN5bPvbtw2gM3iKcXpj/view),
SHA256 `3e6448ae34fa4146c7db5676368fc5d279e37e9276c991852056583a4a4aa963`.

**Not Android:** `MangaRestorer`, DB/generated SQLDelight queries and
serialization are stubbed in host tests; actual codegen, real ProtoBuf,
full history/tracking verification and Android runtime B01–B05 remain
unverified. Production `BackupRestorer.kt` and migration15 unchanged.

## 17/10/2026 — stage optional ProtoBuf 107 and fail-closed stock restore lifecycle

New `yomotsu-source-port/kotlin/PolarisBackupRestorerLifecycle.kt` preflights the real portable bundle before stock Yomotsu DB jobs, awaits one structured stock restore operation and then enforces strict required-child source checks before virtual-parent associations. It leaves legacy backups on the one-pass stock path.

SHA-pinned **non-production** `android-bridge/Backup.staged.kt` adds optional `polarisBundle` ProtoBuf field 107; `BackupRestorer.staged.kt` wraps the upstream structured `coroutineScope` in a suspend callback. If a Polaris segment is present but the lifecycle has not been DI-injected, it **fails explicitly**. Neither staged file is in the Android source set or compiled with Gradle.

`backup-yomotsu-children` now runs three mains and checks independent exact markers, with minima 23 source +14 sequence +16 new lifecycle = **53**. Local **53/53 Kotlin/JVM PASS**, same source blobs published to GitHub; runner's third main is `HostLifecycleTestKt`. Overall **12 host groups configured minimum 474**, NOT a completed 474-case run. New package `Polaris_R001_BackupRestorer_Lifecycle_2026-10-17.zip` SHA256 `b83c850a65dfdf44e1d9375a256d68fc18dd0315abaa4533bfd5a2e92db35f11`, saved in Library `/Polaris/R001/`. Remote Drive upload of this ZIP did not succeed; use the verified sandbox ZIP link.

Production gate unchanged: SQLDelight codegen and DI, real ProtoBuf encode/decode, Android B01–B05, tracks/history verification, migration15 review. PR #1 remains DRAFT.

## 2026-10-17 — UUID-ledger replay must revalidate real-child identity

A **confirmed** bug allowed `SqlDelightPolarisAtomicVirtualWorkPort` to
reuse an existing UUID ledger while the linked real `mangas._id`
now had a changed source ID or URL. The old implementation skipped the
exact source+URL lookup on ledger hits. A new negative regression failed
on the previous Kotlin code. The fix runs the exact-key query in the
transaction BEFORE both new and existing ledger paths.

Six Kotlin regressions check URL drift, source drift, deleted or ambiguous
rows, pending-NULL preservation, and rollback of a newly created FIRST
parent if the SECOND old UUID has an invalid real source identity.
Another six tests run the query and FK semantics on **actual SQLite**
rather than the fake Kotlin database.

**25/25 Kotlin adapter + 16/16 real portable-model integration = 41/41
Kotlin host PASS**, and **16/16 SQLite host PASS**. That is 57
separately executed host cases, NOT an Android acceptance test.
New Git blobs for Kotlin adapter, Kotlin tests and SQLite test:
`09edf277b9060ce0e0df5b9b7dcf0d4810a29ccc`,
`563f04df2aa45b1f901e9d8b216eea62c5b9f7a2`,
`7c31425d186f70aec285971eb4253c6cef39ddf2`.

Gate minima: `backup-sqldelight-port` = 41 and
`backup-sqldelight-sqlite` = 16. Combined 12-stage configured
minimum **486**, NOT executed in full. Evidence
`Polaris_R001_Replay_Identidade_Real_2026-10-17.zip`
SHA256 `45ad1d62d8d0f69fa1deb2da6921890c290a36f11c6a9cd5b7935202ae141cf7`.
No production schema, migration 15 or user DB changes.

## 2026-10-17 — backup field 107, pending-only and duplicate parent fail-closed

Three concrete staging errors corrected: `BackupCreator.staged.kt` wrote
`Backup.polaris` while `Backup.staged.kt` defined `polarisBundle`
and `BackupRestorer.staged.kt` read `backup.polarisBundle`. Both now
use the same `polaris` property as the existing 107-tag patcher.
`BackupPolarisBundle` now forbids supplemental full-manga snapshots
if ALL associated source links are pending. A shared source remains
eligible when at least one parent has a resolved link.

Critically, `BackupPolarisBundle.validateSnapshotCoverage` fails closed
when an archive contains both actual Polaris virtual works and ordinary
Yomotsu backup mangas with `source=6969`, which would otherwise
create two different virtual parent rows on import. This is a P0
incompatibility with the current staged exporter: **do not bypass**.
Complete portable parent metadata preservation and duplicate-free
restoration before enabling Android export/import.

New `backup-proto-contract` host gate compiles the staged
`Backup.staged.kt`, real portable DTO and requires four unique
success markers with minima 18+19+9+5 = **51**. It runs via
`bash spikes/spike001/backup/proto-candidate/run_model_validation.sh`.
CI also checks the six cross-file field-107 contracts in Python.

Locally executed **32/32** DTO/staged field tests, **53/53** strict
restore, **41/41** atomic port and **16/16** SQLite = 142 distinct
host test cases across four suites, plus **7/7** pinned proto staging
Python cases; all PASS. The builder's 19 tests are configured but
not rerun here. The 13-stage **configured** host minimum is
**537**, not an executed full gate. No actual ProtoBuf or Android
Gradle SQLDelight codegen.

[Evidence ZIP](https://drive.google.com/file/d/164HHr-yLvfW9Br24WNISJyDDQsULA4Bj/view):
SHA256 `2d525668bca17556211bc8d6cc554add4b10d3d405bc49f12133bd44d6a53c09`.
No production migrations or file writes to a user's Android data.

## 17 October 2026 — lossless virtual-parent snapshot partition (23 new tests)

The staged Yomotsu full `BackupManga` already contains notes, categories,
chapters, history, tracking, viewer flags, memo and user metadata.
`spikes/spike001/backup/parent-candidate/` has a standalone **full snapshot**
partition plan: bind original selected local manga ID and canonical parent
UUID; separate source-6969 parent payloads from stock ordinary backups
WITHOUT dropping any field; keep original list indices to prove reversibility.
It refuses orphan/mismatching parents, changed titles/URLs and duplicate UUIDs.
`bash spikes/spike001/backup/parent-candidate/run_tests.sh` ran
**23/23 Kotlin/JVM host cases PASS** with BackupManga/ProtoBuf host doubles.
Source code was checked against pinned BackupManga's source/url/title field
names but not compiled against real Android dependencies.

`backup-parent-split` is now the 14th fail-closed gate, minimum 23.
Aggregate **configured** 560 cases across 14 groups, not executed 560/560.
[GitHub candidate](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation/spikes/spike001/backup/parent-candidate).
[Drive ZIP](https://drive.google.com/file/d/1Qj-6J0Ie0Be2CVFfhuBt44N5kCdTi5kb/view),
SHA256 `411e5d91333a58386074b4ee11d8044531157ec74bbd0c8c217cf779a563f6af`.

Critical P0 remains: add a versioned archive payload for full parent
snapshots, real ProtoBuf roundtrip, ensure stock path excludes virtual
manga, restore full metadata onto exactly one UUID parent ID inside
reviewed DB operations, safely merge memo JSON and map categories/history.
Keep the preflight guard that refuses duplicate virtual parents.
Migration 15 and production source files untouched.


## 19/10/2026 — portable parent-v2 contract

`BackupPolarisBundle` extends v1 with additive Proto tag 4
`parentSnapshots` (full `BackupManga` + UUID + original ordinal).
`PolarisParentBundleAssembler` matches the full partition to portable works.
`PolarisRestoreCoordinator.preflight` refuses v2 **before stock writes**
until an atomic full-parent metadata restore exists. Keep this fail-closed barrier.

New standalone 26/26 Kotlin/JVM suite, total 74/74 across locally available
model suites (16-case old Builder fixture, rather than the 19-case latest).
Host `backup-proto-contract` now REQUIRES 77 via five independent unique
markers (18+19+9+5+26); total configured **586/14 groups, not executed**.
[Evidence ZIP](https://drive.google.com/file/d/12EPjHFr695yWWRKOO50PvI3EXPPD4vyk/view),
SHA256 `c6d09c031f2738239cb288a637f2b0cf9595709f1e009177aa812b85cfee6d13`.
Real serialization/codegen/Android B01–B05 remain open. See
[technical report](PARENT_V2_PORTABLE_2026_10_19.md).


## 2026-10-19 — v2 parent metadata restore preflight (host staging)

Added `PolarisParentMetadataRestorePlanner` in `spikes/spike001/backup/parent-candidate/`.
It carries each FULL original `BackupManga` into a UUID-bound restore command,
requires category ID mapping (archive category -> destination category, obtained by
name from the archive's category restoration phase), and fails closed for local
metadata conflicts, ambiguous UUID lookups, reused destination IDs, cross-source
identity, unknown source URL and missing child snapshots. Replays are a no-op ONLY
when an Android adapter independently proves a byte/field-complete identical state.
The candidate deliberately does NOT write metadata, and is NOT proof of an
atomic SQLDelight transaction or authorization to remove the v2 import guard.

25/25 **NEW** standalone Kotlin/JVM assertions passed locally with representative
BackupManga/DTO/annotation doubles. Source and log are in the Polaris Library:
`/Polaris/R001/parent-metadata-restore/` (ZIP SHA256
`aec1c270d8f63e3a96b25c88ae99ff7f11cbdc4eb906cfe7d76bcdb8cfa0ecf3`).
The exact committed runner against the *real staged DTO* and CI are pending.

The 15th fail-closed offline gate is `backup-parent-metadata-plan`:
`bash spikes/spike001/backup/parent-candidate/run_restore_plan_tests.sh`.
Its minimum is 25 unique cases with exact success marker; both Domain spikes
workflow and gate parser/self-test were updated. **15 configured groups /
611 required cases; NOT executed together, NOT Android validation.**
See [candidate report](PARENT_V2_METADATA_RESTORE_PLAN_2026_10_19.md).
Mandatory blockers remain: transactional UUID-indexed metadata applier and
verified conflict handling, actual Kotlin ProtoBuf encode/decode, SQLDelight
code generation/bundled driver, Android B01-B05. PR #1 Draft, issue #11 open,
no migration15 or production Yomotsu modifications.


## 2026-10-19 — destination UUID URL regression (supersedes earlier 25-case threshold)

The staging v2 parent metadata planner originally compared the destination
virtual parent's `mangas.url` to the **archived source-6969 URL**. But the
staged SQLDelight restore port creates the destination at
`merged://polaris/<canonicalUuid>`, independent of the origin device's URL.
A reused UUID parent could therefore be wrongly rejected. Corrected the
staging-only planner to preserve the original full `BackupManga` while
explicitly carrying `destinationUrl=merged://polaris/<canonicalUuid>` and
requiring exact stable URLs for existing ledger parents. Legacy untracked
parents must still fail closed rather than title-matching.

**Local 28/28 Kotlin/JVM tests PASS**, including 3 new regression cases,
with representative model doubles (not real Android ProtoBuf/SQLDelight).
The new tests did not compile against the pre-fix model because the required
`destinationUrl` contract was absent. Evidence ZIP SHA256:
`bd07f88ea8b82ff48829ac04fee2300f33098c473ae1152060a52759e3660d11`,
Library `/Polaris/R001/parent-metadata-restore/`.

The fifteenth `backup-parent-metadata-plan` gate now requires **28 cases**.
**Configured minimum: 614 tests in 15 gates; no aggregate run.**
No production Yomotsu, migration15, UUID ledger or v2 coordinator preflight
was modified. [Detailed report](PARENT_V2_UUID_DESTINATION_URL_FIX_2026_10_19.md).
Android B01–B05 and real transactions/serialization remain P0 blockers.
