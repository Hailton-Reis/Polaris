package polaris.spike001.backup.restore.sqldelight

import app.cash.sqldelight.async.coroutines.awaitAsList
import app.cash.sqldelight.async.coroutines.awaitAsOne
import app.cash.sqldelight.async.coroutines.awaitAsOneOrNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import polaris.spike001.backup.restore.PolarisAtomicVirtualWorkPort
import polaris.spike001.backup.restore.RestoredPolarisWork
import tachiyomi.data.Database
import java.util.UUID

/**
 * R001 non-production candidate: written against pinned Yomotsu's Database,
 * its SQLDelight async await helpers and proposed polarisRestore.sq queries.
 * Requires a reviewed migration installing ledger and unique indexes.
 * Uncompiled against the actual Android SQLDelight generator at this stage.
 */
class SqlDelightPolarisAtomicVirtualWorkPort(
    private val database: Database,
) : PolarisAtomicVirtualWorkPort {
    private companion object {
        const val VIRTUAL_SOURCE = 6969L
        const val UUID_MEMO_KEY = "polaris.merge.work.uuid"
    }

    private data class Edge(
        val info: Boolean,
        val updates: Boolean,
        val sort: Long,
        val priority: Long,
        val download: Boolean,
        val mangaId: Long?,
        val mangaUrl: String,
        val mangaSource: Long,
        val mergeUrl: String,
    )

    override suspend fun commitAllOrThrow(works: List<RestoredPolarisWork>) {
        val uuids = works.map { it.archiveUuid }
        require(uuids.distinct().size == works.size) { "Two archive works share a parent UUID" }
        for (work in works) validate(work)

        // This is ONE transaction for every parent, not one per child/work.
        // SQLite must enforce the candidate UNIQUE indexes and FK constraints.
        database.transaction {
            for (work in works) {
                val q = database.polarisRestoreQueries
                val digest = PolarisRestoreDigest.of(work)
                val registered = q.selectLedgerForUuid(work.archiveUuid).awaitAsOneOrNull()
                if (registered != null) {
                    val parentId = registered.parent_manga_id
                    check(registered.archive_digest == digest) { "Archive UUID refers to different content" }
                    val parent = q.selectVirtualParentById(parentId).awaitAsOneOrNull()
                    check(parent != null && parent.source == VIRTUAL_SOURCE && parent.title == work.title) {
                        "Ledger parent was removed or modified"
                    }
                    check(memoUuid(parent.memo) == work.archiveUuid) { "Parent UUID memo disagrees with ledger" }
                    val expected = desiredEdges(work, parentId, parent.url)
                    val existing = q.selectRestoredParentEdges(parentId).awaitAsList().map {
                        Edge(it.info_manga, it.get_chapter_updates, it.chapter_sort_mode,
                             it.chapter_priority, it.download_chapters, it.manga_id,
                             it.manga_url, it.manga_source, it.merge_url)
                    }
                    // Compare complete row multiset, not just source names/count.
                    // This prevents replay from silently recreating an intentionally
                    // removed source or overwriting priority/flags.
                    check(existing.size == expected.size && existing.groupingBy { it }.eachCount() ==
                          expected.groupingBy { it }.eachCount()) {
                        "Virtual parent links changed since the original import"
                    }
                    continue
                }

                for (legacy in q.selectAllVirtualUuidMemos().awaitAsList()) {
                    check(memoUuid(legacy.memo) != work.archiveUuid) {
                        "UUID already exists on a parent without restore ledger; manual repair required"
                    }
                }
                for (link in work.children) {
                    if (link.realMangaId == null) continue
                    check(q.selectAllExactSourceChildIds(link.sourceId, link.sourceUrl)
                        .awaitAsList() == listOf(link.realMangaId)) {
                        "Real child source/URL does not identify exactly the restored manga"
                    }
                }

                val parentUrl = "merged://polaris/${work.archiveUuid}"
                check(q.selectVirtualParentByUrl(parentUrl).awaitAsList().isEmpty()) {
                    "Virtual parent URL already exists without an archive ledger"
                }
                val memo = JsonObject(mapOf(UUID_MEMO_KEY to JsonPrimitive(work.archiveUuid)))
                val parentId = q.insertNewRestoredParent(parentUrl, work.title, memo).awaitAsOne()
                check(parentId > 0L) { "Virtual parent insert did not produce a valid local ID" }
                q.insertArchiveLedger(work.archiveUuid, parentId, digest)
                desiredEdges(work, parentId, parentUrl).forEach { edge ->
                    q.insertRestoredEdge(
                        infoManga = edge.info, getChapterUpdates = edge.updates,
                        chapterSortMode = edge.sort, chapterPriority = edge.priority,
                        downloadChapters = edge.download, parentId = parentId,
                        parentUrl = edge.mergeUrl, mangaId = edge.mangaId,
                        mangaUrl = edge.mangaUrl, mangaSource = edge.mangaSource,
                    )
                }
            }
        }
    }

    private fun validate(work: RestoredPolarisWork) {
        val canonical = runCatching { UUID.fromString(work.archiveUuid).toString() }.getOrNull()
        require(canonical == work.archiveUuid) { "Noncanonical archive UUID" }
        require(work.title.isNotBlank() && work.children.isNotEmpty()) { "Invalid parent title/links" }
        require(!work.rootSettings.infoManga) { "Synthetic root cannot be metadata source" }
        require(work.children.count { it.settings.infoManga } <= 1) { "Two metadata source children" }
        val identities = work.children.map { it.sourceId to it.sourceUrl }
        require(identities.distinct().size == identities.size) { "Repeated child source+URL identity" }
        val resolvedIds = work.children.mapNotNull { it.realMangaId }
        require(resolvedIds.distinct().size == resolvedIds.size) { "Two child identities share one local manga ID" }
        for (link in work.children) {
            require(link.sourceId != VIRTUAL_SOURCE && link.sourceUrl.isNotBlank()) { "Invalid real child identity" }
            require(link.wasPending == (link.realMangaId == null)) { "Inconsistent pending/source-child ID" }
            require(link.realMangaId == null || link.realMangaId > 0L) { "Bad resolved local manga ID" }
            require(link.settings.chapterSortMode in 0L..4L) { "Invalid chapter sort mode" }
        }
        require(work.rootSettings.chapterSortMode in 0L..4L) { "Invalid root chapter sort" }
    }

    private fun desiredEdges(work: RestoredPolarisWork, parentId: Long, parentUrl: String): List<Edge> =
        work.children.map { link ->
            Edge(link.settings.infoManga, link.settings.getChapterUpdates,
                 link.settings.chapterSortMode, link.settings.chapterPriority,
                 link.settings.downloadChapters, link.realMangaId, link.sourceUrl,
                 link.sourceId, parentUrl)
        } + Edge(
            work.rootSettings.infoManga, work.rootSettings.getChapterUpdates,
            work.rootSettings.chapterSortMode, work.rootSettings.chapterPriority,
            work.rootSettings.downloadChapters, parentId, parentUrl, VIRTUAL_SOURCE,
            parentUrl,
        )

    private fun memoUuid(memo: JsonObject): String? {
        val raw = memo[UUID_MEMO_KEY] ?: return null
        val value = raw as? JsonPrimitive
        require(value != null && value.isString) { "Invalid UUID memo type" }
        return value.content
    }
}
