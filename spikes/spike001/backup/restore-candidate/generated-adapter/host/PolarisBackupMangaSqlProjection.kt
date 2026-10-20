package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.source.model.UpdateStrategy
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import tachiyomi.data.MemoColumnAdapter
import tachiyomi.data.StringListColumnAdapter

/**
 * R001 STAGING ONLY. Converts the EXACT pinned Yomotsu BackupManga data types
 * into typed fields for the SQLDelight `PolarisParentMetadataRestore.sq` surface.
 * It deliberately does not write to the database or authorize v2 import.
 *
 * The destination URL is UUID-stable and is NOT the archive's source URL.
 * Category IDs below are local IDs, obtained via ARCHIVE ORDER -> NAME -> ID.
 * Never use normal MangaRestorer upserts for chapters/history/tracks here.
 */
object PolarisBackupMangaSqlProjection {
    const val VIRTUAL_SOURCE: Long = 6969L
    const val UUID_MEMO_KEY = "polaris.merge.work.uuid"

    /** Not present in BackupManga, so these destination-only technical fields need explicit policy. */
    data class TechnicalState(
        val lastUpdate: Long? = null,
        val nextUpdate: Long? = null,
        val coverLastModified: Long = 0L,
        val calculateInterval: Long = 0L,
    )

    data class ParentRow(
        val reservedParentId: Long,
        val source: Long,
        val destinationUrl: String,
        val artist: String?,
        val author: String?,
        val description: String?,
        val genre: List<String>,
        val title: String,
        val status: Long,
        val thumbnailUrl: String?,
        val favorite: Boolean,
        val lastUpdate: Long?,
        val nextUpdate: Long?,
        val initialized: Boolean,
        val viewer: Long,
        val chapterFlags: Long,
        val coverLastModified: Long,
        val dateAdded: Long,
        val updateStrategy: UpdateStrategy,
        val calculateInterval: Long,
        val lastModifiedAt: Long,
        val favoriteModifiedAt: Long?,
        val version: Long,
        val isSyncing: Long,
        val notes: String,
        val memo: JsonObject,
    )
    data class ChapterRow(
        val parentId: Long,
        val url: String,
        val name: String,
        val scanlator: String?,
        val read: Boolean,
        val bookmark: Boolean,
        val lastPageRead: Long,
        val chapterNumber: Double,
        val sourceOrder: Long,
        val dateFetch: Long,
        val dateUpload: Long,
        val lastModifiedAt: Long,
        val version: Long,
        val isSyncing: Long,
        val memo: JsonObject,
    )
    data class HistoryRow(val chapterUrl: String, val lastRead: Long, val readDuration: Long)
    data class TrackingRow(
        val parentId: Long,
        val syncId: Long,
        val remoteId: Long,
        val libraryId: Long,
        val title: String,
        val lastChapterRead: Double,
        val totalChapters: Long,
        val status: Long,
        val score: Double,
        val remoteUrl: String,
        val startDate: Long,
        val finishDate: Long,
        val private: Boolean,
    )
    data class Prepared(
        val parent: ParentRow,
        val chapters: List<ChapterRow>,
        val categories: List<Long>,
        val history: List<HistoryRow>,
        val tracking: List<TrackingRow>,
        val excludedScanlators: List<String>,
    )

    fun prepare(
        archive: BackupManga,
        canonicalUuid: String,
        reservedParentId: Long,
        localCategoryIdByArchiveOrder: Map<Long, Long>,
        technical: TechnicalState = TechnicalState(),
    ): Prepared {
        require(reservedParentId > 0L) { "POLARIS_V2_INVALID_PARENT_ID" }
        require(archive.source == VIRTUAL_SOURCE) { "POLARIS_V2_NOT_VIRTUAL_PARENT" }
        require(archive.url.isNotBlank() && archive.title.isNotBlank()) { "POLARIS_V2_INVALID_ARCHIVED_PARENT" }
        val parsed = runCatching { java.util.UUID.fromString(canonicalUuid) }.getOrNull()
        require(parsed != null && parsed.toString() == canonicalUuid) { "POLARIS_V2_NONCANONICAL_UUID" }
        require(archive.version >= 0 && archive.lastModifiedAt >= 0 && technical.coverLastModified >= 0 && technical.calculateInterval >= 0) {
            "POLARIS_V2_INVALID_PARENT_FIELDS"
        }
        // This exact adapter uses `", "`; certain distinct archive genre lists are not round-trippable.
        require(archive.genre.none { it.isBlank() } &&
            StringListColumnAdapter.decode(StringListColumnAdapter.encode(archive.genre)) == archive.genre) {
            "POLARIS_V2_GENRE_NOT_ROUNDTRIPPABLE"
        }
        val decodedParentMemo = MemoColumnAdapter.decode(archive.memo)
        val priorUuid = decodedParentMemo[UUID_MEMO_KEY]
        require(priorUuid == null || priorUuid == JsonPrimitive(canonicalUuid)) {
            "POLARIS_V2_CONFLICTING_MEMO_UUID"
        }
        // Only inject this one internal key; preserve all other arbitrary memo entries and values.
        val destinationMemo = JsonObject(decodedParentMemo + (UUID_MEMO_KEY to JsonPrimitive(canonicalUuid)))
        require(destinationMemo.size == decodedParentMemo.size + if (priorUuid == null) 1 else 0)
        val destinationUrl = "merged://polaris/$canonicalUuid"
        val categories = archive.categories
        require(categories.distinct().size == categories.size) { "POLARIS_V2_DUPLICATE_CATEGORY_ORDER" }
        require(categories.all { localCategoryIdByArchiveOrder[it]?.let { id -> id > 0L } == true }) {
            "POLARIS_V2_MISSING_CATEGORY_ORDER"
        }
        val destinationCategories = categories.map { localCategoryIdByArchiveOrder.getValue(it) }
        require(destinationCategories.distinct().size == destinationCategories.size) { "POLARIS_V2_CATEGORY_DESTINATION_COLLISION" }
        val urls = archive.chapters.map { it.url }
        require(urls.all { it.isNotBlank() } && urls.distinct().size == urls.size) {
            "POLARIS_V2_DUPLICATE_OR_EMPTY_CHAPTER_URL"
        }
        val chapters = archive.chapters.map { c ->
            require(c.name.isNotBlank() && c.chapterNumber.isFinite() && c.version >= 0 && c.lastModifiedAt >= 0 && c.lastPageRead >= 0) {
                "POLARIS_V2_INVALID_CHAPTER_FIELD"
            }
            ChapterRow(
                parentId = reservedParentId, url = c.url, name = c.name, scanlator = c.scanlator,
                read = c.read, bookmark = c.bookmark, lastPageRead = c.lastPageRead,
                chapterNumber = c.chapterNumber.toDouble(), sourceOrder = c.sourceOrder,
                dateFetch = c.dateFetch, dateUpload = c.dateUpload,
                lastModifiedAt = c.lastModifiedAt, version = c.version,
                isSyncing = 0L, memo = MemoColumnAdapter.decode(c.memo),
            )
        }
        val chapterUrls = urls.toSet()
        val historyUrls = archive.history.map { it.url }
        require(historyUrls.distinct().size == historyUrls.size && historyUrls.all { it in chapterUrls }) {
            "POLARIS_V2_UNRESOLVED_OR_DUPLICATE_HISTORY"
        }
        val history = archive.history.map { h ->
            require(h.readDuration >= 0 && h.lastRead >= 0) { "POLARIS_V2_INVALID_HISTORY_FIELD" }
            HistoryRow(h.url, h.lastRead, h.readDuration)
        }
        val syncIds = archive.tracking.map { it.syncId }
        require(syncIds.distinct().size == syncIds.size) { "POLARIS_V2_DUPLICATE_TRACKER_ID" }
        val tracking = archive.tracking.map { t ->
            @Suppress("DEPRECATION")
            val oldId = t.mediaIdInt
            require(oldId == 0 || t.mediaId == 0L || t.mediaId == oldId.toLong()) {
                "POLARIS_V2_CONFLICTING_TRACK_MEDIA_IDS"
            }
            require(t.lastChapterRead.isFinite() && t.score.isFinite() && t.libraryId >= 0 &&
                t.totalChapters >= 0 && t.syncId >= 0) { "POLARIS_V2_INVALID_TRACK_FIELDS" }
            val remote = if (oldId != 0) oldId.toLong() else t.mediaId
            TrackingRow(
                reservedParentId, t.syncId.toLong(), remote, t.libraryId, t.title,
                t.lastChapterRead.toDouble(), t.totalChapters.toLong(), t.status.toLong(),
                t.score.toDouble(), t.trackingUrl, t.startedReadingDate, t.finishedReadingDate, t.private,
            )
        }
        require(archive.excludedScanlators.distinct().size == archive.excludedScanlators.size &&
            archive.excludedScanlators.all { it.isNotBlank() }) { "POLARIS_V2_INVALID_SCANLATOR_EXCLUSIONS" }
        val parent = ParentRow(
            reservedParentId, VIRTUAL_SOURCE, destinationUrl,
            archive.artist, archive.author, archive.description, archive.genre.toList(), archive.title,
            archive.status.toLong(), archive.thumbnailUrl, archive.favorite,
            technical.lastUpdate, technical.nextUpdate, archive.initialized,
            (archive.viewer_flags ?: archive.viewer).toLong(), archive.chapterFlags.toLong(),
            technical.coverLastModified, archive.dateAdded, archive.updateStrategy,
            technical.calculateInterval, archive.lastModifiedAt, archive.favoriteModifiedAt,
            archive.version, 0L, archive.notes, destinationMemo,
        )
        return Prepared(parent, chapters, destinationCategories, history, tracking, archive.excludedScanlators.toList())
    }
}
