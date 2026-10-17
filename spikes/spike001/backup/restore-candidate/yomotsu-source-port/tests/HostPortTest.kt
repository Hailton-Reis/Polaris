package polaris.spike001.backup.restore.yomotsu

import eu.kanade.tachiyomi.data.backup.models.*
import eu.kanade.tachiyomi.data.backup.restore.restorers.MangaRestorer
import tachiyomi.data.Database
import kotlin.coroutines.*

fun <T> sync(block:suspend ()->T):T {
  var result: Result<T>? = null
  block.startCoroutine(object: Continuation<T> {
    override val context:CoroutineContext=EmptyCoroutineContext
    override fun resumeWith(x:Result<T>){ result=x }
  })
  return checkNotNull(result).getOrThrow()
}

fun main() {
 var counter=0
 fun test(name:String, block:()->Unit){ block();counter++;println("SOURCE_RESTORE_PASS $counter $name") }
 fun fail(block:()->Unit){ check(runCatching(block).isFailure) }
 fun env():Triple<YomotsuPolarisSourceRestorePort,Database,MangaRestorer> {
   val db=Database();val rest=MangaRestorer(db)
   return Triple(YomotsuPolarisSourceRestorePort(rest,db,emptyList()),db,rest)
 }
 fun backup(source:Long=11,url:String="/real",chapters:List<BackupChapter> = listOf(BackupChapter("/one",true,true,7))):BackupManga=BackupManga(source,url,chapters)
 test("supplemental snapshot strictly restored and validated") {val (a,_,r)=env();sync{a.restoreSupplementalMangaOrThrow(backup())};check(r.calls==1)}
 test("real manga source and URL returned exactly") {val (a,_,_)=env();sync{a.restoreSupplementalMangaOrThrow(backup())};check(sync{a.findMangaIdsBySourceAndUrl(11,"/real")}==listOf(100L))}
 test("missing chapter blocks completion") {val (a,_,r)=env();r.omitChapter=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("read state regression blocks completion") {val (a,_,r)=env();r.regressRead=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("bookmark regression blocks completion") {val (a,_,r)=env();r.regressBookmark=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("backed-up page progress regression blocks completion") {val (a,_,r)=env();r.regressProgress=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("duplicate chapter URL in local db blocks completion") {val (a,_,r)=env();r.chapterDuplicate=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("duplicate backed-up chapter URL refused before DB mutation") {val (a,_,r)=env();fail{sync{a.restoreSupplementalMangaOrThrow(backup(chapters=listOf(BackupChapter("x"),BackupChapter("x"))))}};check(r.calls==0)}
 test("empty chapter URL refused before DB mutation") {val (a,_,r)=env();fail{sync{a.restoreSupplementalMangaOrThrow(backup(chapters=listOf(BackupChapter(""))))}};check(r.calls==0)}
 test("ambiguous restored manga ID blocks completion") {val (a,_,r)=env();r.ambiguous=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("hard MangaRestorer failures throw") {val (a,_,r)=env();r.fail=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("database read exception propagates instead of returning empty list") {val (a,db,_)=env();db.chaptersQueries.fail=true;fail{sync{a.restoreSupplementalMangaOrThrow(backup())}}}
 test("virtual 6969 cannot restore as source child") {val (a,_,r)=env();fail{sync{a.restoreSupplementalMangaOrThrow(backup(6969))}};check(r.calls==0)}
 test("empty real source URL refused") {val (a,_,r)=env();fail{sync{a.restoreSupplementalMangaOrThrow(backup(url=""))}};check(r.calls==0)}
 test("ordinary required source retries only linked manga") {val (a,_,r)=env();sync{a.strictRestoreRequiredOrdinaryOrThrow(listOf(backup(),backup(22,"/irrelevant")),setOf(11L to "/real"))};check(r.calls==1)}
 test("unrelated ordinary failure ignored on linked-only strict retry") {val (a,_,r)=env();sync{a.strictRestoreRequiredOrdinaryOrThrow(listOf(backup(22,"/unrelated")),setOf(11L to "/real"))};check(r.calls==0)}
 test("ambiguous ordinary backup identities block strict retry") {val (a,_,r)=env();fail{sync{a.strictRestoreRequiredOrdinaryOrThrow(listOf(backup(),backup()),setOf(11L to "/real"))}};check(r.calls==0)}
 test("hard failure propagates during strict ordinary replay") {val (a,_,r)=env();r.fail=true;fail{sync{a.strictRestoreRequiredOrdinaryOrThrow(listOf(backup()),setOf(11L to "/real"))}}}
 test("unmodified chapter without read/progress state allowed") {val (a,_,_)=env();sync{a.restoreSupplementalMangaOrThrow(backup(chapters=listOf(BackupChapter("/one"))))}}
 test("several chapters validated") {val (a,_,_)=env();sync{a.restoreSupplementalMangaOrThrow(backup(chapters=listOf(BackupChapter("/one",true,true,3),BackupChapter("/two",false,true,0))))}}
 test("empty chapter list permits source without chapters") {val (a,_,_)=env();sync{a.restoreSupplementalMangaOrThrow(backup(chapters=emptyList()))}}
 test("pending-like lookup returns empty when no rows") {val (a,_,_)=env();check(sync{a.findMangaIdsBySourceAndUrl(44,"/missing")}.isEmpty())}
 test("invalid lookup identity rejected") {val (a,_,_)=env();fail{sync{a.findMangaIdsBySourceAndUrl(6969,"/x")}};fail{sync{a.findMangaIdsBySourceAndUrl(44,"")}}}
 println("POLARIS_YOMOTSU_SOURCE_RESTORE_PASS $counter")
}
