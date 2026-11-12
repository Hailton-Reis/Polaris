# Polaris R001 — generated-query fresh-parent Kotlin adapter candidate (2026-10-20)

**Candidate only; v2 backup restore remains disabled.** This commit adds a substantial Kotlin adapter, not a new production migration.

## Implemented
The new `spikes/spike001/backup/restore-candidate/generated-adapter/SqlDelightPolarisFreshParentAdapter.kt` references the *named* SQLDelight query facades of the existing staged `PolarisParentMetadataRestore.sq`, `merged.sq` and proposed UUID ledger. It uses `PolarisDeferredFkTransaction` under the pinned Mihon SQLDelight AndroidX driver contract, reserves a parent ID from `selectPolarisNextFreshParentId` **inside** the transaction, prepares the exact `BackupManga` field projection for that ID, validates physical source/URL identities, writes full chapters with returned IDs and exact history, categories, tracker data, scanlator exclusions, merged root/real/pending edges and UUID ledger. It INSERTs the full physical parent row **LAST**, and verifies every column of mangas and chapters and all related rows before the transaction returns; an exception must roll back the whole batch.

It refuses existing parents (including byte-identical replays), duplicate UUID/source identities, stale/pending conflicts, invalid root priority/metadata flags, untracked legacy memo UUID claims and missing/changed physical fields. No title-based auto-relink.

## Executed evidence
- **28/28 Kotlin/JVM host behavior tests PASS**, compiling the **actual new Kotlin adapter** against explicit fake generated query, driver, model and JSON classes. Includes staged chapter/history linkage, category/tracker/exclusion, resolved/pending edges, same-transaction rollback when second parent fails, and altered stored title, track, history, category or edge detection.
- **22/22 Python source/SQL contract tests PASS**, comparing actual named arguments and persistent column coverage with staged Yomotsu SQLDelight schema, query order and readback.
- **50/50 combined host adapter checks PASS**, unique `POLARIS_GENERATED_QUERY_BRIDGE_PASS 50` marker, no skipped checks.
- Separately reexecuted **68/68 Python SQLite parent relational reference tests PASS**. Total this turn **118 host checks across two adapter suites and the earlier SQLite reference suite**, not 118 Android tests.
- Added 24th gate `backup-generated-query-adapter` min 50. Aggregate **1,153 configured minimum cases in 24 groups**, NOT a verified aggregate or GitHub CI PASS.

Evidence ZIP SHA256 `2c0526b02d665fbb25a054a0e8e029358e433e82b22f162e387b3531d2907408`, Library folder `/Polaris/R001/generated-query-adapter/`.

## Not yet proven
This Kotlin adapter was compiled with **API-shape host doubles**, not the real *generated* SQLDelight 2.3.2 classes or Android SDK. Real SQLDelight may expose different nullable return/adapter types. The staged .sq files are not deployed to the data module; physical UUID-ledger migration has not been approved. The external archive digest is checked for SHA256 hex *format*, not recalculated here. Real source-child importer and category order→name→local-id resolution, full ProtoBuf/memo roundtrip, Android B01–B05 and safe existing-parent/identical-replay rules remain P0.

Keep migration14 and migration15 untouched, PR #1 DRAFT, issues #2/#11 OPEN and `PolarisRestoreCoordinator.preflight` v2 **fail-closed**. No user's SQLite database modified.
