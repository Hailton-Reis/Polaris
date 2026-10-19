# Polaris R001 — Full-parent SQLDelight query surface + pinned trigger incompatibility

2026-10-19. **Staging / host tests only. NOT an Android integration.** The
existing Yomotsu baseline and Polaris Spike-001 migration 14 are retained.
Do not modify migration 15, remove the v2 preflight guard, or merge PR #1.

## Deliverable

`PolarisParentMetadataRestore.sq` is a SQLDelight-style staging query candidate
covering the physical Yomotsu tables `mangas`, `chapters`, `history`,
`manga_sync`, `mangas_categories`, `excluded_scanlators`, `categories` and
Spike-001 `merged`. It has explicit **full-column** parent/chapter INSERT,
exact history/tracker/category/exclusion INSERT, and the physical readback
selectors needed by `PolarisFullParentTransactionCoordinator`.
The future Kotlin DB port must use these queries inside **one** transaction
alongside the reviewed UUID ledger migration/queries and existing merge-edge
queries; no Android port exists yet.

The query file must NOT be copied into the real app before reviewing generated
SQLDelight signatures (the real `memo AS JsonObject`, `genre AS List<String>`,
`favorite AS Boolean`, `update_strategy AS UpdateStrategy`, Date adapters),
DAO location, repo schema and import lifecycle. This test environment strips
the Kotlin SQLDelight type annotations from a pinned-*shaped* SQLite fixture;
it does **not** build any Yomotsu APK or generated Kotlin code.

## Important new source-confirmed blocker: UPDATE triggers

The pinned Yomotsu `mangas.sq` defines `update_last_modified_at_mangas`,
`update_manga_version`, `update_last_favorited_at_mangas`; its
`mangas_categories.sq` defines `insert_manga_category_update_version`;
`chapters.sq` defines analogous timestamp/version triggers. The relevant
trigger text is reproduced in `pinned_update_triggers.sql`, from commit
`0fb80c439ef816eeb50674f1b90af39918b176d8`.

- Insert a parent with archive `last_modified_at=123456789`, `version=7`,
  `is_syncing=0`. Adding a category updates parent `version` to 8 and fires
  a timestamp UPDATE trigger, changing its archived timestamp.
- Use `is_syncing=1` during category restore: the version/time remains stable
  while the flag stays 1. **But leaving `is_syncing=1` is unacceptable** for
  normal future change tracking.
- Resetting `is_syncing` to 0 with an UPDATE fires
  `update_last_modified_at_mangas`, changing the archived timestamp anyway.
  The same issue arises when changing `chapters.is_syncing` to 0.
- Therefore **no demonstrated non-destructive field-exact finalize strategy
  exists at this pinned baseline**. A future adapter must find/verify an
  allowed approach, and physically check every restored field. Do not claim
  full v2 metadata restoration or treat an `is_syncing=1` record as success.
  Do not drop/disable production triggers merely to pass a test.

Genre needs a lossless round-trip through `StringListColumnAdapter` (which uses
`, ` as a separator); archive strings containing the separator are ambiguous.
`BackupManga.viewer_flags ?: viewer` must map to `mangas.viewer`.
`BackupManga.memo` is JSON-encoded bytes mapped to `JsonObject` and its unknown
keys must survive UUID binding. Tracking's `mediaIdInt` legacy fallback,
category `BackupCategory.order` -> name -> destination ID, and history
`BackupHistory.url` -> newly restored chapter ID must be implemented without
silent filtering or merging read durations.

## Local validation

From the repository checkout:

```bash
bash spikes/spike001/backup/restore-candidate/parent-sqldelight-fields/run_tests.sh
```

**35/35 Python/SQLite tests PASS** on source-shaped in-memory tables using the
original Polaris Spike-001 migration 14, proposed additive restore ledger,
physical query statements parsed from this new `.sq`, and pinned Yomotsu
trigger bodies. A two-parent strict timestamp readback failure rolls back the
entire transaction; chapter/category FK and memo preservation are checked.
This is **not** generated SQLDelight code, a real ProtoBuf codec, or Android.

The complete R001 host gate remains separate. This proof does NOT authorize
production database writes or backup v2 import. Issues #2 and #11 remain OPEN.
