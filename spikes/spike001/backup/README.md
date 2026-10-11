# Issue #11 — merged-work backup/restore: staged portable planning (2026-10-11)

**Status:** 24 isolated Kotlin/JVM tests PASS. **NOT integrated into Yomotsu's production Backup model/Creator/Restorer; no Android proof; #11 remains P0 open.**

## Source of truth and compatibility

Baseline: `kiritsuguxs/yomotsu@0fb80c439ef816eeb50674f1b90af39918b176d8`.
Polaris branch: `r001/multisource-foundation`.

Yomotsu's `app/src/main/java/eu/kanade/tachiyomi/data/backup/models/Backup.kt` uses protobuf numbers **1, 2, 101, 104, 105, 106**. A **candidate**, not yet implemented, is a new top-level `@ProtoNumber(107) val polarisMergedWorks: List<BackupMergedWork> = emptyList()`. Before shipping, verify actual protobuf forward/backward decoding and that no other plugin/version has claimed the tag. Never renumber existing tags. A backup without the Polaris field should decode as an empty list and continue through the original Yomotsu restore path.

The current `MangaBackupCreator` serializes chapters belonging directly to each `manga.id`. The virtual parent keeps **zero** chapter rows; real source children own chapters. Thus a virtual parent's ordinary `BackupManga` does **not** preserve its merged links or child chapter progress. The new message must preserve each linked child's **source ID and canonical source URL/key**, plus all per-link flags, sort priority, and the virtual root settings. **Local DB manga IDs and the `merged://<local IDs>` URL are not portable.**

### Payload requirements not yet implemented

- One versioned merged-work record per favorite virtual parent; an **archiveWorkKey** unique within a backup and preferably a stable canonical UUID when available. Do not assume the parent ID/URL from one device identifies the same parent on another. Across multiple different archives, reliable deduplication will require a durable canonical UUID or persisted restore ledger.
- Explicit linked child list only, **never reconstruct from the original creation child set or title**. A deliberate unlink must survive backup/restore.
- Each child: full `sourceId + source URL`, display/metadata, all five merge flags (`info_manga`, `get_chapter_updates`, `chapter_sort_mode`, `chapter_priority`, `download_chapters`) and a **BackupManga snapshot** (including chapters/history when selected) even if this child is not separately favorited. Deduplicate embedded snapshots by source+URL when multiple parents share a child; respect original backup options. Without child snapshots the current production backup could still lose non-favorite child reading state.
- Root settings and optional canonical UUID/progress/glossary metadata (canonical state belongs to Spike-018 once #3 exists).
- Ensure no data deletion or silent overwrite when an archived child is unavailable or unresolved.

## Implemented host planner

Files: `MergedBackupRestorePlanner.kt`, `MergedBackupRestorePlannerTest.kt`, `run_tests.sh`.

```bash
bash spikes/spike001/backup/run_tests.sh
```

The planner consumes explicit source identities, installed real-source IDs and existing local source works and produces:

1. **REUSE_EXISTING**: exact source ID+URL already exists locally, even if the extension is missing; display an unavailable-source warning separately.
2. **CREATE_CHILD_STUB**: source extension is installed but the real child row is absent; the caller must restore/create the child using its source-specific backup snapshot, then return its **new local ID**.
3. **PENDING_EXTENSION**: no matching local child and extension absent; keep `manga_id=NULL`, original `manga_source` + `manga_url`, and display a restoration warning.

`bindCreatedChildren` fails closed on missing/duplicate/mismatched child IDs and never assigns one device's exported IDs on another. The resulting links are kept in original priority order; the root reference remains a separate settings record. A virtual work with just one remaining linked child is valid on restore even though the original UI creation requires two independent sources.

**Limits:** pure Kotlin only. This is NOT a database transaction or serializer. The code has not been moved to a Yomotsu module; no deployed migrations, `14.sqm`, `15.sqm`, application UI or backup byte stream were changed.

## Android integration sequence, after #2 B01–B05

1. **Protobuf:** add a new `BackupMergedWork` model and an unused optional top-level tag. Add round-trip golden tests: stock Yomotsu archive decodes; Polaris archive decodes; newer unsupported record fails without erasing the original archive. Verify the GZIP/ProtoBuf full backup route, not only Kotlin data classes.
2. **Exporter:** alongside `BackupCreator.backupMangas`, collect all virtual favorite parents and their current `merged` references; collect **nonfavorite child snapshots** with their true source IDs and chapter state using the existing MangaBackupCreator; exclude synthetic root from child list. Never rely on chapters of parent id 6969.
3. **Restore ordering:** `BackupRestorer.restoreManga` currently `launch`es the manga batch in a coroutine and its `MangaRestorer.restore` transaction resolves originals via URL+source. The merged-link reconstruction **must await the child restoration job**, rather than start another asynchronous sibling coroutine and race. Prefer a sequenced suspend operation in the same restored-library phase.
4. **Resolve:** find/create source child rows using exact source ID and URL, build original-key -> new-manga-ID mapping, find/create virtual parent using a durable work key, and write root/child associations with a transaction and duplicate-safe operations. A missing extension must not erase a work; if using `merged.manga_id=NULL` preserve source+URL and retry when an extension reappears.
5. **Interrupted restore:** persist a restore ledger (or canonical UUID once #3 exists), so retry does not create two parents or restore deliberately removed links. Restore must be idempotent; avoid `CreateMergedManga`'s local-ID-derived `mergeUrl` as backup identity.
6. **Regression:** physical device/emulator two-source full round-trip; children with different destination DB IDs; one source not in library; missing extension; interrupted restore; intentional unlink; repeated restore; two parents sharing one source; old backup; existing read/bookmark/history; chapter/download/source ownership; full Yomotsu regressions. Include the pending warning in the restore error log/UI.

## Decision and gate

**Do not claim #11 fixed by these host tests.** Defer production changes until #2 has real Android build/route evidence B01–B05, then implement the serializer/adapter with a tested upgrade path. No migration 15 at this stage; keep draft PR #1 as draft. The 24/24 Kotlin tests are separate from the earlier 146 host checks, which should not be retroactively relabeled as a unified gate.

## Additional SQL integration finding — orphan relinking, 2026-10-11

The current `merged.sq` `insert` statement is idempotent when repeatedly inserting either the same resolved `mangaId` or the same NULL child. **It is NOT idempotent when an existing NULL orphan later reappears with a real local child ID.** An INSERT of `mergeId+source+URL+mangaId=NULL` followed by an INSERT of the same logical child with `mangaId=30` produces **two rows**, one NULL and one resolved. This was reproduced using the exact published SQLDelight `merged.sq` (Git blob `3e9fb499d0e1d0523aaaaaae336dd9bf5b2d4b62`) and migration-14 (`8f23dc5219f49a0368705ba21d0c4e5a0d7fb1fb`).

A **candidate only** (not added to production queries) exists in `orphan_relink_candidate.sql`: transactionally rebind the oldest NULL source+URL association to the verified destination manga ID, and remove surplus NULL duplicates only once an exact-source+URL resolved association exists. It protects other parents, excludes synthetic source 6969, preserves original link settings/priority, and never guesses by title. The correct Android implementation should add appropriate SQLDelight queries, verify zero/one affected rows, and consider serialization and concurrency together with #10.

```bash
python3 -m unittest discover -s spikes/spike001/backup -p 'test_*.py' -v
```

**14/14 SQLite cases PASS**, including one explicit defect reproduction (the old DML creates a duplicate) and successful candidate repair cases. All four staged Kotlin/SQL/test artifact hashes matched the locally executed files. These 14 are **not** Android verification and are **not** part of the existing unified host gate. **Do not change migration14/15 or the production query until the issue #2 Android baseline is proven.**
