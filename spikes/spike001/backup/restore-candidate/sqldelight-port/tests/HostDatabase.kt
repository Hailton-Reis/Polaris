package tachiyomi.data

import kotlinx.serialization.json.JsonObject

class Query<T>(val fetch:()->List<T>)
data class MangaRow(val id:Long,val source:Long,val url:String,val title:String,val memo:JsonObject)
data class LedgerRow(val parent_manga_id:Long,val archive_digest:String)
data class EdgeRow(val info_manga:Boolean,val get_chapter_updates:Boolean,val chapter_sort_mode:Long,val chapter_priority:Long,val download_chapters:Boolean,val manga_id:Long?,val manga_url:String,val manga_source:Long,val merge_url:String,val merge_id:Long)
class FakeRestoreQueries {
  val mangas=linkedMapOf<Long,MangaRow>()
  val ledgers=linkedMapOf<String,LedgerRow>()
  val edges=mutableListOf<EdgeRow>()
  var nextId=900L
  var failAtEdge = -1
  fun selectLedgerForUuid(archiveUuid:String)=Query { listOfNotNull(ledgers[archiveUuid]) }
  fun selectAllVirtualUuidMemos()=Query { mangas.values.filter{it.source==6969L}.toList() }
  fun selectVirtualParentById(parentId:Long)=Query { listOfNotNull(mangas[parentId]) }
  fun selectVirtualParentByUrl(parentUrl:String)=Query { mangas.values.filter{it.source==6969L&&it.url==parentUrl}.map{it.id} }
  fun selectAllExactSourceChildIds(sourceId:Long,sourceUrl:String)=Query { mangas.values.filter{it.source==sourceId&&it.url==sourceUrl}.map{it.id} }
  fun selectRestoredParentEdges(parentId:Long)=Query { edges.filter{it.merge_id==parentId}.toList() }
  fun insertNewRestoredParent(parentUrl:String,parentTitle:String,memo:JsonObject):Query<Long> {
    check(mangas.values.none{it.source==6969L&&it.url==parentUrl})
    val id=nextId++
    mangas[id]=MangaRow(id,6969L,parentUrl,parentTitle,memo)
    return Query { listOf(id) }
  }
  fun insertArchiveLedger(archiveUuid:String,parentId:Long,archiveDigest:String) {
    check(ledgers[archiveUuid]==null && ledgers.values.none{it.parent_manga_id==parentId})
    ledgers[archiveUuid]=LedgerRow(parentId,archiveDigest)
  }
  fun insertRestoredEdge(infoManga:Boolean,getChapterUpdates:Boolean,chapterSortMode:Long,chapterPriority:Long,downloadChapters:Boolean,parentId:Long,parentUrl:String,mangaId:Long?,mangaUrl:String,mangaSource:Long) {
    if (failAtEdge==edges.size) error("Injected SQL constraint failure")
    check(edges.none{it.merge_id==parentId && it.manga_source==mangaSource && it.manga_url==mangaUrl})
    check(edges.none{it.merge_id==parentId && mangaId!=null && it.manga_id==mangaId})
    if(mangaId!=null)check(mangas.containsKey(mangaId))
    edges+=EdgeRow(infoManga,getChapterUpdates,chapterSortMode,chapterPriority,downloadChapters,mangaId,mangaUrl,mangaSource,parentUrl,parentId)
  }
  data class Snapshot(val mangas:LinkedHashMap<Long,MangaRow>,val ledgers:LinkedHashMap<String,LedgerRow>,val edges:List<EdgeRow>,val id:Long)
  fun save()=Snapshot(LinkedHashMap(mangas),LinkedHashMap(ledgers),edges.toList(),nextId)
  fun restore(s:Snapshot){mangas.clear();mangas.putAll(s.mangas);ledgers.clear();ledgers.putAll(s.ledgers);edges.clear();edges.addAll(s.edges);nextId=s.id}
}
class Database(val polarisRestoreQueries:FakeRestoreQueries=FakeRestoreQueries()) {
  suspend fun transaction(block:suspend ()->Unit) {
    val snapshot=polarisRestoreQueries.save()
    try{block()}catch(e:Throwable){polarisRestoreQueries.restore(snapshot);throw e}
  }
}
