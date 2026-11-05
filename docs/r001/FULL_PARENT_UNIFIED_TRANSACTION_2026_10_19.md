# Polaris R001 — unified full-parent v2 transaction contract (host-only)

Date: 2026-10-19. **STAGING ONLY. NOT PRODUCTION ANDROID RESTORE.**
Related: Draft PR #1, P0 issue #11, pinned Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`.

## Problem addressed

The previous `SqlDelightPolarisAtomicVirtualWorkPort` stages a transaction for UUID parent creation, restore ledger and linked source edges. The full `BackupManga` parent snapshot (notes, categories, chapters, history, tracking, flags, memo, exclusions) is prepared by a separate staging planner. Calling two separate transaction implementations would risk a partial parent when metadata restoration fails.

## Implemented staging contract

`spikes/spike001/backup/parent-candidate/unified-transaction/PolarisFullParentTransactionCoordinator.kt` introduces:
- `PolarisFullParentAtomicTransactionPort.transaction { ... }`, encompassing **all** parent UUID, metadata, ledger and edge changes;
- `PolarisFullParentTransaction` with transaction-bound methods for complete UUID owners (including legacy colliders), exact destination category names, exact resolved child source+URL rows, untracked-parent guards, create/apply to new or proven empty parent and **mandatory readback** for every parent (also repeated imports);
- Pre-write consistency checks between v2 `BackupPolarisBundle` and `RestoredPolarisWork`: UUID/title/root and child settings, link order, pending-null invariants, unique real-ID identity;
- Fresh category order->name->destination ID mapping and real child lookup **within the same transaction**, followed by the existing `PolarisParentMetadataRestorePlanner.prepare` **inside** that transaction;
- Hard rollback on any exception including incomplete writes, ambiguous matches or changed local parent state.

The new port is **NOT** implemented against real SQLDelight. Its `createAndApplyFullParent` and `assertExactFullParentState` obligations explicitly require ALL fields and relationships. An Android port must enforce ledger/index uniqueness, source and UUID identity, accurate category remapping and full metadata readback in actual SQLite transaction scope. Do not simply invoke the earlier association-only port plus stock `MangaRestorer` in separate transactions. Source-child ordinary backup restoration still precedes this parent transaction and is **not** rolled back by it.

## Executed evidence

- **44/44 Kotlin/JVM standalone cases PASS** using host doubles for `BackupManga`, staged backup DTO, `RestoredPolarisWork`, serialization annotations and transactional port. Includes rollback of two parents on second-write failure, empty-parent reuse, replay, category ambiguity, pending links, settings drift and readback failure.
- **42/42 existing Python/SQLite host cases PASS**, rerun separately. These use a synthetic full-field schema and **do not** exercise Yomotsu's generated SQLDelight DB.
- **86 separately executed host checks, not a single Android test suite.**
- The committed `run_tests.sh` is designed to compile actual staged `BackupPolarisBundle.kt` and `PolarisRestoreCoordinator.kt` with fake annotations; that full-checkout runner has **not** executed in this environment.
- The host gate gained `backup-full-parent-unified-kotlin` (minimum 44). Together with the previous 42 SQLite checks, the total is **700 configured minimum cases / 17 groups**, NOT an executed full gate.
- `.github/workflows/domain-spikes.yml` now includes both 42-case SQLite and 44-case Kotlin tests. This only configures CI; does not prove it ran successfully.

Evidence package: Library `/Polaris/R001/unified-full-parent-kotlin/Polaris_R001_Unified_FullParent_Transaction_Kotlin_2026-10-19.zip`, SHA-256 `9fb014ca1c820d9ed9a7f05fa388fba8a28549bd322cc6527c49b63808c41da0`.

## Hard blockers remain

1. Implement transactional, field-complete `PolarisFullParentAtomicTransactionPort` against pinned SQLDelight 2.3.2, not the synthetic JSON columns.
2. Audit old virtual-parent identities, duplicates and schema compatibility before any migration.
3. Verify actual Kotlin ProtoBuf v1 and v2 encode/decode, complete `BackupManga` roundtrip and unknown memo key preservation.
4. Verify Android baseline #2 B01–B05 with two real source extensions; exercise backup, restore, retry, rollback and live edits.
5. Keep v2 `PolarisRestoreCoordinator.preflight` rejection; no migration15, real user database or APK change in this round.

**PR #1 remains Draft and issue #11 remains OPEN.**
