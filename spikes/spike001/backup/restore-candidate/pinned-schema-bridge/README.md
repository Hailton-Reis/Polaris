# Polaris R001 — compatibility gap in pinned Yomotsu SQLDelight (host-only)

**19 October 2026. NOT a production migration, not SQLDelight codegen, not Android.**

## Confirmed at the exact upstream pin

Repository `kiritsuguxs/yomotsu`, commit `0fb80c439ef816eeb50674f1b90af39918b176d8` has **no** `merged.sq`, no `merged` DDL, and no `merged` source code file in its complete 2,325-entry Git tree. The staged `SqlDelightPolarisAtomicVirtualWorkPort` and `polarisRestore.sq` rely on `merged` with columns `merge_id`, `manga_id`, `manga_url`, `manga_source`, `merge_url`, merge flags and ordering. Thus the existing candidate cannot be applied as written against that pin. Verify source tree before deciding whether to create a Polaris merge table and feature plumbing or adapt to a different upstream branch. A table alone does not implement the merged-source reader UI and domain.

Seven original, pinned source SQLDelight table definitions were manually transcribed into `pinned_schema_fixture.py` **with column sets retained** but SQLDelight-only type annotations stripped for bare `sqlite3`. Original blob SHAs are tracked in `SOURCE_BLOBS`. This fixture intentionally omits original triggers and is **not byte-identical to pinned SQLDelight source**; the original upstream has update timestamps/version triggers, which must be validated separately in production.

The bridge `merged_bridge_candidate.sql` adds *only* the missing candidate merged table, foreign keys, uniqueness indexes and restore UUID ledger to that host fixture. It is not applied to `14.sqm`/`15.sqm` or other production files. `native_restore_sql.py` uses physical native-shaped SQLite tables (`mangas`, `chapters`, `history`, `manga_sync`, `mangas_categories`, `excluded_scanlators`, `categories`) **instead of the prior synthetic `payload_json` or `tracking` columns**. The model needs the previous host fixture's `BackupManga`-shaped input validator and tests, imported from adjacent `full-parent-sqlite/` in the repository. SQLDelight Kotlin types, migrations, adapters, Android drivers and actual ProtoBuf codec remain unverified.

The candidate rejects ambiguous/missing real-source matches, unmapped category names, duplicated UUIDs, malformed memo, missing chapter for history, lossy genre delimiter, local alterations on replay and other conflicts. Uses `BEGIN IMMEDIATE`, verifies full relevant stored fields, commits both full metadata and parent edges in one transaction, and rolls back two parents together on second-parent failure.

## Evidence

Run in the Polaris repository checkout:

```sh
python3 -m unittest discover -s spikes/spike001/backup/restore-candidate/pinned-schema-bridge -p 'test_pinned_schema_bridge.py' -v
```

**49/49 Python SQLite tests PASS locally** against this pinned-*shaped* schema. All 49 are host checks (0 Android). In the tests, the unbridged baseline rejects the staged `merged` query (`no such table`). The candidate bridge repairs the SQL table dependency *only in the test database*. The complete aggregate gate, pinned runtime triggers/column adapters, SQLDelight code generator, Yomotsu source-domain integration, real ProtoBuf, and Android B01–B05 remain blockers.

A `manga_sync` unique constraint uses `ON CONFLICT REPLACE`, so live local tracking can be replaced by naïve replays; the port must preserve fail-closed replay behavior. The original Yomotsu `genre` adapter serializes list values as delimited text and might be lossy for embedded delimiters, which this host implementation refuses. Real v2 metadata restoration cannot be considered proven until adapter round trips and complete field readbacks are verified under Yomotsu's actual runtime triggers.

**Do not lift the v2 fail-closed import guard in `PolarisRestoreCoordinator`, merge Draft PR #1, or alter migration 15 on this evidence alone.**


## Correction (2026-10-19) — do not install a second merged table

This README previously characterized missing `merged` in pristine Yomotsu as a newly discovered integration blocker. **That wording is incomplete.** Polaris Spike-001 already supplies `new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq` and migration14; baseline and patched builds were reported successful in `docs/r001/ISSUE002_WORK_LOG.md`. The independent `merged_bridge_candidate.sql` is an **alternative test-only bridge for the pristine upstream** and MUST NOT be applied to a tree/database after Spike-001, where it would attempt a duplicate `CREATE TABLE merged`. For the actual existing Polaris path, audit legacy data then add ONLY the restore ledger and unique indexes on top of migration14; see `../spike001-layering/README.md` and `docs/r001/SPIKE001_LEDGER_LAYERING_CORRECTION_2026_10_19.md`. No production DB migration was performed. Android B01–B05 and full metadata restore are still open.
