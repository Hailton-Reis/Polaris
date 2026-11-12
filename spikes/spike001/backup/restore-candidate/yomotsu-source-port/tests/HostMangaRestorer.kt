package eu.kanade.tachiyomi.data.backup.restore.restorers
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupCategory
import tachiyomi.data.Database
import tachiyomi.data.ChapterRow

class MangaRestorer(private val db:Database) {
 var calls=0
 var fail=false
 var omitChapter=false
 var regressRead=false
 var regressBookmark=false
 var regressProgress=false
 var ambiguous=false
 var chapterDuplicate=false
 var rowId=100L
 suspend fun restore(snapshot:BackupManga,categories:List<BackupCategory>) {
  calls++
  if(fail) error("Original MangaRestorer hard failure")
  val key=snapshot.source to snapshot.url
  db.polarisRestoreQueries.ids[key]=if(ambiguous)mutableListOf(rowId,rowId+1) else mutableListOf(rowId)
  db.chaptersQueries.chapters[rowId] = snapshot.chapters.filterNot{omitChapter}.map{ch->
    ChapterRow(ch.url, ch.read && !regressRead, ch.bookmark && !regressBookmark,
               if(regressProgress) 0L else ch.lastPageRead)
  }.toMutableList().apply{if(chapterDuplicate&&isNotEmpty())add(first())}
 }
}
