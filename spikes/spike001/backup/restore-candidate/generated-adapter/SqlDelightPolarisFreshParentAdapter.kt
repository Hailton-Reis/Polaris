package polaris.spike001.backup.restore

import app.cash.sqldelight.async.coroutines.awaitAsList
import app.cash.sqldelight.async.coroutines.awaitAsOne
import app.cash.sqldelight.async.coroutines.awaitAsOneOrNull
import app.cash.sqldelight.db.SqlDriver
import eu.kanade.tachiyomi.data.backup.models.BackupCategory
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import tachiyomi.data.Database
import java.util.Date
import java.util.UUID

/**
 * R001 CANDIDATE, NOT PRODUCTION: wraps the staged generated query surface.
 * Requires merged.sq (migration 14), reviewed UUID ledger DDL and
 * PolarisParentMetadataRestore.sq added to the data module.
 * Do NOT connect to PolarisRestoreCoordinator until real SQLDelight/Android tests.
 * Only NEW virtual parents; never rewrites a user's existing placeholder.
 */
class SqlDelightPolarisFreshParentAdapter(
    private val database: Database,
    driver: SqlDriver,
) {
    data class LinkSettings(
        val infoManga: Boolean = false,
        val getChapterUpdates: Boolean = false,
        val chapterSortMode: Long = 2,
        val chapterPriority: Long,
        val downloadChapters: Boolean = false,
    )

    data class ChildLink(
        val sourceId: Long,
        val sourceUrl: String,
        val realMangaId: Long?, // null means deliberately pending
        val settings: LinkSettings,
    )

    data class FreshWork(
        val archiveUuid: String,
        val archiveDigest: String,
        val archive: BackupManga,
        val categoryIdsByArchiveOrder: Map<Long, Long>,
        val children: List<ChildLink>,
        val rootSettings: LinkSettings,
        val technical: PolarisBackupMangaSqlProjection.TechnicalState =
            PolarisBackupMangaSqlProjection.TechnicalState(),
        /** Full BackupCategory snapshots for the orders listed in archive.categories. */
        val archiveCategories: List<BackupCategory> = emptyList(),
    )

    private data class ExpectedEdge(
        val source: Long, val url: String, val mangaId: Long?, val settings: LinkSettings,
    )

    private val transaction = PolarisDeferredFkTransaction(database, driver)

    /** ONE transaction across all new parents and their associated physical rows. */
    suspend fun restoreNewOnly(works: List<FreshWork>): List<Long> {
        require(works.isNotEmpty()) { "POLARIS_FRESH_EMPTY_BATCH" }
        require(works.map { it.archiveUuid }.distinct().size == works.size) {
            "POLARIS_FRESH_DUPLICATE_UUID"
        }
        // The driver guard begins BEGIN IMMEDIATE before this block; every
        // query runs through the same coroutine-bound writer connection.
        return transaction.restoreNewParents {
            val parentIds = mutableListOf<Long>()
            works.forEach { work ->
                validateWork(work)
                val q = database.polarisParentMetadataRestoreQueries
                check(database.polarisRestoreQueries.selectLedgerForUuid(work.archiveUuid)
                    .awaitAsOneOrNull() == null) { "POLARIS_FRESH_UUID_ALREADY_RESTORED" }
                check(q.selectPolarisRestoreParentUrlCandidates(destinationUrl(work.archiveUuid))
                    .awaitAsList().isEmpty()) { "POLARIS_FRESH_PARENT_URL_COLLISION" }
                // Detect a legacy UUID memo without a ledger: no silent re-import.
                val preexisting = database.polarisRestoreQueries.selectAllVirtualUuidMemos().awaitAsList()
                check(preexisting.none { row ->
                    val raw = row.memo[PolarisBackupMangaSqlProjection.UUID_MEMO_KEY]
                    raw == JsonPrimitive(work.archiveUuid)
                }) { "POLARIS_FRESH_LEGACY_UUID_CLAIM" }
                val id = q.selectPolarisNextFreshParentId().awaitAsOne()
                check(id > 0L && id !in parentIds) { "POLARIS_FRESH_RESERVED_ID_CONFLICT" }
                check(database.mangasQueries.getMangaById(id).awaitAsOneOrNull() == null) {
                    "POLARIS_FRESH_RESERVED_ID_ALREADY_USED"
                }
                val prepared = PolarisBackupMangaSqlProjection.prepare(
                    work.archive, work.archiveUuid, id, work.categoryIdsByArchiveOrder, work.technical,
                )
                check(prepared.parent.reservedParentId == id &&
                    prepared.chapters.all { it.parentId == id }) { "POLARIS_FRESH_MISMATCHED_PREPARED_ID" }
                validatePhysicalChildren(work)
                validateArchiveCategories(work)
                val edges = expectedEdges(work, id)
                stageDependencies(id, work, prepared, edges)
                val p = prepared.parent
                val insertedId = q.insertPolarisRestoredReservedParentLast(
                    parentId = id, destinationUrl = p.destinationUrl,
                    artist = p.artist, author = p.author, description = p.description,
                    genre = p.genre, title = p.title, status = p.status,
                    thumbnailUrl = p.thumbnailUrl, favorite = p.favorite,
                    lastUpdate = p.lastUpdate, nextUpdate = p.nextUpdate,
                    initialized = p.initialized, viewer = p.viewer,
                    chapterFlags = p.chapterFlags, coverLastModified = p.coverLastModified,
                    dateAdded = p.dateAdded, updateStrategy = p.updateStrategy,
                    calculateInterval = p.calculateInterval, lastModifiedAt = p.lastModifiedAt,
                    favoriteModifiedAt = p.favoriteModifiedAt, version = p.version,
                    notes = p.notes, memo = p.memo,
                ).awaitAsOne()
                check(insertedId == id) { "POLARIS_FRESH_PARENT_LAST_ID_CHANGED" }
                assertExactRows(id, work, prepared, edges)
                parentIds += id
            }
            parentIds
        }
    }

    private fun destinationUrl(uuid: String) = "merged://polaris/$uuid"

    private fun validateWork(w: FreshWork) {
        val parsed = runCatching { UUID.fromString(w.archiveUuid) }.getOrNull()
        require(parsed?.toString() == w.archiveUuid) { "POLARIS_FRESH_NONCANONICAL_UUID" }
        require(Regex("[a-f0-9]{64}").matches(w.archiveDigest)) { "POLARIS_FRESH_BAD_DIGEST" }
        require(w.children.isNotEmpty() && w.archive.source == 6969L) { "POLARIS_FRESH_BAD_CHILDREN" }
        require(w.children.map { it.sourceId to it.sourceUrl }.distinct().size == w.children.size) {
            "POLARIS_FRESH_DUPLICATE_SOURCE_IDENTITY"
        }
        require(w.children.mapNotNull { it.realMangaId }.distinct().size ==
            w.children.count { it.realMangaId != null }) { "POLARIS_FRESH_DUPLICATE_REAL_CHILD_ID" }
        require(w.children.all { it.sourceId != 6969L && it.sourceUrl.isNotBlank() &&
            (it.realMangaId == null || it.realMangaId > 0) }) { "POLARIS_FRESH_INVALID_CHILD" }
        val settings = w.children.map { it.settings } + w.rootSettings
        require(settings.map { it.chapterPriority }.distinct().size == settings.size &&
            settings.all { it.chapterSortMode in 0L..4L }) { "POLARIS_FRESH_BAD_EDGE_ORDER" }
        require(!w.rootSettings.infoManga && !w.rootSettings.downloadChapters &&
            !w.rootSettings.getChapterUpdates) { "POLARIS_FRESH_INVALID_ROOT" }
        require(w.children.count { it.settings.infoManga } == 1) {
            "POLARIS_FRESH_INFO_SOURCE_CARDINALITY"
        }
    }

    private suspend fun validatePhysicalChildren(w: FreshWork) {
        val q = database.polarisParentMetadataRestoreQueries
        for (child in w.children) {
            val ids = q.selectPolarisRestoreRealChildCandidates(child.sourceId, child.sourceUrl)
                .awaitAsList()
            check(if (child.realMangaId == null) ids.isEmpty() else ids == listOf(child.realMangaId)) {
                "POLARIS_FRESH_SOURCE_IDENTITY_CHANGED"
            }
        }
        // Existing categories must be unambiguous and correspond to exactly
        // the expected physical IDs; names/order matching occurs upstream.
        for (catId in w.categoryIdsByArchiveOrder.values) {
            check(catId > 0L) { "POLARIS_FRESH_INVALID_CATEGORY_ID" }
        }
    }

    /**
     * Verify archive category ORDER -> archived NAME -> exactly one real local ID.
     * Merely checking an ID exists would silently attach a manga to a renamed or
     * unrelated user category. The snapshot list must come from the SAME decoded
     * backup as the BackupManga: never reconstruct it from local DB category IDs.
     * All queries run under the deferred-FK transaction before any category write.
     */
    private suspend fun validateArchiveCategories(w: FreshWork) {
        val expectedOrders = w.archive.categories.toSet()
        check(expectedOrders.size == w.archive.categories.size &&
            w.archiveCategories.size == expectedOrders.size &&
            w.archiveCategories.map { it.order }.toSet() == expectedOrders &&
            w.categoryIdsByArchiveOrder.keys == expectedOrders) {
            "POLARIS_FRESH_CATEGORY_ARCHIVE_ORDER_MISMATCH"
        }
        val names = w.archiveCategories.map { it.name }
        check(names.all { it.isNotBlank() } && names.toSet().size == names.size) {
            "POLARIS_FRESH_AMBIGUOUS_ARCHIVED_CATEGORY"
        }
        val q = database.polarisParentMetadataRestoreQueries
        for (archived in w.archiveCategories) {
            val id = requireNotNull(w.categoryIdsByArchiveOrder[archived.order]) {
                "POLARIS_FRESH_CATEGORY_MAPPING_MISSING"
            }
            check(id > 0L && q.selectPolarisRestoreCategoryCandidates(archived.name)
                .awaitAsList() == listOf(id)) {
                "POLARIS_FRESH_CATEGORY_NAME_OR_ID_CHANGED"
            }
        }
    }

    private fun expectedEdges(w: FreshWork, parentId: Long): List<ExpectedEdge> {
        val url = destinationUrl(w.archiveUuid)
        return w.children.map { ExpectedEdge(it.sourceId, it.sourceUrl, it.realMangaId, it.settings) } +
            ExpectedEdge(6969L, url, parentId, w.rootSettings)
    }

    private suspend fun stageDependencies(
        id: Long,
        work: FreshWork,
        prepared: PolarisBackupMangaSqlProjection.Prepared,
        edges: List<ExpectedEdge>,
    ) {
        val q = database.polarisParentMetadataRestoreQueries
        prepared.categories.forEach { q.insertPolarisRestoredCategoryExact(id, it) }
        val chapterIds = mutableMapOf<String, Long>()
        prepared.chapters.forEach { chapter ->
            check(chapter.parentId == id) { "POLARIS_FRESH_CHAPTER_PARENT_MISMATCH" }
            val chapterId = q.insertPolarisRestoredChapterFull(
                parentId = id, chapterUrl = chapter.url, chapterName = chapter.name,
                scanlator = chapter.scanlator, read = chapter.read,
                bookmark = chapter.bookmark, lastPageRead = chapter.lastPageRead,
                chapterNumber = chapter.chapterNumber, sourceOrder = chapter.sourceOrder,
                dateFetch = chapter.dateFetch, dateUpload = chapter.dateUpload,
                chapterLastModifiedAt = chapter.lastModifiedAt, chapterVersion = chapter.version,
                chapterIsSyncing = chapter.isSyncing, chapterMemo = chapter.memo,
            ).awaitAsOne()
            check(chapterId > 0L && chapterId !in chapterIds.values) { "POLARIS_FRESH_CHAPTER_ID_CONFLICT" }
            chapterIds[chapter.url] = chapterId
        }
        prepared.history.forEach { h ->
            val chapterId = requireNotNull(chapterIds[h.chapterUrl]) { "POLARIS_FRESH_HISTORY_ORPHAN" }
            q.insertPolarisRestoredHistoryExact(chapterId, Date(h.lastRead), h.readDuration)
        }
        prepared.tracking.forEach { t ->
            check(t.parentId == id) { "POLARIS_FRESH_TRACK_PARENT_MISMATCH" }
            q.insertPolarisRestoredTrackExact(
                parentId = id, syncId = t.syncId, remoteId = t.remoteId,
                libraryId = t.libraryId, trackTitle = t.title,
                lastChapterRead = t.lastChapterRead, totalChapters = t.totalChapters,
                trackStatus = t.status, trackScore = t.score, remoteUrl = t.remoteUrl,
                startDate = t.startDate, finishDate = t.finishDate, isPrivate = t.private,
            )
        }
        prepared.excludedScanlators.forEach { q.insertPolarisRestoredExclusionExact(id, it) }
        edges.forEach { e ->
            val s = e.settings
            val created = database.mergedQueries.insertReturningId(
                infoManga = s.infoManga, getChapterUpdates = s.getChapterUpdates,
                chapterSortMode = s.chapterSortMode, chapterPriority = s.chapterPriority,
                downloadChapters = s.downloadChapters, mergeId = id,
                mergeUrl = destinationUrl(work.archiveUuid), mangaId = e.mangaId,
                mangaUrl = e.url, mangaSource = e.source,
            ).awaitAsOneOrNull()
            check(created != null && created > 0) { "POLARIS_FRESH_SILENT_EDGE_DEDUP" }
        }
        database.polarisRestoreQueries.insertArchiveLedger(work.archiveUuid, id, work.archiveDigest)
    }

    private suspend fun assertExactRows(
        id: Long,
        work: FreshWork,
        prepared: PolarisBackupMangaSqlProjection.Prepared,
        edges: List<ExpectedEdge>,
    ) {
        val q = database.polarisParentMetadataRestoreQueries
        val p = prepared.parent
        val stored = q.selectPolarisRestoredParentFull(id).awaitAsOne()
        check(stored._id == id && stored.source == 6969L && stored.url == p.destinationUrl &&
            stored.artist == p.artist && stored.author == p.author && stored.description == p.description &&
            stored.genre == p.genre && stored.title == p.title && stored.status == p.status &&
            stored.thumbnail_url == p.thumbnailUrl && stored.favorite == p.favorite &&
            stored.last_update == p.lastUpdate && stored.next_update == p.nextUpdate &&
            stored.initialized == p.initialized && stored.viewer == p.viewer &&
            stored.chapter_flags == p.chapterFlags && stored.cover_last_modified == p.coverLastModified &&
            stored.date_added == p.dateAdded && stored.update_strategy == p.updateStrategy &&
            stored.calculate_interval == p.calculateInterval && stored.last_modified_at == p.lastModifiedAt &&
            stored.favorite_modified_at == p.favoriteModifiedAt && stored.version == p.version &&
            stored.is_syncing == 0L && stored.notes == p.notes && stored.memo == p.memo) {
            "POLARIS_FRESH_PARENT_READBACK_DRIFT"
        }
        val chapters = q.selectPolarisParentChaptersFull(id).awaitAsList()
        check(chapters.size == prepared.chapters.size &&
            chapters.map { it.url }.toSet().size == chapters.size) { "POLARIS_FRESH_CHAPTER_COUNT_DRIFT" }
        val chaptersByUrl = chapters.associateBy { it.url }
        prepared.chapters.forEach { c ->
            val actual = chaptersByUrl[c.url]
            check(actual != null && actual.manga_id == id && actual.name == c.name &&
                actual.scanlator == c.scanlator && actual.read == c.read && actual.bookmark == c.bookmark &&
                actual.last_page_read == c.lastPageRead && actual.chapter_number == c.chapterNumber &&
                actual.source_order == c.sourceOrder && actual.date_fetch == c.dateFetch &&
                actual.date_upload == c.dateUpload && actual.last_modified_at == c.lastModifiedAt &&
                actual.version == c.version && actual.is_syncing == c.isSyncing && actual.memo == c.memo) {
                "POLARIS_FRESH_CHAPTER_READBACK_DRIFT"
            }
        }
        val history = q.selectPolarisParentHistoryFull(id).awaitAsList()
        check(history.size == prepared.history.size &&
            history.map { it.chapter_url }.toSet().size == history.size) { "POLARIS_FRESH_HISTORY_COUNT_DRIFT" }
        val hByUrl = history.associateBy { it.chapter_url }
        prepared.history.forEach { h ->
            val row = hByUrl[h.chapterUrl]
            check(row != null && row.chapter_id == chaptersByUrl[h.chapterUrl]?._id &&
                row.last_read?.time == h.lastRead && row.time_read == h.readDuration) {
                "POLARIS_FRESH_HISTORY_READBACK_DRIFT"
            }
        }
        val tracking = q.selectPolarisParentTrackingFull(id).awaitAsList()
        check(tracking.size == prepared.tracking.size &&
            tracking.map { it.sync_id }.toSet().size == tracking.size) { "POLARIS_FRESH_TRACK_COUNT_DRIFT" }
        val trackBySync = tracking.associateBy { it.sync_id }
        prepared.tracking.forEach { t ->
            val row = trackBySync[t.syncId]
            check(row != null && row.manga_id == id && row.remote_id == t.remoteId &&
                row.library_id == t.libraryId && row.title == t.title &&
                row.last_chapter_read == t.lastChapterRead && row.total_chapters == t.totalChapters &&
                row.status == t.status && row.score == t.score && row.remote_url == t.remoteUrl &&
                row.start_date == t.startDate && row.finish_date == t.finishDate && row.private == t.private) {
                "POLARIS_FRESH_TRACK_READBACK_DRIFT"
            }
        }
        val categories = q.selectPolarisParentCategoriesFull(id).awaitAsList().map { it.category_id }
        check(categories.size == prepared.categories.size &&
            categories.sorted() == prepared.categories.sorted()) { "POLARIS_FRESH_CATEGORY_READBACK_DRIFT" }
        val excluded = q.selectPolarisParentExclusionsFull(id).awaitAsList().map { it.scanlator }
        check(excluded.size == prepared.excludedScanlators.size &&
            excluded.sorted() == prepared.excludedScanlators.sorted()) { "POLARIS_FRESH_EXCLUSION_READBACK_DRIFT" }
        val actualEdges = q.selectPolarisParentEdgesFull(id).awaitAsList()
        check(actualEdges.size == edges.size &&
            actualEdges.map { it.chapter_priority }.toSet().size == edges.size) {
            "POLARIS_FRESH_EDGE_COUNT_DRIFT"
        }
        val actualByPriority = actualEdges.associateBy { it.chapter_priority }
        edges.forEach { e ->
            val s = e.settings
            val row = actualByPriority[s.chapterPriority]
            check(row != null && row.info_manga == s.infoManga &&
                row.get_chapter_updates == s.getChapterUpdates &&
                row.chapter_sort_mode == s.chapterSortMode &&
                row.download_chapters == s.downloadChapters &&
                row.merge_id == id && row.merge_url == p.destinationUrl &&
                row.manga_id == e.mangaId && row.manga_url == e.url && row.manga_source == e.source) {
                "POLARIS_FRESH_EDGE_READBACK_DRIFT"
            }
        }
        val ledger = database.polarisRestoreQueries.selectLedgerForUuid(work.archiveUuid).awaitAsOne()
        check(ledger.parent_manga_id == id && ledger.archive_digest == work.archiveDigest) {
            "POLARIS_FRESH_LEDGER_READBACK_DRIFT"
        }
    }
}
