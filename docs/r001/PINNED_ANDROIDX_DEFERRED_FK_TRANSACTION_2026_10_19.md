# Polaris R001 — pinned AndroidX SQLDelight transaction guard

**19 October 2026 — STAGING ONLY.** Issue #2 + issue #11, Draft PR #1.
**No Android build, real-driver run, or production DB mutation in this round.**

## Actual pinned driver (not a generic assumption)

Yomotsu fixed commit `0fb80c439ef816eeb50674f1b90af39918b176d8`, with:
- `gradle/libs.versions.toml`: SQLDelight **2.3.2**, Mihon fork of `com.github.mihon.sqldelight-androidx-driver` at revision **`0637a964a1`**.
- `data/build.gradle.kts`: `generateAsync.set(true)`.
- `app/src/main/java/eu/kanade/tachiyomi/di/AppModule.kt`: `AndroidxSqliteDriver(driver = BundledSQLiteDriver(), ... isForeignKeyConstraintsEnabled = true)`.

I retrieved and inspected the pinned driver's **exact** original code at `mihon/sqldelight-androidx-driver` revision `0637a964a1`:
- `AndroidxSqliteExecutingDriver.kt`, blob SHA `3bdfecd513592580acde3ec94e5fd1da80af7df4`: the outer Transaction runs `BEGIN IMMEDIATE`; `TransactionElement` occupies the coroutine context; `withConnection` routes statements to `ConnectionHolder.connection` inside the active transaction; `COMMIT` / `ROLLBACK` end it.
- `ConnectionPool.kt`, blob `8377aed614f9adb556918bb6604cce5af25bb6e9`: writer connection acquisition and transaction-aware dispatch.
- `AndroidxSqliteUtils.kt`, blob `08fcacc70c2854dc673e7413547365fb77085dcb`: `PRAGMA defer_foreign_keys` does NOT take the special journal-mode / foreign-keys / synchronous route, so it is executed normally within the transaction.
- `AndroidxSqliteDriver.kt`, blob `686bcf336ce572e7af2705ba80c88e6aa3dd10c1`: `execute` and `executeQuery` delegate to executing driver.

Original pinned driver: https://github.com/mihon/sqldelight-androidx-driver/tree/0637a964a1

These observations resolve the **source-code-level compatibility question** (writer connection and transaction semantics) for this pinned driver. They are NOT a runtime proof for `PRAGMA defer_foreign_keys` with the bundled Android SQLite binary, or Kotlin codegen compatibility.

## Implemented Kotlin candidate

`spikes/spike001/backup/restore-candidate/pinned-driver-transaction/PolarisDeferredFkTransaction.kt` imports the pinned app API types `tachiyomi.data.Database`, `SqlDriver` and `QueryResult`.

It wraps `database.transactionWithResult`; checks `PRAGMA foreign_keys=1`, activates and reads back `PRAGMA defer_foreign_keys=1`, then strictly orders NEW-parent phases through `PolarisFreshParentStages<T>`: reserve unused ID, stage all references, INSERT complete parent LAST, verify persisted complete metadata. It refuses duplicate or nonpositive parent IDs. It then rechecks both PRAGMAs (to detect missing transaction context), checks `PRAGMA foreign_key_check` for any row, and relies on SQLDelight's commit/rollback. All PRAGMA SQL strings are constant, and diagnostic codes do not leak manga metadata.

This is **not** the full concrete `PolarisFullParentAtomicTransactionPort`: callers still must implement complete field mapping and readback in the generated SQLDelight database; existing-EMPTY placeholder reuse and repeat imports must remain fail-closed. The helper must not be used on a live DB until reviewed and compiled with the actual pinned SQLDelight/Android dependencies.

## Local reproducible tests

The Kotlin guard is compiled with **small fake SQLDelight Database, SqlDriver, QueryResult and SqlCursor host test doubles**, and not the actual driver classes. The test double checks the protocol and deliberately injects:
- Foreign keys disabled or unqueryable.
- Driver refusing the PRAGMA, lost connection context, unresolved FKs.
- Failure in the second parent's physical readback.
- Reserved ID collision, missing data and commit failure.
- Correct ordering: ID reservation → dependent writes → INSERT parent → readback.

**33/33 Kotlin/JVM host protocol tests PASS.** On the same self-contained evidence tree the previous **51/51** Yomotsu-column SQLite tests and **98/98** migration14/UUID readiness SQLite tests PASS. **182 locally executed host checks**, three distinct suites; **zero real SQLDelight driver/Android runtime tests** in this round.

Evidence package: `/Polaris/R001/pinned-driver-transaction/Polaris_R001_Pinned_Driver_Transaction_2026-10-19.zip`, SHA-256 `e0ae1d69455391ef5a66e7f412b31bb90f237bcdb3b4dfd8231baaca4abd9c31`. It contains a minimal staged source tree to reproduce the two SQLite suites without missing dependencies, the Kotlin stubs and the `run_all_evidence.sh` script.

Added **`backup-pinned-driver-kotlin`** (33 required) to `scripts/r001/run_host_gate.py` and `.github/workflows/domain-spikes.yml`. New aggregate **931 minimum configured cases across 21 groups**, **NOT** an executed 931-test aggregate, and GitHub CI success not confirmed.

## Hard blockers

1. Implement the *actual* `PolarisFreshParentStages<...>` against generated asynchronous SQLDelight queries using the **real pinned driver**, reserving IDs under the writer lock, checking source+URL real child collisions, categories, all BackupManga metadata, memo, chapters/history/tracking and legacy UUID state.
2. Compile the helper and queries inside a clean pinned Yomotsu/Spike-001 Android build. Verify same-connection `PRAGMA defer_foreign_keys` at runtime, plus COMMIT rollback on FK failure and cancellation.
3. Retain the **separate existing-empty / identical replay** policy (no write that would trigger timestamp drift), real protobuf v1/v2, B01–B05, real extension selection, UI/reader tests.
4. Resolve GitHub Actions jobs failing with **zero executed steps** without misattributing them to app Kotlin compilation.

**Keep `PolarisRestoreCoordinator.preflight` v2 refusal. Migration14/15 untouched; no user DB modified. PR #1 Draft, issues #2/#11 open.**
