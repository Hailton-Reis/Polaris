# Polaris R001 — pinned SQLDelight transaction, verified API candidate (19 Oct 2026)

**STAGING ONLY — not integrated, not compiled with real SQLDelight, not tested on Android.**

The Yomotsu pin `0fb80c439ef816eeb50674f1b90af39918b176d8` uses:
- `data/build.gradle.kts`: `generateAsync.set(true)`, SQLDelight `2.3.2`.
- `app/src/main/java/eu/kanade/tachiyomi/di/AppModule.kt`: a `BundledSQLiteDriver` wrapped in `com.eygraber.sqldelight.androidx.driver.AndroidxSqliteDriver`; foreign keys enabled.
- Gradle `sqldelight-androidx-driver = 0637a964a1`, artifact `com.github.mihon.sqldelight-androidx-driver` (a PINNED fork, not today's latest release).

Verified live upstream driver sources in repo `mihon/sqldelight-androidx-driver` at revision `0637a964a1`, their Git blobs:
- `AndroidxSqliteExecutingDriver.kt`: `3bdfecd513592580acde3ec94e5fd1da80af7df4` — `TransactionElement` is coroutine-context-bound, `withConnection()` reuses `ConnectionHolder.connection` inside the transaction, the outer `Transaction` executes `BEGIN IMMEDIATE` and ends with `COMMIT` or `ROLLBACK`.
- `ConnectionPool.kt`: `8377aed614f9adb556918bb6604cce5af25bb6e9` — writer pool and in-transaction dispatch.
- `AndroidxSqliteUtils.kt`: `08fcacc70c2854dc673e7413547365fb77085dcb` — `PRAGMA defer_foreign_keys` is not a `journal_mode`, `foreign_keys` or `synchronous` special-case, so it follows the ordinary in-transaction writer route.
- `AndroidxSqliteDriver.kt`: `686bcf336ce572e7af2705ba80c88e6aa3dd10c1` — delegates `execute` and `executeQuery` to the executing driver.

## New Kotlin staging guard

`PolarisDeferredFkTransaction.kt` references the ACTUAL Yomotsu imports:
`tachiyomi.data.Database`, `app.cash.sqldelight.db.SqlDriver`, and
`app.cash.sqldelight.db.QueryResult`. In a `database.transactionWithResult` block:

1. Check that `PRAGMA foreign_keys` returns `1`.
2. Execute `PRAGMA defer_foreign_keys=ON`, query that it returns `1`.
3. Enforce new-parent stage order through `PolarisFreshParentStages<T>`: `reserveUnusedParentId`, `stageAllDependencies`, `insertFullParentLast`, `assertExactStoredParent`; reject invalid/repeated IDs.
4. Check the same PRAGMAs again; refuse if the execution context has changed.
5. Query `PRAGMA foreign_key_check`; abort if any violation, otherwise SQLDelight commits. Exceptions cause a rollback. No user metadata is embedded in PRAGMA strings or diagnostic codes.

The new guard does **not** yet implement the field-complete SQLDelight queries; it defines a safe sequencing boundary that a future real `PolarisFullParentAtomicTransactionPort` must adapt. It is for **new** parents only; existing empty-parent reuse/replay needs separate policy. In the pinned driver, a nested transaction is not equivalent to an independent top-level writer scope, so a real integration should prohibit nested caller transactions or positively test same-connection and commit semantics before enabling restore.

`SqlDelightHostStubs.kt` and `DatabaseHostStub.kt` exist ONLY to compile/run the guard on host Kotlin/JVM. They are NOT part of the Android patch and do NOT prove actual SQLDelight binary compatibility. The fake driver tests transaction state and simulates failures; real driver, compiled queries, true Protobuf and Android B01–B05 remain untested.

## Verified tests

```sh
bash spikes/spike001/backup/restore-candidate/pinned-driver-transaction/run_tests.sh
```

- **33/33 Kotlin/JVM simulated transaction protocol PASS**.
- Independently reran existing staging host suites: **51/51** Yomotsu-column-shaped field/deferred-FK SQLite checks and **98/98** migration14/UUID-readiness SQLite checks. **182/182 separately compiled/executed local host checks** over 3 suites, not one real Android integration test.
- The source-shaped SQL fixture strips original SQLDelight adapter types; FK tests still do not prove actual bundled Android native driver.

**Safety boundary:** Leave `PolarisRestoreCoordinator.preflight` v2 rejection, issue #11 OPEN, issue #2 OPEN, PR #1 Draft, migration14/15 unchanged. Don't use this as a restoration implementation until real same-driver SQLDelight codegen, actual actor connection and full physical readback pass.
