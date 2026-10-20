# Polaris R001 — new-parent generated-query adapter candidate

**Staging only. Do not wire into production backup v2.**

`SqlDelightPolarisFreshParentAdapter.kt` is the first Kotlin candidate that
binds the staged `PolarisBackupMangaSqlProjection` to explicit named query
APIs for `PolarisParentMetadataRestore.sq`, the existing Spike-001 `merged.sq`
and UUID ledger, inside `PolarisDeferredFkTransaction`.

For NEW parents only, it reserves a parent ID inside the writer transaction,
checks resolved/pending children, creates categories, full chapters and exact
history using actual chapter IDs, tracking, scanlator exclusions, all merged
edges and ledger. It INSERTs the complete parent LAST and compares EVERY
persistent physical manga/chapter column plus all relations/ledger before the
transaction may commit. Any discrepancy must abort all parents. Old or
identical parents are always rejected; no user-row overwrite.

`bash run_host_contract.sh` runs **26 source/SQL binding and coverage tests**,
plus **38 Kotlin/JVM behavioral tests**, compiling this exact candidate Kotlin
file against explicitly named **API-shape test doubles** for Database,
generated queries, `SqlDriver`, BackupManga and JSON. This is **NOT**
real SQLDelight-generated code or an Android build. Readback types, driver
behavior and real ProtoBuf still require an Android integration run.

Remaining P0: stage original query files in actual `data` module, install a
reviewed UUID ledger migration, test the exact SQLDelight 2.3.2 generated
methods and Kotlin argument types, calculate archive digest instead of merely
checking supplied digest syntax, resolve archive category order->name->local ID,
verify real memo and serialized ProtoBuf, and Android B01–B05. Neither
migration14/15 nor preflight refusal is changed. Draft PR #1, issues #2/#11
remain open.

## 2026-10-20: fail-closed archived category identities

New `FreshWork.archiveCategories` contains the original backup-wide `BackupCategory`
snapshots for every `BackupManga.categories` order. The Android integrator MUST pass
this list from the **same decoded backup**, never infer category names from local IDs.
Before inserting any rows, `validateArchiveCategories` enforces exact order-map
coverage, unique and nonblank archive category names, and that the pinned
`selectPolarisRestoreCategoryCandidates(categoryName)` query returns **only**
the selected local category ID. The pinned `categories` schema permits repeated
names, so FK validity alone does not protect against wrong-category restore.
No local category name/flags are updated automatically.

**38 Kotlin/JVM checks** (10 new) and **26 SQL/source checks** (4 new):
**64 combined host-only cases**, not real SQLDelight/Android compilation.
