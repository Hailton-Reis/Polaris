# Polaris R001 — Full-parent relational write (2026-10-19)

**HOST REFERENCE ONLY. DO NOT WIRE INTO THE ANDROID RESTORE COORDINATOR.**
The shipped `PolarisRestoreCoordinator` must continue to reject backup v2 before stock writes. Issue #11 and Draft PR #1 remain open, migrations 14/15 remain untouched.

This work advances beyond separately testing Kotlin projections and SQLite statements: `ProjectionSqlBridgeFixture.kt` invokes the **actual staged** `PolarisBackupMangaSqlProjection.prepare` Kotlin code (compiled with pinned-shape host DTO/memo test doubles), exports its typed rows to JSON, and `test_kotlin_projection_sql_bridge.py` feeds those rows through the actual staged Yomotsu-column SQL statements and the existing Spike-001 `merged.sq` insert. The SQLite test proves complete roundtrip, UUID ledger, chapter/history/track/category/exclusion/link persistence, nested JSON memo preservation in SQLite and FK integrity.

`physical_parent_writer.py` is an independent Python **reference implementation**, not the intended Android code. It accepts `Batch` with Kotlin row names, reserves new parent `_id` under a `BEGIN IMMEDIATE` writer lock, invokes `PRAGMA defer_foreign_keys=ON`, confirms existing UUID/URL/source identities, writes child relations first, inserts complete parent **LAST** (already `is_syncing=0`), then reads all physical tables and verifies strict equality **before committing**. Failure at any point — including when the second parent fails — rolls back all parents. It will **not** update an existing parent or silently retry, infer titles, or replace local edits. The bridge verifies Kotlin-prepared reserved ID and chapter `parentId` against the actual reserved ID, rejecting any mismatch.

Original staged SQL and schema files are dependencies from the same repo branch:
- `../parent-sqldelight-fields/PolarisParentMetadataRestore.sq`
- `../../../new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq`
- `../../../new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm`
- `../atomic-sqlite/atomic_parent_restore_candidate.sql` (migration candidate, **not installed**)
- `../parent-field-projection/PolarisBackupMangaSqlProjection.kt` plus host test doubles
- `../pinned-schema-bridge/pinned_schema_fixture.py` and `../parent-sqldelight-fields/pinned_update_triggers.sql` (disposable Yomotsu-shaped host schema, not real Android generated schema)

## Run

From a complete Polaris branch checkout:

```bash
bash spikes/spike001/backup/restore-candidate/parent-relational-port/run_tests.sh
```

Requires `kotlinc`, `java`, `python3`, no Android SDK. The runner compiles the Kotlin projector with small host stubs into a **temporary** JAR, serializes the result, then runs **69 Python/SQLite tests** against in-memory DBs. It deletes its temporary JSON/JAR. Source/test code never opens a user's `tachiyomi.db`.

**69/69 host checks PASSED locally**, including an actual Kotlin-prepared DTO passed into the Python SQL writer. This is not a 69-test Android suite. Kotlin memo test stubs support basic string-only objects; nested JSON object preservation is separately exercised inside real SQLite with fixture payloads, NOT with real Yomotsu serialization. Generated Kotlin SQLDelight APIs, real Android driver, real ProtoBuf, complete source UI/reader and empty existing parent reuse remain untested.

## Hard production blockers

1. Implement this exact new-parent-only algorithm as Kotlin `PolarisFreshParentStages` using the **generated** SQLDelight 2.3.2 query interfaces, actual bundled Android SQLite, and source metadata model. This host Python writer must **never** be deployed as the Android backing store.
2. Verify real `BackupManga` and nested memo encode/decode, `StringListColumnAdapter` and Float representation, full physical readback against actual schema/triggers and crash/cancellation rollback.
3. Verify the legitimate prior migration for `polaris_restore_ledger` + unique indexes after safely auditing preexisting data. Do not apply a second `merged` table or prematurely change `15.sqm`.
4. Cover existing EMPTY parent and IDENTICAL replay separately; current writer intentionally refuses both rather than silently replacing edited data.
5. Resolve GitHub Actions failures occurring **before any step**, run Android B01–B05 using two real source extensions, then consider removing v2 fail-closed guard.


## 2026-10-20 — dynamic transaction-reserved parent ID and mandatory Kotlin bridge evidence

The previous Kotlin→SQLite bridge used a fixed test parent ID (`103`). It now
accepts the physical ID selected **inside** `BEGIN IMMEDIATE` by the staged
SQLDelight query `selectPolarisNextFreshParentId` (selecting `MAX(_id)+1`). The
local test launcher generates Kotlin parent payloads for IDs `103` and `203`,
and runs another dynamically generated payload for `204` from the same compiled
JAR. It checks mismatched ID rejection, no changes to existing real manga rows,
failed write rollback, and explicit rejection of invalid/multiple CLI arguments.

Important additional safety fix: `test_kotlin_projection_sql_bridge.py` now
**fails**, rather than reporting a Python unittest SKIP, if the compiled Kotlin
projection fixture is missing. The enclosing R001 host gate must also require
exactly ONE `POLARIS_KOTLIN_SQL_BRIDGE_PASS` marker in addition to `Ran 83 tests`
and `OK`. This prevents a fake 83/83 pass if the Kotlin→SQL bridge never ran.

**83/83 test cases PASS locally**, 14 new since the prior 69-case runner. The
same staged SQLDelight query text is used by the Python SQLite writer. This
proves source-level binding logic and host transaction behavior, **not** actual
SQLDelight generated Kotlin or Android driver runtime.

The production implementation still requires reserving the ID and computing
the real BackupManga projection on the *same* writer transaction/connection;
SQLDelight codegen, Android instrumentation and real ProtoBuf remain open.
No production migration, app install, or v2 import enablement here.
