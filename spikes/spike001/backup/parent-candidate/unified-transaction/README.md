# Polaris R001 — Unified full-parent Kotlin transaction protocol (STAGING)

2026-10-19. Issue #11 / PR #1. **Not integrated in Yomotsu/Android.**

The full-parent v2 backup planner and the earlier SQLDelight association port currently represent different persistence actions. Calling them as two independent transactions risks restoring a virtual parent and associations but leaving notes, chapters, progress, history, tracking and categories missing if a later metadata operation fails.

## Candidate

`PolarisFullParentTransactionCoordinator.kt` is a host-portable Kotlin bridge between:

- the real staged `BackupPolarisBundle` and original complete `BackupManga` objects;
- `PolarisParentMetadataRestorePlanner` (canonical UUID, original ordinal, destination stable URL, category-order mapping);
- `RestoredPolarisWork` produced by the child-first coordinator; and
- a **NEW** `PolarisFullParentAtomicTransactionPort` interface that requires the eventual Android implementation to use ONE transaction for parent identity, category remap, full metadata, parent links, UUID ledger and mandatory readback.

The coordinator validates portable/resolved UUID sets, exact child order and source+URL identity, merge settings, pending/null status, global real-ID integrity, and archive category orders before writing. **Inside** the transaction, it queries live category names and exact child IDs, obtains all existing UUID owners, rebuilds the parent plan, rejects legacy collisions, creates/applies a complete snapshot through the port, and always performs readback (even for a no-op replay). Any exception rejects the entire transaction. There is no title-based matching and no URL guessed from the old device.

The new transaction port MUST implement full field-by-field persistence/readback with the pinned Yomotsu `BackupManga`, including memo byte content, notes, flags, genres, metadata, categories, chapters/progress/history, trackers, exclusions and all source edges and root flags. This method contract is NOT an implementation and DOES NOT replace the existing `SqlDelightPolarisAtomicVirtualWorkPort` until a reviewed refactor composes both concerns into a single transaction.

## Evidence / limitations

The initial **44/44 Kotlin/JVM local tests PASSED** with host-only `BackupManga`, `@Serializable`, protobuf annotation and `RestoredPolarisWork` doubles. The executable repository script instead compiles the real staged DTO, original metadata planner and real `RestoredPolarisWork` coordinator source with fake annotations/DB, so it still requires execution in a full repository checkout. No actual SQLite driver, SQLDelight Kotlin-generated query API, real protobuf, Android APK or B01–B05 verification is included in these Kotlin checks.

Run in checkout:

```sh
bash spikes/spike001/backup/parent-candidate/unified-transaction/run_tests.sh
```

Keep v2 `PolarisRestoreCoordinator.preflight` refusal, Draft PR #1, issue #11 open, migration 15 unchanged. Do NOT claim issue #11 resolved.