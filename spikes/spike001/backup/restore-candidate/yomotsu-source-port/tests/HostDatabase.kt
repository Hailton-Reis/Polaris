package tachiyomi.data
class Query<T>(val fetch: ()->List<T>)
data class ChapterRow(val url:String,val read:Boolean,val bookmark:Boolean,val last_page_read:Long)
class FakeRestoreQueries {
  val ids=mutableMapOf<Pair<Long,String>,MutableList<Long>>()
  fun selectAllExactSourceChildIds(sourceId:Long,sourceUrl:String) = Query { ids[sourceId to sourceUrl]?.toList().orEmpty() }
}
class FakeChaptersQueries {
  val chapters=mutableMapOf<Long,MutableList<ChapterRow>>()
  var fail=false
  fun getChaptersByMangaId(mangaId:Long,applyScanlatorFilter:Boolean) = Query {
    check(!fail) {"Database chapter query failed"}
    check(!applyScanlatorFilter)
    chapters[mangaId]?.toList().orEmpty()
  }
}
class Database(val polarisRestoreQueries:FakeRestoreQueries=FakeRestoreQueries(),val chaptersQueries:FakeChaptersQueries=FakeChaptersQueries())
