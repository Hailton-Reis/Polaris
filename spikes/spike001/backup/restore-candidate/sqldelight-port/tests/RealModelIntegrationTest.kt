package polaris.spike001.backup.restore.sqldelight

import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.restore.*
import kotlinx.serialization.json.JsonObject
import tachiyomi.data.Database
import tachiyomi.data.MangaRow
import kotlin.coroutines.*

private val UUID_A = "123e4567-e89b-42d3-a456-426614174000"
private val UUID_B = "123e4567-e89b-42d3-a456-426614174001"
private val cfg = BackupPolarisMergeSettings(false,true,2,4,false)
private val root = BackupPolarisMergeSettings(false,false,2,2147483647,false)
private var passed = 0
private fun case(name:String, action:()->Unit){action();passed++;println("REAL_MODEL_E2E_PASS $passed $name")}
private fun fail(action:()->Unit){check(runCatching(action).isFailure)}
private fun <T> suspendNow(code:suspend ()->T):T {
 var answer:Result<T>?=null
 code.startCoroutine(object:Continuation<T>{override val context=EmptyCoroutineContext;override fun resumeWith(result:Result<T>){answer=result}})
 return checkNotNull(answer).getOrThrow()
}
private fun link(source:Long,url:String,pending:Boolean=false)=BackupPolarisLink(source,url,"Work $url",cfg,pending)
private fun work(uuid:String=UUID_A, links:List<BackupPolarisLink> = listOf(link(11,"/a"),link(12,"/b")))=
 BackupPolarisWork(uuid,"Virtual Work",root,links,uuid)
private fun bundle(works:List<BackupPolarisWork> = listOf(work()), extra:List<BackupManga> = listOf(BackupManga(12,"/b")))=
 BackupPolarisBundle(works=works,supplementalManga=extra)

private class RealSourcePort(val db:Database) : PolarisSourceRestorePort {
 val events=mutableListOf<String>()
 var failChild=false
 override suspend fun restoreSupplementalMangaOrThrow(snapshot:BackupManga){
  events+="restore:${snapshot.source}:${snapshot.url}"
  if(failChild)error("actual supplemental child restoration failed")
  val q=db.polarisRestoreQueries
  if(q.mangas.values.none{it.source==snapshot.source&&it.url==snapshot.url}){
   val id=if(snapshot.source==12L)202L else 203L
   q.mangas[id]=MangaRow(id,snapshot.source,snapshot.url,"Restored",JsonObject(emptyMap()))
  }
 }
 override suspend fun findMangaIdsBySourceAndUrl(sourceId:Long,sourceUrl:String):List<Long>{
  events+="lookup:$sourceId:$sourceUrl"
  return db.polarisRestoreQueries.mangas.values.filter{it.source==sourceId&&it.url==sourceUrl}.map{it.id}
 }
}
private fun setup():Pair<Database,RealSourcePort>{
 val db=Database()
 db.polarisRestoreQueries.mangas[101L]=MangaRow(101,11,"/a","Ordinary",JsonObject(emptyMap()))
 return db to RealSourcePort(db)
}
private fun restore(db:Database, sources:RealSourcePort, archive:BackupPolarisBundle?=bundle(), ordinary:List<BackupManga> = listOf(BackupManga(11,"/a")), enabled:Boolean=true, verify:suspend ()->Unit={sources.events+="ordinary-verified"}):List<RestoredPolarisWork> =
 suspendNow{ PolarisRestoreCoordinator(sources,SqlDelightPolarisAtomicVirtualWorkPort(db))
  .restore(archive,ordinary,enabled,verify) }

fun main(){
 case("real portable DTO -> child-first coordinator -> actual Kotlin parent adapter") {
  val(db,s)=setup();val works=restore(db,s)
  check(works.single().children.map{it.realMangaId}==listOf(101L,202L))
  check(s.events==listOf("ordinary-verified","restore:12:/b","lookup:11:/a","lookup:12:/b"))
  check(db.polarisRestoreQueries.ledgers.size==1&&db.polarisRestoreQueries.edges.size==3)
 }
 case("supplemental BackupManga restored before virtual work linking"){
  val(db,s)=setup();restore(db,s);check(db.polarisRestoreQueries.mangas.values.any{it.source==12L&&it.url=="/b"})
 }
 case("verified ordinary restore barrier failures never commit parents"){
  val(db,s)=setup();fail{restore(db,s,verify={error("ordinary backup had failures")})}
  check(s.events.isEmpty()&&db.polarisRestoreQueries.ledgers.isEmpty())
 }
 case("real source supplementary snapshot exception never commits parents"){
  val(db,s)=setup();s.failChild=true;fail{restore(db,s)}
  check(db.polarisRestoreQueries.ledgers.isEmpty()&&db.polarisRestoreQueries.edges.isEmpty())
 }
 case("backups without Polaris data leave merged table alone"){
  val(db,s)=setup();check(restore(db,s,archive=null).isEmpty());check(db.polarisRestoreQueries.ledgers.isEmpty())
 }
 case("disabled library entry import leaves database alone"){
  val(db,s)=setup();check(restore(db,s,enabled=false).isEmpty());check(db.polarisRestoreQueries.mangas.size==1)
 }
 case("portable archive unknown version fails BEFORE ordinary callback"){
  val(db,s)=setup();fail{restore(db,s,archive=bundle().copy(formatVersion=25))}
  check(s.events.isEmpty()&&db.polarisRestoreQueries.ledgers.isEmpty())
 }
 case("insufficient source snapshots fail preflight before any data writes"){
  val(db,s)=setup();fail{restore(db,s,archive=bundle(extra=emptyList()))}
  check(s.events.isEmpty()&&db.polarisRestoreQueries.edges.isEmpty())
 }
 case("explicitly pending source remains NULL and no artificial restoration"){
  val(db,s)=setup();val b=bundle(works=listOf(work(links=listOf(link(11,"/a"),link(12,"/pending",true)))),extra=emptyList())
  restore(db,s,b);check(db.polarisRestoreQueries.edges.single{it.manga_source==12L}.manga_id==null)
  check(s.events.none{it.startsWith("restore:")})
 }
 case("same archive imported twice is idempotent through coordinator"){
  val(db,s)=setup();restore(db,s);restore(db,s)
  check(db.polarisRestoreQueries.ledgers.size==1 && db.polarisRestoreQueries.edges.size==3)
 }
 case("manual unlink then archived replay never reattaches the source"){
  val(db,s)=setup();restore(db,s);db.polarisRestoreQueries.edges.removeAll{it.manga_source==12L}
  fail{restore(db,s)};check(db.polarisRestoreQueries.edges.size==2)
 }
 case("two portable virtual works are committed in a single parent transaction"){
  val(db,s)=setup();restore(db,s,archive=bundle(works=listOf(work(),work(UUID_B))))
  check(db.polarisRestoreQueries.ledgers.size==2 && db.polarisRestoreQueries.edges.size==6)
 }
 case("failure after second work insertion rolls back first virtual parent"){
  val(db,s)=setup();val q=db.polarisRestoreQueries;q.failAtEdge=3
  fail{restore(db,s,archive=bundle(works=listOf(work(),work(UUID_B))))}
  check(q.ledgers.isEmpty() && q.edges.isEmpty() && q.mangas.values.none{it.source==6969L})
 }
 case("UUID key tampering fails before restore, without guessing parent title"){
  val(db,s)=setup();val hacked=work().copy(canonicalUuid=UUID_B)
  fail{restore(db,s,archive=bundle(works=listOf(hacked)))}
  check(s.events.isEmpty()&&db.polarisRestoreQueries.ledgers.isEmpty())
 }
 case("duplicate real URL rows stop before parent transaction"){
  val(db,s)=setup();db.polarisRestoreQueries.mangas[301]=MangaRow(301,11,"/a","Dup",JsonObject(emptyMap()))
  fail{restore(db,s)};check(db.polarisRestoreQueries.ledgers.isEmpty())
 }
 case("restore settings from portable DTO preserved on real virtual edges"){
  val(db,s)=setup();restore(db,s)
  val q=db.polarisRestoreQueries
  check(q.edges.single{it.manga_source==11L}.chapter_priority==cfg.chapterPriority)
  check(q.edges.single{it.manga_source==6969L}.chapter_priority==root.chapterPriority)
 }
 println("POLARIS_REAL_MODEL_END_TO_END_PASS $passed")
}
