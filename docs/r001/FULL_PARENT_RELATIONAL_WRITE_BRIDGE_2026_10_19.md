# Polaris R001 — Kotlin projection to full relational parent restore (host proof)

2026-10-19. **HOST STAGING ONLY, not production Android.**
Pinned Yomotsu: `0fb80c439ef816eeb50674f1b90af39918b176d8`.
Branch `r001/multisource-foundation`, Draft PR #1, issue #11.

## Actual new code

Implemented `spikes/spike001/backup/restore-candidate/parent-relational-port/` with a **new-parent-only** reference writer `physical_parent_writer.py` that executes the already staged `PolarisParentMetadataRestore.sq` and original Polaris Spike-001 `merged.sq` statements on disposable SQLite. It uses the original Yomotsu-shaped host tables + pinned update triggers; no synthetic `payload_json` columns.

For each parent, inside ONE BEGIN IMMEDIATE transaction with `defer_foreign_keys=ON`:

1. Validate canonical UUID, archive digest shape, full parent JSON memo UUID, genre roundtrip, category/chapter/history/tracker/exclusion/source-link identity. Reject UUID memo/URL legacy claims, ambiguous physical real child source+URL, stale child ID, newly resolvable pending link, duplicate parents and conflicting local data.
2. Reserve a new positive destination manga ID **under the writer lock**. Independently verify the Kotlin Prepared parent/chapter reserved IDs exactly match that reserved ID; otherwise refuse.
3. Insert category relations, full chapters (RETURNING local chapter IDs), history linked to those IDs with exact duration, tracking, exclusions, existing merged source/pending/root edges and UUID ledger. The root references the reserved future parent ID.
4. INSERT the complete `mangas` row **LAST**, with `is_syncing=0`, avoiding the pinned category and UPDATE trigger timestamp/version drift.
5. Physically SELECT and compare **all** parent persistent columns and every chapter, history, tracker, category, scanlator exclusion, merged link and UUID ledger row before COMMIT; check `PRAGMA foreign_key_check`. Abort/rollback on any mismatch including extra rows. Multiple parents belong to the same transaction; failure on the second restores none.

The second file, `ProjectionSqlBridgeFixture.kt`, executes the actual staged `PolarisBackupMangaSqlProjection.prepare` Kotlin mapper against existing pinned-field host DTO/JSON stubs; it emits a prepared JSON row batch consumed by the new Python relational writer. This is a genuinely connected **Kotlin field projection → SQL statements → physical SQLite readback** test, rather than two independent tests. The fixture uses reserved parent 103, the local target ID under its two known real-source rows; the reference writer verifies that Kotlin's prepared IDs match the reserved physical ID.

## What ran

- **69/69 new standalone host integration tests PASS**, via `bash spikes/spike001/backup/restore-candidate/parent-relational-port/run_tests.sh`. The bash runner compiles the typed Kotlin projection to a temporary JAR with explicit host DTO/JSON declaration doubles, exports the fixture and runs disposable Python SQLite tests. It deletes temporary binary outputs after execution.
- Positive tests include full parent/chapters/category/history/tracker/excluded-scanlator/merged-root/pending-edge/UUID-ledger recreation and retention of deeply nested memo keys **in SQLite**.
- Negative cases reproduce corrupted/missing/extra rows, physical child ambiguity, duplicate or malformed UUID and category identity, user-edit conflicts, mismatched prepared parent/chapter IDs, stale pending links, FK integrity failures and all-parent rollback when the second parent fails.
- Reproduced initial test failure of chapter-drift check caused by pinned UPDATE triggers; adjusted fault injection to isolate the chapter field, then passed. Both source code and produced Git blobs were verified after publication.
- New 23rd host gate `backup-parent-relational-write` requires **69** cases; total **1,089 minimum configured tests in 23 gates**, **NOT** an executed 1,089-test aggregate or CI/Android PASS.

## Strict boundary

**The Python writer is not an Android implementation.** The Kotlin compiled fixture uses **host doubles** for `BackupManga` and `MemoColumnAdapter` and does not prove real ProtoBuf, SQLDelight-generated adapters, or the packaged Android SQLite binary. Nested memo retention is tested using actual JSON bytes in SQLite, separately from the simplified Kotlin fake decoder. The source SQL statements are original staged candidate .sq files, **not** generated SQLDelight Kotlin query bindings.

Production still requires porting the algorithm to a Kotlin implementation of `PolarisFreshParentStages`/transaction port using the **real pinned SQLDelight 2.3.2 driver**, making reserved ID selection and projection creation atomic on that connection. It also needs a reviewed ledger migration, complete generated adapter and Android B01–B05 verification. This path intentionally refuses existing EMPTY parent reuse and ALREADY_IDENTICAL replay, rather than silently replacing local edits. Prior ordinary source child restoration lies outside this atomic parent transaction.

The v2 `PolarisRestoreCoordinator.preflight` remains **fail-closed**, migrations 14 and 15 unchanged, PR #1 Draft, issue #11 OPEN, no user database modified.

Evidence package and SHA256: `Polaris_R001_Parent_Relational_Write_69_Host_2026-10-19.zip`, `b9f3fc186fc1890345cbcdcd038fcb97bdaeb8eca247aaa177e085e0007b7c7f`. Stored in Library `/Polaris/R001/parent-relational-write/` with the 69-case log, full source tree and pinned-shaped dependencies.
