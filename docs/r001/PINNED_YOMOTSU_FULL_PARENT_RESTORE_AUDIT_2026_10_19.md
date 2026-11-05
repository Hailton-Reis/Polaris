# Polaris R001 — field-complete virtual-parent restore: pinned Yomotsu audit

**Date:** 2026-10-19. **Scope:** technical staging only; no Android restoration approval.

Sources audited (Yomotsu `kiritsuguxs/yomotsu` commit `0fb80c439ef816eeb50674f1b90af39918b176d8`):

- `app/src/main/java/eu/kanade/tachiyomi/data/backup/models/BackupManga.kt`
- `app/src/main/java/eu/kanade/tachiyomi/data/backup/restore/restorers/MangaRestorer.kt`
- `app/src/main/java/eu/kanade/tachiyomi/data/backup/restore/restorers/CategoriesRestorer.kt`
- Polaris `spikes/spike001/backup/restore-candidate/sqldelight-port/kotlin-candidate/SqlDelightPolarisAtomicVirtualWorkPort.kt`

## Source-confirmed integration hazards

1. **Old archive URL is not the destination URL.** Stock `MangaRestorer.findExistingManga`
   queries by backup `(source,url)`. Directly passing the source-6969 parent
   snapshot to the stock restorer will look for the origin device's old URL,
   not the UUID-stable destination URL introduced by the Polaris SQLDelight port;
   it can therefore create a second parent. The staging planner now carries
   `destinationUrl=merged://polaris/<canonical-uuid>` separately and retains the
   unmodified `fullBackupManga.url`. It does *not* invoke the stock restorer.
2. **Archive category values are `BackupCategory.order`, not database IDs.**
   `MangaRestorer.restoreCategories` uses `backupCategories.associateBy { it.order }`,
   resolves by `name` into destination categories, and then writes destination IDs.
   `CategoriesRestorer` separately creates/looks up categories by name. The
   Polaris plan explicitly requires `categoryOrderToDestinationId`; a missing
   mapping or collapsed distinct categories is a hard failure.
3. **Stock category restoration may silently omit unresolvable entries.**
   It uses `mapNotNull` for absent archive order/name/local category; even a
   successful stock restore is not proof of full metadata preservation. Polaris
   must fail closed on missing mappings BEFORE parent metadata writes.
4. **Stock history restoration can drop entries.** History entries whose chapter
   URL cannot be found under the destination manga ID are skipped. The virtual
   parent may have different chapter identity/lifecycle semantics, so one must
   verify all archived history entries by explicit policies, not just await a
   stock `MangaRestorer.restore` call.
5. **Stock tracking/chapter restore is a merge, not bitwise replay.** The stock
   restorer merges bookmarks/read flags/progress and may preserve newer local
   values. Tracker progress uses `max(...)`. Idempotent/strict replay must
   separately distinguish permitted local edits from true identical metadata.
6. **Memo is serialized bytes.** `BackupManga.memo: ByteArray` is decoded through
   `MemoColumnAdapter`. A UUID ledger applied by constructing a new JSON object
   with only the Polaris UUID would erase unrelated existing memo keys. An
   eventual metadata applier must merge UUID into the complete original memo,
   reject malformed/foreign UUIDs, and preserve all unknown keys/values.

## Full BackupManga archive fields that must be accounted for

Source/provenance: `source`, `url`, `title`; descriptive metadata: `artist`,
`author`, `description`, `genre`, `status`, `thumbnailUrl`; user metadata:
`favorite`, `dateAdded`, `viewer`, `viewer_flags`, `chapterFlags`, `favoriteModifiedAt`,
`version`, `notes`, `initialized`, `memo`, `updateStrategy`, `lastModifiedAt`;
children/relationships: `chapters`, `categories`, `tracking`, `history`,
`excludedScanlators`. These are distinct fields; the host BackupManga test
stubs only cover a subset. Field-completeness requires a real Kotlin serialization
roundtrip and explicit post-restore comparisons.

## Required Android/SQLDelight adapter design before unblocking v2

- Decode and validate the v2 bundle before stock writes; partition ordinary
  children from source-6969 full parent payloads.
- Resolve real child source+URL identities first, keeping missing/pending links.
- Map every archived parent UUID to at most one ledger-bound destination parent;
  reject legacy/untracked UUID collisions and source/URL mismatch.
- Resolve `BackupCategory.order` to unique existing/created destination IDs by
  explicit archive name, refusing missing/collapsed mappings.
- Recheck UUID, destination URL, complete metadata conflict/equality and
  destination category mapping *inside* an atomic restoration transaction.
- Apply the FULL selected BackupManga state at the SINGLE UUID-resolved parent ID;
  preserve unknown memo properties, remap categories, restore chapters/history/
  tracking/exclusions and safely handle interrupted attempts.
- Avoid invoking stock `MangaRestorer.restore(backupSnapshot)` with the original
  virtual-parent URL. Use a reviewed identity-bound adapter, not title heuristics.
- Verify rollback, replay, local edits and all relevant metadata fields on the
  *real* SQLDelight 2.3.2 generated driver, then real ProtoBuf v1/v2 and Android
  B01–B05 with two source extensions.

**Current staging proof:** 28/28 Kotlin/JVM tests with representative test doubles,
including three new destination-URL regressions. No production SQL/schema,
migration 15, or v2 fail-closed import guard was modified. The new planner is
NOT a transaction or implementation of complete restoration.
