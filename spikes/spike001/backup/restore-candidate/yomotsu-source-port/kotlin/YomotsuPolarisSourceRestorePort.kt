package polaris.spike001.backup.restore.yomotsu

import app.cash.sqldelight.async.coroutines.awaitAsList
import eu.kanade.tachiyomi.data.backup.models.BackupCategory
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.restore.restorers.MangaRestorer
import polaris.spike001.backup.restore.PolarisSourceRestorePort
import tachiyomi.data.Database

/**
 * Staged adapter for Yomotsu's real MangaRestorer and SQLDelight generated queries.
 * Caller must invoke strictRestoreRequiredOrdinaryOrThrow() AFTER the stock normal
 * restore has completed, BEFORE PolarisRestoreCoordinator commits virtual parents.
 *
 * Stock BackupRestorer can swallow failed MangaRestorer entries. Re-running only
 * linked/required source snapshots strictly ensures their exceptions propagate.
 * This is deliberately opt-in for Polaris and is not yet wired to Android.
 */
class YomotsuPolarisSourceRestorePort(
    private val mangaRestorer: MangaRestorer,
    private val database: Database,
    private val restoredCategories: List<BackupCategory>,
) : PolarisSourceRestorePort {
    companion object { private const val VIRTUAL_SOURCE_ID = 6969L }

    /** Verified retry for the required ordinary child snapshots only. */
    suspend fun strictRestoreRequiredOrdinaryOrThrow(
        ordinary: List<BackupManga>,
        requiredResolvedKeys: Set<Pair<Long, String>>,
    ) {
        val byIdentity = ordinary.groupBy { it.source to it.url }
        for (key in requiredResolvedKeys) {
            val matching = byIdentity[key].orEmpty()
            if (matching.isEmpty()) continue // supplemental snapshot is handled separately
            check(matching.size == 1) { "Ambiguous ordinary source snapshot" }
            strictRestoreAndVerify(matching.single())
        }
    }

    override suspend fun restoreSupplementalMangaOrThrow(snapshot: BackupManga) {
        strictRestoreAndVerify(snapshot)
    }

    override suspend fun findMangaIdsBySourceAndUrl(sourceId: Long, sourceUrl: String): List<Long> {
        require(sourceId != VIRTUAL_SOURCE_ID && sourceUrl.isNotBlank())
        return database.polarisRestoreQueries.selectAllExactSourceChildIds(sourceId, sourceUrl).awaitAsList()
    }

    private suspend fun strictRestoreAndVerify(snapshot: BackupManga) {
        require(snapshot.source != VIRTUAL_SOURCE_ID && snapshot.url.isNotBlank()) {
            "Polaris cannot restore a virtual manga as a real source child"
        }
        val chapterUrls = snapshot.chapters.map { it.url }
        require(chapterUrls.all { it.isNotBlank() } && chapterUrls.size == chapterUrls.distinct().size) {
            "Incomplete or ambiguous backed-up chapter identities"
        }
        // MangaRestorer.restore() itself wraps manga+chapters+categories+history+
        // tracking in one DB transaction and throws on hard errors. Do NOT use
        // GetChaptersByMangaId.await(), which catches DB exceptions and returns [].
        mangaRestorer.restore(snapshot, restoredCategories)
        val ids = findMangaIdsBySourceAndUrl(snapshot.source, snapshot.url)
        check(ids.size == 1 && ids.single() > 0L) {
            "Restored real child is absent or has ambiguous source+URL"
        }
        val mangaId = ids.single()
        val rows = database.chaptersQueries.getChaptersByMangaId(mangaId, false).awaitAsList()
        val byUrl = rows.groupBy { it.url }
        for (chapter in snapshot.chapters) {
            val matches = byUrl[chapter.url].orEmpty()
            check(matches.size == 1) { "Expected chapter URL missing or ambiguous after source restore" }
            val actual = matches.single()
            check(!chapter.read || actual.read) { "Restored chapter lost backed-up read state" }
            check(!chapter.bookmark || actual.bookmark) { "Restored chapter lost backed-up bookmark" }
            check(actual.last_page_read >= chapter.lastPageRead) { "Restored chapter lost backed-up page progress" }
        }
    }
}
