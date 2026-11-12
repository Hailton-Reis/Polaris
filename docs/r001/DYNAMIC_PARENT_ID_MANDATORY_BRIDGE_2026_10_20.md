# Polaris R001 — dynamic reserved parent ID + fail-closed Kotlin-to-SQL bridge

2026-10-20 — **host-only staging**. Draft PR #1, issue #11, pinned Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`.

## Concrete defects closed in the staging prototype

The earlier `ProjectionSqlBridgeFixture.kt` prepared `PolarisBackupMangaSqlProjection` with a **fixed parent ID 103**, while the SQLite transactional writer allocated its real ID using `MAX(mangas._id)+1`. This concealed parent-ID mismatches in the main happy-path test. A parent must instead be projected with the exact ID reserved **inside its write transaction**.

The existing Python bridge test also performed `skipTest` when the Kotlin fixture was absent. Unittest still prints `OK (skipped=1)` and the old R001 gate counted the `Ran 69 tests` line without requiring that Kotlin-to-SQL bridge itself ran. This was a **false-green test coverage risk**.

## Implemented and published

1. Added a named SQLDelight candidate query `selectPolarisNextFreshParentId` using `SELECT COALESCE(MAX(_id),0)+1` to `spikes/spike001/backup/restore-candidate/parent-sqldelight-fields/PolarisParentMetadataRestore.sq`. **Call only inside** `BEGIN IMMEDIATE` / SQLDelight writer transaction; querying outside is unsafe. The SQLite reference writer now invokes this same staged query instead of repeating its SQL.
2. Kotlin test fixture `ProjectionSqlBridgeFixture.kt` takes a validated parent ID at invocation and projects both the parent and chapter rows with that ID. It rejects malformed, zero and extra arguments rather than silently accepting a default.
3. Runner compiles the actual staged Kotlin field projection with test DTO/JSON doubles, generates IDs 103 and 203, then an extra on-demand 204; tests verify the persisted ID, preservation of other local manga rows, FK integrity and collision rollback.
4. The Python bridge test now **fails**, instead of skipping, when the Kotlin-generated fixture is absent. A success case emits `POLARIS_KOTLIN_SQL_BRIDGE_PASS`.
5. `scripts/r001/run_host_gate.py` now requires BOTH `Ran 83 tests ... OK` AND exactly one `POLARIS_KOTLIN_SQL_BRIDGE_PASS` line and refuses `skipped=` summaries. Parser tests reject missing, repeated and skipped bridge results.

## Real execution evidence

- **83/83 local host integration cases PASS**, 14 more than the earlier 69 cases.
- The **self-contained ZIP was extracted in a fresh directory**, and its `run_tests.sh` compiled Kotlin and ran the complete suite successfully a second time: **83/83 PASS, unique bridge marker, no skips**.
- Source and proof ZIP SHA256: `e8cc8b8740034940557889a86f5194487c7ea137241982a43a77f4dd8249aac3`. Library: `/Polaris/R001/dynamic-parent-id-hardening/`.
- R001 host aggregator configured minimum rises **1,089 → 1,103 cases across 23 groups**. These 1,103 tests were **NOT executed together or on Android**.

## Safety boundary

The prototype's relational writer is still Python/SQLite disposable, and Kotlin compiles against the host field/JSON doubles, not actual Yomotsu SDK/ProtoBuf/SQLDelight-generated classes. This source-level reservation candidate is **not yet the real Kotlin SQLDelight database adapter**. The Android build cannot be completed in the current offline container (no Gradle distribution or Android SDK/dependency caches and Maven DNS is unavailable). The same-transaction production Kotlin projection must be implemented on pinned SQLDelight 2.3.2 and instrumented before enabling v2. Existing-parent/replay remains a separate blocked path.

**No change to migration14, migration15, production user DB or `PolarisRestoreCoordinator.preflight` fail-closed v2 rejection. Keep Draft PR #1 and issues #2/#11 open.**
