# Polaris R001 — Yomotsu strict real-child restoration candidate

**Host-validated candidate only. No production `BackupRestorer.kt`, migration 15,
SQLite schema, or Android/ProtoBuf code path changed.**

## Discovered correctness blocker

Pinned Yomotsu `BackupRestorer.kt` Git blob `ce21be4073a5a168376e95e0fa6f317bf88b8c98`
uses `restoreManga()` in batches of 100. If a batch fails it retries each manga,
then catches individual `MangaRestorer.restore()` failures, records `errors`,
and increments progress **without throwing**. Mere coroutine completion cannot
be the Polaris `awaitVerifiedOrdinaryRestore()` success barrier.

Pinned `GetChaptersByMangaId.kt` blob `1dee7770e1d041dc7f67d0782f6f1776a305e876`
also catches query errors and returns `emptyList()`; therefore the new port uses
**direct** typed `database.chaptersQueries.getChaptersByMangaId(id, false)`
with `awaitAsList()`, so DB errors propagate.

## Candidate source adapter and integration sequence

`kotlin/YomotsuPolarisSourceRestorePort.kt` implements the existing
`PolarisSourceRestorePort`, using the real `MangaRestorer.restore(backup,
categories)` API and the earlier `polarisRestoreQueries.selectAllExactSourceChildIds`
SQLDelight query. For each supplemental child, the call is strict (failures throw)
and is followed by unique `(source,URL)` local manga-ID matching. Every backed-up
chapter URL must exist **exactly once** in the database, retain `read=true`,
`bookmark=true`, and have `last_page_read >= backed-up progress`.

`kotlin/PolarisYomotsuStrictRestoreSequence.kt` builds a fail-closed
Polaris-only path around the **actual** `BackupPolarisBundle` and
`PolarisRestoreCoordinator`. It calls preflight before writes. After all
stock `restoreManga()` jobs complete, but before creating virtual parents,
it strictly replays and verifies **only ordinary backup manga that are
required by the restored Polaris works**. Missing ordinary children must be
present in the supplemental section (enforced by bundle preflight). Unrelated
ordinary backup errors do not incorrectly block a valid linked work. Legacy
backups and `libraryEntries=false` preserve their original no-Polaris path.

**Important:** a supplemental `MangaRestorer.restore()` may already write its
real source manga row before a later chapter validation fails. This candidate
prevents the virtual parent commit, but it does not roll back all ordinary and
supplemental mangas globally. Verify history, tracking, excluded scanlators,
category state, and chapter-progress merge behavior in the Android runtime.
The fallback can repeat actual source restoration for linked ordinary works;
profile its cost and idempotence before production.

## Reproduce local validation

The local host lab contains two fully executable Kotlin programs and stubs for
**only** `MangaRestorer`, SQLDelight database/query objects, `BackupManga`/
`BackupChapter`, and serialization annotations. The **actual** committed
`BackupPolarisBundle.kt` and `PolarisRestoreCoordinator.kt` are compiled,
not rewritten.

```bash
bash spikes/spike001/backup/restore-candidate/yomotsu-source-port/run_tests.sh
```

Verified locally: **23/23 source-port** + **14/14 coordinator sequence** =
**37/37 Kotlin/JVM host cases passed** using Java 21 and kotlinc.

The `backup-yomotsu-children` gate requires two independently unique markers
`POLARIS_YOMOTSU_SOURCE_RESTORE_PASS 23` and
`POLARIS_YOMOTSU_RESTORE_SEQUENCE_PASS 14`, with independent minima. This adds
37 configured cases to the eleven previous groups, for **458 minimum cases
configured across 12 host gates**. The entire 458 tests have NOT been run.

**Unverified:** Actual SQLDelight 2.3.2 code-generation and typed signatures,
Android SQLite driver/transactions, real category/history/tracking persistence,
real ProtoBuf serialize/deserialize and Android B01–B05. The pinned upstream
`BackupRestorer.kt` remains unchanged; PR #1 stays DRAFT and issues #2, #10,
#11 stay OPEN.
