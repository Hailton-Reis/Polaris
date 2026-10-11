# Issue #11 — merged-work backup/restore: staged portable planning (2026-10-11)

**Status:** 44 isolated Kotlin/JVM tests PASS (24 restore + 20 export). **NOT integrated into Yomotsu's production Backup model/Creator/Restorer; no Android proof; #11 remains P0 open.**

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

## 2026-10-11 — fail-closed SQL candidate hardening (17 SQLite tests)

Three additional regression tests were written **before** the candidate fix. They reproduced three previously unprotected data-corruption cases:

1. The pinned `mangas` schema does not enforce `UNIQUE(source,url)`, so two real manga rows may share the same source+URL. The candidate had previously relinked to either supplied ID; now it requires **exactly one** real row for the identity and otherwise leaves the orphan pending.
2. The migration14 schema permits a malformed `merged.merge_id` pointing to a **real** manga. The candidate previously relinked it; now both UPDATE and DELETE require a verified virtual parent whose `source=6969`.
3. The cleanup query previously deleted NULL pending links if a real manga with matching source+URL happened to have a merged row whose saved association's own `manga_url` was wrong. Cleanup now requires exact `attached.manga_source` **and** `attached.manga_url` equality before removing the pending reference.

Both the relink and cleanup statements now fail closed on an ambiguous local source identity and a nonvirtual parent. No title-based matching, schema migration, or real manga deletion is involved.

**Red/green evidence:** 3 new tests failed against the original candidate; 17/17 SQLite tests passed after correction. Independent runner-parser self-tests: 10/10 PASS. The two backup subsets of the actual offline aggregator completed **17 SQLite + 24 Kotlin = 41/41 host-only PASS**; **this does not mean the full 187-case five-gate set was run**. The new configured minimum is 72 Python + 36 SQLite + 38 main Kotlin + 17 backup SQLite + 24 backup Kotlin = **187**.

Evidence archive, including red/green logs, code snapshots, source Git blob hashes and JSON report: [Google Drive — issue11 hardening](https://drive.google.com/file/d/1XPMcRYO4LHs35xySldVu8k-IDXb8_DNg/view?usp=drivesdk), SHA-256 `0da0bca28355833160a328575540e21b351e7b1b12f94728f9351a7c9719c363`.

**Status unchanged:** still a candidate outside production `merged.sq`; issue #11 and the physical uniqueness problem #10 remain OPEN, SQLDelight + Android B01–B05 unverified, migration15 blocked.

## 2026-10-11 — export selection for nonfavorite real-source child mangas

**New host-only code:** `MergedBackupExportPlanner.kt`, `MergedBackupExportPlannerTest.kt`.

The original Yomotsu `BackupCreator.backup()` passes `getFavorites.await() + nonFavoriteManga` to `MangaBackupCreator`, and the latter exports chapters under **each actual manga ID**. A favorite virtual parent (source 6969) has no owned chapter rows; its real child source mangas may be nonfavorite and not otherwise included. The current app therefore **does not yet export those child snapshots**.

`MergedBackupExportPlanner.plan()` now produces:
- `works`: one `PortableMergedWork` per explicit virtual parent, preserving exact source+URL, current links, per-link flags/priority, root settings and optional canonical UUID; **never reconstruct deleted child links from the available catalog**.
- `additionalRealChildMangaIds`: deduplicated persisted **real child IDs** absent from the normal Yomotsu selection, including two virtual parents sharing one source; the future Android adapter must load these as ordinary `Manga` rows and pass them through existing `MangaBackupCreator` with the **same backup options**, preserving chapters/read/bookmarks/history/tracking as selected.
- `pendingSourceWorks`: explicit unresolved `sourceId+url` reference records where there is no live child ID. Do not fabricate an ID or silently discard a pending link.

The planner does **not** serialize the actual chapter records; it returns the exact persisted child IDs for the Yomotsu backup creator to serialize. A missing non-NULL child row, mismatching local ID/source/URL, ambiguous catalog, nonvirtual parent, duplicated links or contradictory root settings causes **a validation error instead of a silent incomplete backup**. When the user disables library entries in the backup, no multifonte records are selected. One intentionally retained child is allowed.

### Evidence and host gates

Local `kotlinc` compiled the **exact checked-in** `MergedBackupRestorePlanner.kt` alongside both test suites and the new export planner. Git blob SHA equality was verified for all seven staged/test/harness files. The project `run_tests.sh` executes both Kotlin test programs, now **24 restoration + 20 export = 44/44 PASS**. The actual offline `run_host_gate.py` executed its two backup stages together: **17/17 SQLite and 44/44 Kotlin = 61/61 PASS**, exit 0; parser tests **11/11 PASS**. This is a **subset**, not the complete five-stage project gate.

`scripts/r001/run_host_gate.py` now requires both unique success markers; missing, duplicate or insufficient markers fail closed. `spikes/domain-lab/build.gradle.kts` requires both tasks `spike001Backup` and `spike001BackupExport` inside `checkSpikes`. Configured five-gate minimum: **207** (72 Python + 36 original SQLite + 38 original Kotlin + 17 backup SQLite + 44 backup Kotlin). **No claim of complete 207-case gate execution, Gradle build, Android APK or real backup protobuf round-trip.**

Downloadable evidence ZIP stored under Polaris Drive: [2026-10-11 export backup host evidence](https://drive.google.com/file/d/14x40OxzeY3JO0uIpV9DfIBYiBMeWTD8B/view?usp=drivesdk), SHA-256 `137acb0181c17026ead2a60f9f3773e352e2b1c64e23efd7735085e1dd3defce`. Contains complete test logs, the two-stage aggregator JSON, 11 parser tests, compiler/environment metadata, seven tested source snapshots and exact Git blob SHA manifest.

**Next production gate:** add versioned `Backup.kt` field and Yomotsu exporter/restorer adapters that actually collect real child rows (including nonfavorite children), save their `BackupManga` snapshots, restore them before parent link reconstruction, and reattach transactionally. Preserve old Yomotsu backups. Still blocked on #2 real Android/SQLDelight baseline. Issue #11 remains P0 open, PR #1 draft, migration15 untouched.
