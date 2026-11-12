# Polaris R001 — typed BackupManga → SQLDelight parent-field projection

**19 October 2026. STAGING / HOST-ONLY. DO NOT WIRE INTO BACKUP v2 IMPORT.**

`PolarisBackupMangaSqlProjection.kt` is a Kotlin field projection deliberately authored to compile with the REAL pinned Yomotsu imports:

- `eu.kanade.tachiyomi.data.backup.models.BackupManga` and nested BackupChapter, BackupHistory, BackupTracking;
- `eu.kanade.tachiyomi.source.model.UpdateStrategy`;
- `tachiyomi.data.MemoColumnAdapter`, `StringListColumnAdapter`;
- `kotlinx.serialization.json.JsonObject`, `JsonPrimitive`.

The exact upstream source commit is `0fb80c439ef816eeb50674f1b90af39918b176d8`; parent DTO blob `BackupManga.kt` with ProtoNumbers 1, 2, 3... and 100–112 is the contract. The four backup model files and `DatabaseAdapter.kt` were inspected at that commit. The file was **compiled and tested only against host declaration stubs** representing those public fields and adapters, NOT against the real pinned JAR, generated SQLDelight or Android.

## Behavior

`prepare(archive, canonicalUuid, reservedParentId, localCategoryIdByArchiveOrder, technical)` is read-only: it prepares strongly typed ParentRow, ChapterRow, HistoryRow, TrackingRow and category/exclusion ID sets for the `PolarisParentMetadataRestore.sq` statements. It does NOT write SQL, change archive DTOs, fabricate local chapter IDs, or declare import ready.

- Canonical destination is `merged://polaris/<uuid>`, *not* the source device's `BackupManga.url` (archive remains untouched).
- Parent has all 25 known physical `mangas` field values, plus reserved `_id`, and the fixed virtual source 6969; `viewer_flags ?: viewer`, original timestamps, version, flags, notes, favorite and updateStrategy are retained.
- Upstream `StringListColumnAdapter` uses `", "` as a delimiter and is not invertible for some genre arrays. Mapper compares `decode(encode(list)) == list` AND rejects blank genre strings. It **refuses** unsafe archives rather than silently changing genres.
- `MemoColumnAdapter.decode(archive.memo)` checks the JSON object using the app's real adapter at future runtime. `JsonObject(original + canonicalUuid)` preserves every other unknown JSON key/value, refuses a conflicting UUID; chapter memo similarly uses the normal decoder.
- Categories use archive **order**, mapped after archive order → category name → destination local ID, never origin category primary keys. Reject missing/duplicate/category collisions.
- Chapters preserve URL/name, scanlator, read/bookmark/page, chapter-number Float represented as Double in physical DB, order, timestamps, version and memo; refuse duplicate URLs, non-finite chapter number or invalid progress.
- History is mapped by *exact chapter URL*, not foreign-key IDs from the origin device, rejecting missing or duplicate chapter URLs; duration is exact (never summed).
- Tracking honors pinned Yomotsu fallback: legacy `mediaIdInt` overrides `mediaId` when nonzero; both nonzero and conflicting is refused to avoid silent loss. Reject duplicate `syncId` and nonfinite Float metrics; other track metadata is retained.
- Source-specific chapter/provider edges, `merged` root, physical history chapter IDs and UUID ledger must be validated/written in one separate transaction; **this projection does not implement them**.
- `TechnicalState` exposes fields *not present in backup* (`last_update`, `next_update`, `cover_last_modified`, `calculate_interval`), with explicit destination defaults. These are not presented as original archived values and need approved destination policy.

## Reproduction

```sh
bash spikes/spike001/backup/restore-candidate/parent-field-projection/run_tests.sh
```

**89/89 Kotlin/JVM host cases PASS**, compiling `PolarisBackupMangaSqlProjection.kt` with small test-only stubs in this folder. The host memo decoder stub understands only a narrow subset of JSON; the test proves projection protocol, NOT actual real `kotlinx.serialization.json` parsing/unknown nested JSON keys. The Android implementation must compile against pinned real `MemoColumnAdapter` and run golden ProtoBuf+SQLDelight roundtrip tests with nested memo objects.

Blockers: real SQLDelight generated query bindings + same transaction as parent-LAST, complete 1:1 stored-field readback, typed schema converters and triggers, existing-parent retry semantics, actual ProtoBuf v1/v2 and Android B01-B05. Never remove the v2 fail-closed guard; migration15 untouched, PR #1 Draft, issue #11 OPEN.
