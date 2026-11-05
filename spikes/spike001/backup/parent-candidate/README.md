# Polaris R001: lossless virtual-parent backup partition (STAGING ONLY)

The pinned Yomotsu `BackupManga` already saves notes, categories, history,
chapters, tracking, favorite flag, page/viewer preferences, and the JSON memo.
The current staged backup exporter puts a virtual source `6969` manga into
ordinary `Backup.backupManga` **and** describes it in the Polaris UUID bundle.
Running both stock and new restore would create TWO parent rows.

`PolarisParentSnapshotPartitioner.partition` is a pure **producer-side candidate**:
- Takes an explicitly ID-bound list produced by zipping the selected `Manga`
  records with `MangaBackupCreator` snapshots. Every `(source,url)` must match.
- Requires exactly one canonical UUID and one complete original `BackupManga`
  for EACH selected virtual parent (identity bound by original local ID, **never
  inferred by matching a title**).
- Keeps real-source snapshots in ordinary order; moves full virtual-parent
  objects into `BackupPolarisParentPayload(archiveUuid,manga,originalOrdinal)`.
- Rejects unmatched synthetic manga, missing parents, UUID collisions,
  duplicate local IDs, stale titles/URLs and changed snapshot order.
- `reassembleOriginalOrder()` proves the split is reversible before encoding.
  It does not edit SQLite or remove chapters, categories or user notes.

## Test

```sh
bash spikes/spike001/backup/parent-candidate/run_tests.sh
```

**23/23 Kotlin/JVM host tests PASS.** The committed Kotlin candidate is
written to use the pinned real `BackupManga.source`, `.url`, and `.title`
properties, but standalone tests use a `BackupManga` host double containing
representative metadata, **not** the actual ProtoBuf serializer or SQLDelight.

## Explicit blockers before Android enablement

1. Introduce the `BackupPolarisParentPayload` as a new optional archive field,
   with tested *actual* ProtoBuf round-trips, older-backup compatibility,
   archive format-version migration, and rejection of missing parent payloads.
   This candidate data class is currently separate from `BackupPolarisBundle`.
2. Integrate the split into `BackupCreator` **before writing archive bytes**.
   Ensure every emitted ordinary `backupManga` has `source != 6969` whenever
   a nonempty Polaris bundle exists. The existing duplicate-parent preflight
   MUST remain active and fail closed until that integration is complete.
3. On restore, bind each UUID to EXACTLY ONE newly created or verified parent ID
   and import the full original metadata, notes, categories, tracks/history and
   reading state onto **that exact parent** (never a second ordinary parent).
   Updating restored parent metadata and ledger must have a reviewed failure
   and replay strategy; app-specific category IDs must be remapped safely.
4. Preserve **all** old memo JSON keys when adding Polaris UUID; the previous
   staged parent insertion stores only the UUID and is not enough to preserve
   parent preferences. Define no-overwrite behavior for local edits on replay.
5. Audit old virtual source URLs, existing UUID memos, parent categories and
   chapters, then test on Android B01-B05 and actual SQLDelight 2.3.2 database.

**DO NOT merge** this staging package into the Android source tree or remove
any existing fail-closed backup/restore guard. No user database was modified.
