# Polaris R001 — deferred-FK, parent-LAST atomic restore candidate

**Date 2026-10-19. Scope: Kotlin/Android NOT integrated; Python/SQLite rehearsal only.**
Pinned Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`.
Existing Polaris Spike-001 migration14 remains the owner of `merged`.

## Initial field-level incompatibility reproduced

The pinned Yomotsu `mangas` and `chapters` triggers update timestamps on **every UPDATE**. Existing category INSERT triggers may increment `mangas.version` through an UPDATE. Therefore the naive parent-first implementation either:
- applies category data with `is_syncing=0` and overwrites archived version/lastModifiedAt, or
- stages `is_syncing=1` during restore, then overwrites lastModifiedAt while finalizing the flag to 0.

Leaving `is_syncing=1`, dropping triggers or silently disregarding timestamp differences is unacceptable. `PINNED_SQLDELIGHT_PARENT_FIELD_TRIGGER_BLOCKER_2026_10_19.md` documents 35 passing SQLite tests including negative proofs and rollback.

## New safe-candidate hypothesis (NEW parents only)

Instead of creating a parent early then updating it, prevalidate a fresh UUID, reserve an unoccupied local `mangas._id` **under one SQLite write-locked transaction**, then:

1. Start ONE `BEGIN IMMEDIATE` and execute `PRAGMA defer_foreign_keys=ON` using the **same connection and transaction**.
2. Insert mapped `mangas_categories`, chapters, chapter-bound history, tracking, excluded scanlators, `merged` edges (including self-root referencing the reserved parent ID), and restore UUID ledger. Never coerce pending-child NULL IDs. Validate all archive refs in memory before writing.
3. Insert the full parent **LAST** at the reserved positive `_id` using the new staging SQLDelight statement `insertPolarisRestoredReservedParentLast`. Insert parent and chapter snapshots with `is_syncing=0` from the beginning, **without any post-parent UPDATE**.
4. Compare the entire physical manga/chapters/categories/history/tracking/exclusions/merged/UUID ledger state to the archive, prove `PRAGMA foreign_key_check` is empty after parent insertion, and commit. On ANY mismatch, ROLLBACK all parents as one transaction.
5. On SQLite COMMIT, `PRAGMA defer_foreign_keys` returns to 0 automatically. The parent was missing when category INSERT fired its UPDATE trigger, so its archive `version` and `last_modified_at` remain intact when the new parent is inserted last.

This approach does **not** disable/drop the app's triggers and does not leave `is_syncing=1`.

## Executed evidence and caveats

- Earlier 35/35 tests: real candidate SQL statements, source-shaped Yomotsu columns, reproduced pinned UPDATE trigger behavior and lossless-update conflict.
- **16/16 additional** new-parent-LAST tests: temporary deferred foreign keys, FK failure without deferral, category insert before parent, archived version/timestamp surviving commit, chapters with `is_syncing=0`, history/tracking, pending edges and root, local ID collision, missing parent COMMIT failure and rollback.
- **51/51 combined** local host SQLite cases PASS; separately reexecuted **98/98** prior UUID ledger/migration14 readiness cases PASS = **149 cases in two host suites**, not an Android execution.
- `backup-parent-sqldelight-fields` aggregate gate now requires 51. Total **898 minimum configured cases in 20 groups**, not yet executed as a whole.
- The statements in `spikes/spike001/backup/restore-candidate/parent-sqldelight-fields/PolarisParentMetadataRestore.sq` are *staging* and have NOT been compiled into Android SQLDelight-generated types.

**Open hard blockers:** Does the pinned SQLDelight Android driver expose the required same-connection transaction scope for `PRAGMA defer_foreign_keys=ON`? Can `BEGIN IMMEDIATE`, pre-reserved IDs, parent-LAST INSERT and readback be implemented without connection switching or scheduler interference? Are there other Android triggers/migrations/adapters beyond the reproduced ones? Will existing _empty placeholder_ reuse need a different lossless strategy? Is source child restoration separate and safe on retry? How do real ProtoBuf codecs roundtrip all metadata and unknown memo fields?

Therefore, **this is a promising new-parent-only transaction strategy, NOT a release-ready v2 restore implementation**. No production migration or Android code was modified; `PolarisRestoreCoordinator` continues to reject v2, migration15 stays untouched, PR #1 stays Draft and issues #2 and #11 stay open.

Evidence ZIP SHA256: `d0a5823ce85dee0a35940ac510acc28fd78ff4306171267a80ade5354787f8d3`.
Library: `/Polaris/R001/parent-sqldelight-fields/`.

Run from complete Polaris checkout: `bash spikes/spike001/backup/restore-candidate/parent-sqldelight-fields/run_tests.sh`.
