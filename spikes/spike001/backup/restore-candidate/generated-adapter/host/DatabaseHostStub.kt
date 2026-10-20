package tachiyomi.data

import eu.kanade.tachiyomi.source.model.UpdateStrategy
import kotlinx.serialization.json.JsonObject
import polaris.spike001.backup.restore.TestDriver
import java.util.Date

/** Host-only API shape double. Not generated code / actual SQLDelight. */
class Query<T>(val rows: suspend () -> List<T>)
fun <T> q(vararg values:T): Query<T> = Query { values.toList() }

class MangaRecord(
    val _id:Long,val source:Long,val url:String,val artist:String?,val author:String?,
    val description:String?,val genre:List<String>,val title:String,val status:Long,
    val thumbnail_url:String?,val favorite:Boolean,val last_update:Long?,val next_update:Long?,
    val initialized:Boolean,val viewer:Long,val chapter_flags:Long,val cover_last_modified:Long,
    val date_added:Long,val update_strategy:UpdateStrategy,val calculate_interval:Long,
    val last_modified_at:Long,val favorite_modified_at:Long?,val version:Long,
    val is_syncing:Long,val notes:String,val memo:JsonObject,
)
class ChapterRecord(
    val _id:Long,val manga_id:Long,val url:String,val name:String,val scanlator:String?,
    val read:Boolean,val bookmark:Boolean,val last_page_read:Long,val chapter_number:Double,
    val source_order:Long,val date_fetch:Long,val date_upload:Long,val last_modified_at:Long,
    val version:Long,val is_syncing:Long,val memo:JsonObject,
)
class HistoryRecord(val chapter_id:Long,val chapter_url:String,val last_read:Date?,val time_read:Long)
class TrackRecord(
    val manga_id:Long,val sync_id:Long,val remote_id:Long,val library_id:Long,
    val title:String,val last_chapter_read:Double,val total_chapters:Long,val status:Long,
    val score:Double,val remote_url:String,val start_date:Long,val finish_date:Long,val private:Boolean,
)
class EdgeRecord(
    val info_manga:Boolean,val get_chapter_updates:Boolean,val chapter_sort_mode:Long,
    val chapter_priority:Long,val download_chapters:Boolean,val merge_id:Long,
    val merge_url:String,val manga_id:Long?,val manga_url:String,val manga_source:Long,
)
class Ledger(val parent_manga_id:Long,val archive_digest:String)
class LegacyVirtual(val memo:JsonObject)
class CategoryRec(val category_id:Long)
class ExclusionRec(val scanlator:String)

class Database(val driver: TestDriver) {
    var parent:MangaRecord? = null
    val chapters = mutableListOf<ChapterRecord>()
    val categories = mutableListOf<CategoryRec>()
    val history = mutableListOf<HistoryRecord>()
    val tracks = mutableListOf<TrackRecord>()
    val exclusions = mutableListOf<ExclusionRec>()
    val edges = mutableListOf<EdgeRecord>()
    val ledger = mutableMapOf<String,Ledger>()
    var tamperParent = false
    var tamperHistory = false
    var tamperTrack = false
    var tamperEdge = false
    var tamperCategory = false
    var missingPhysicalChild = false
    var forceInsertParentFailure = false
    var nextId = 103L
    val polarisParentMetadataRestoreQueries=PolarisParentMetadataRestoreQueries(this)
    val mangasQueries=MangasQueries(this)
    val polarisRestoreQueries=PolarisRestoreQueries(this)
    val mergedQueries=MergedQueries(this)
    suspend fun <T> transactionWithResult(block: suspend ()->T):T {
        driver.begin()
        val oldParent=parent;val oldChapters=chapters.toList();val oldCategories=categories.toList()
        val oldHistory=history.toList();val oldTracks=tracks.toList()
        val oldExclusions=exclusions.toList();val oldEdges=edges.toList();val oldLedger=ledger.toMap()
        try { val result=block(); driver.commit(); return result }
        catch(t:Throwable) {
            parent=oldParent
            chapters.clear();chapters.addAll(oldChapters)
            categories.clear();categories.addAll(oldCategories)
            history.clear();history.addAll(oldHistory)
            tracks.clear();tracks.addAll(oldTracks)
            exclusions.clear();exclusions.addAll(oldExclusions)
            edges.clear();edges.addAll(oldEdges)
            ledger.clear();ledger.putAll(oldLedger)
            driver.rollback();throw t
        }
    }
}
class MangasQueries(private val db:Database){fun getMangaById(id:Long):Query<MangaRecord> = Query { listOfNotNull(db.parent?.takeIf { it._id==id }) }}
class PolarisRestoreQueries(private val db:Database){
    fun selectLedgerForUuid(archiveUuid:String):Query<Ledger> = Query {listOfNotNull(db.ledger[archiveUuid])}
    fun selectAllVirtualUuidMemos():Query<LegacyVirtual> = Query {db.parent?.let {listOf(LegacyVirtual(it.memo))}?:emptyList()}
    fun insertArchiveLedger(archiveUuid:String,parentId:Long,archiveDigest:String){db.ledger[archiveUuid]=Ledger(parentId,archiveDigest)}
}
class MergedQueries(private val db:Database){
    fun insertReturningId(infoManga:Boolean,getChapterUpdates:Boolean,chapterSortMode:Long,
        chapterPriority:Long,downloadChapters:Boolean,mergeId:Long,mergeUrl:String,
        mangaId:Long?,mangaUrl:String,mangaSource:Long):Query<Long> = Query {
        val e=EdgeRecord(infoManga,getChapterUpdates,chapterSortMode,chapterPriority,
            downloadChapters,mergeId,mergeUrl,mangaId,mangaUrl,mangaSource)
        db.edges.add(e);listOf(db.edges.size.toLong())
    }
}
class PolarisParentMetadataRestoreQueries(private val db:Database) {
    fun selectPolarisRestoreParentUrlCandidates(destinationUrl:String):Query<Long> = Query {
        db.parent?.takeIf { it.url==destinationUrl }?.let {listOf(it._id)}?:emptyList()
    }
    fun selectPolarisNextFreshParentId():Query<Long> = q(db.nextId)
    fun selectPolarisRestoreRealChildCandidates(childSource:Long,childUrl:String):Query<Long> = Query {
        if(db.missingPhysicalChild) emptyList()
        else if(childSource==77L && childUrl=="/real-101") listOf(101L) else emptyList()
    }
    fun insertPolarisRestoredCategoryExact(parentId:Long,categoryId:Long){db.categories.add(CategoryRec(categoryId))}
    fun insertPolarisRestoredChapterFull(parentId:Long,chapterUrl:String,chapterName:String,
        scanlator:String?,read:Boolean,bookmark:Boolean,lastPageRead:Long,chapterNumber:Double,
        sourceOrder:Long,dateFetch:Long,dateUpload:Long,chapterLastModifiedAt:Long,
        chapterVersion:Long,chapterIsSyncing:Long,chapterMemo:JsonObject):Query<Long> = Query {
        val id=200L+db.chapters.size;db.chapters.add(ChapterRecord(id,parentId,chapterUrl,chapterName,
            scanlator,read,bookmark,lastPageRead,chapterNumber,sourceOrder,dateFetch,dateUpload,
            chapterLastModifiedAt,chapterVersion,chapterIsSyncing,chapterMemo));listOf(id)
    }
    fun insertPolarisRestoredHistoryExact(chapterId:Long,lastRead:Date,readDuration:Long){
        val chapter=db.chapters.single {it._id==chapterId}
        db.history.add(HistoryRecord(chapterId,chapter.url,lastRead,readDuration))
    }
    fun insertPolarisRestoredTrackExact(parentId:Long,syncId:Long,remoteId:Long,libraryId:Long,
        trackTitle:String,lastChapterRead:Double,totalChapters:Long,trackStatus:Long,trackScore:Double,
        remoteUrl:String,startDate:Long,finishDate:Long,isPrivate:Boolean){
        db.tracks.add(TrackRecord(parentId,syncId,remoteId,libraryId,trackTitle,lastChapterRead,
            totalChapters,trackStatus,trackScore,remoteUrl,startDate,finishDate,isPrivate))
    }
    fun insertPolarisRestoredExclusionExact(parentId:Long,excludedScanlator:String){db.exclusions.add(ExclusionRec(excludedScanlator))}
    fun insertPolarisRestoredReservedParentLast(parentId:Long,destinationUrl:String,artist:String?,
        author:String?,description:String?,genre:List<String>,title:String,status:Long,
        thumbnailUrl:String?,favorite:Boolean,lastUpdate:Long?,nextUpdate:Long?,initialized:Boolean,
        viewer:Long,chapterFlags:Long,coverLastModified:Long,dateAdded:Long,
        updateStrategy:UpdateStrategy,calculateInterval:Long,lastModifiedAt:Long,
        favoriteModifiedAt:Long?,version:Long,notes:String,memo:JsonObject):Query<Long> = Query {
        if(db.forceInsertParentFailure) error("SIMULATED_PARENT_INSERT_FAIL")
        db.parent=MangaRecord(parentId,6969L,destinationUrl,artist,author,description,genre,title,
            status,thumbnailUrl,favorite,lastUpdate,nextUpdate,initialized,viewer,chapterFlags,
            coverLastModified,dateAdded,updateStrategy,calculateInterval,lastModifiedAt,
            favoriteModifiedAt,version,0L,notes,memo)
        listOf(parentId)
    }
    fun selectPolarisRestoredParentFull(parentId:Long):Query<MangaRecord> = Query {
        db.parent?.takeIf {it._id==parentId}?.let {
            if(db.tamperParent) listOf(MangaRecord(it._id,it.source,it.url,it.artist,it.author,
                it.description,it.genre,it.title+" EDITED",it.status,it.thumbnail_url,it.favorite,
                it.last_update,it.next_update,it.initialized,it.viewer,it.chapter_flags,
                it.cover_last_modified,it.date_added,it.update_strategy,it.calculate_interval,
                it.last_modified_at,it.favorite_modified_at,it.version,it.is_syncing,it.notes,it.memo))
            else listOf(it)
        }?:emptyList()
    }
    fun selectPolarisParentChaptersFull(parentId:Long):Query<ChapterRecord> = Query {db.chapters.filter {it.manga_id==parentId}}
    fun selectPolarisParentHistoryFull(parentId:Long):Query<HistoryRecord> = Query {db.history.filter {h->db.chapters.any{it._id==h.chapter_id && it.manga_id==parentId}}.map{if(db.tamperHistory)HistoryRecord(it.chapter_id,it.chapter_url,it.last_read,it.time_read+1) else it}}
    fun selectPolarisParentTrackingFull(parentId:Long):Query<TrackRecord> = Query {db.tracks.filter {it.manga_id==parentId}.map{if(db.tamperTrack)TrackRecord(it.manga_id,it.sync_id,it.remote_id,it.library_id,it.title,it.last_chapter_read,it.total_chapters,it.status,it.score+1,it.remote_url,it.start_date,it.finish_date,it.private) else it}}
    fun selectPolarisParentCategoriesFull(parentId:Long):Query<CategoryRec> = Query {if(db.tamperCategory)emptyList() else db.categories.toList()}
    fun selectPolarisParentExclusionsFull(parentId:Long):Query<ExclusionRec> = Query {db.exclusions.toList()}
    fun selectPolarisParentEdgesFull(parentId:Long):Query<EdgeRecord> = Query {db.edges.filter {it.merge_id==parentId}.map{if(db.tamperEdge)EdgeRecord(it.info_manga,it.get_chapter_updates,it.chapter_sort_mode,it.chapter_priority+1,it.download_chapters,it.merge_id,it.merge_url,it.manga_id,it.manga_url,it.manga_source) else it}}
}
