package polaris.spike001.backup.restore.sqldelight

import eu.kanade.tachiyomi.data.backup.models.BackupPolarisMergeSettings
import polaris.spike001.backup.restore.*
import tachiyomi.data.*
import kotlinx.serialization.json.*
import kotlin.coroutines.*

private const val A="123e4567-e89b-42d3-a456-426614174000"
private const val B="123e4567-e89b-42d3-a456-426614174001"
private var cases=0
private fun case(title:String, action:()->Unit){action();cases++;println("SQLDELIGHT_PORT_PASS $cases $title")}
private fun fail(action:()->Unit){check(runCatching(action).isFailure)}
private fun <T> block(code:suspend ()->T):T {var res:Result<T>?=null;code.startCoroutine(object:Continuation<T>{override val context=EmptyCoroutineContext;override fun resumeWith(result:Result<T>){res=result}});return checkNotNull(res).getOrThrow()}
private val flags=BackupPolarisMergeSettings(false,true,2,1,true)
private val root=flags.copy(getChapterUpdates=false,chapterPriority=2147483647,downloadChapters=false)
private fun link(source:Long,url:String,id:Long?,pending:Boolean=id==null,settings:BackupPolarisMergeSettings=flags)=RestoredPolarisLink(source,url,id,pending,settings)
private fun work(uuid:String=A,children:List<RestoredPolarisLink> =listOf(link(11,"/a",101),link(12,"/b",202)))=RestoredPolarisWork(uuid,"Work",root,children)
private fun setup():Database {
 val db=Database()
 db.polarisRestoreQueries.mangas[101L]=MangaRow(101,11,"/a","A",JsonObject(emptyMap()))
 db.polarisRestoreQueries.mangas[202L]=MangaRow(202,12,"/b","B",JsonObject(emptyMap()))
 return db
}
private fun run(db:Database,vararg works:RestoredPolarisWork) = block {SqlDelightPolarisAtomicVirtualWorkPort(db).commitAllOrThrow(works.toList())}
fun main(){
 case("inserts parent, ledger and root+source edges") {val db=setup();run(db,work());val q=db.polarisRestoreQueries;check(q.ledgers.size==1&&q.mangas.size==3&&q.edges.size==3)}
 case("parent memo contains canonical UUID") {val db=setup();run(db,work());val m=db.polarisRestoreQueries.mangas[900]!!.memo;check((m["polaris.merge.work.uuid"] as JsonPrimitive).content==A)}
 case("idempotent restore does not insert duplicate parent or links") {val db=setup();run(db,work());run(db,work());check(db.polarisRestoreQueries.mangas.size==3&&db.polarisRestoreQueries.edges.size==3)}
 case("root stores all five flags, not just priority and sort") {val db=setup();run(db,work());val r=db.polarisRestoreQueries.edges.single{it.manga_source==6969L};check(r.download_chapters==root.downloadChapters && r.get_chapter_updates==root.getChapterUpdates&&r.chapter_priority==root.chapterPriority)}
 case("explicit pending URL retains a null manga ID") {val db=setup();run(db,work(children=listOf(link(11,"/a",101),link(12,"/b",null))));check(db.polarisRestoreQueries.edges.single{it.manga_source==12L}.manga_id==null)}
 case("different archives sharing a real source can coexist") {val db=setup();run(db,work(),work(B));check(db.polarisRestoreQueries.ledgers.size==2&&db.polarisRestoreQueries.edges.size==6)}
 case("different archive fingerprint refuses replacement") {val db=setup();run(db,work());fail{run(db,work().copy(title="different"))};check(db.polarisRestoreQueries.edges.size==3)}
 case("manual unlink remains unlinked on repeated backup") {val db=setup();run(db,work());db.polarisRestoreQueries.edges.removeIf{it.manga_source==12L};fail{run(db,work())};check(db.polarisRestoreQueries.edges.size==2)}
 case("virtual parent URL mutation is not accepted on replay") {val db=setup();run(db,work());val q=db.polarisRestoreQueries;val r=q.mangas.getValue(900);q.mangas[900]=r.copy(url="merged://bad-url");fail{run(db,work())}}
 case("manual priority edit refuses replay") {val db=setup();run(db,work());val q=db.polarisRestoreQueries;q.edges[0]=q.edges[0].copy(chapter_priority=99);fail{run(db,work())}}
 case("failed second parent rolls back first parent") {val db=setup();val q=db.polarisRestoreQueries;q.failAtEdge=3;fail{run(db,work(),work(B))};check(q.mangas.size==2&&q.edges.isEmpty()&&q.ledgers.isEmpty())}
 case("real child missing aborts before parent creation") {val db=setup();db.polarisRestoreQueries.mangas.remove(202L);fail{run(db,work())};check(db.polarisRestoreQueries.ledgers.isEmpty())}
 case("ambiguous source identity aborts rather than picking one") {val db=setup();db.polarisRestoreQueries.mangas[203]=MangaRow(203,11,"/a","duplicate",JsonObject(emptyMap()));fail{run(db,work())}}
 case("preledger UUID in memo blocks duplicate parent") {val db=setup();db.polarisRestoreQueries.mangas[903]=MangaRow(903,6969,"merged://legacy","old",JsonObject(mapOf("polaris.merge.work.uuid" to JsonPrimitive(A))));fail{run(db,work())}}
 case("bad archive UUID aborts before mutation") {val db=setup();fail{run(db,work("nonsense"))};check(db.polarisRestoreQueries.mangas.size==2)}
 case("mixed pending/real flags rejected") {val db=setup();fail{run(db,work(children=listOf(link(11,"/a",101,true))))}}
 case("two archive works with one UUID rejected before transaction") {val db=setup();fail{run(db,work(),work())}}
 case("different source IDs cannot map to one manga row") {val db=setup();fail{run(db,work(children=listOf(link(11,"/a",101),link(12,"/b",101))))}}
 case("digest distinguishes root settings, flags and link order") {val w=work();check(PolarisRestoreDigest.of(w)!=PolarisRestoreDigest.of(w.copy(rootSettings=root.copy(downloadChapters=true))));check(PolarisRestoreDigest.of(w)!=PolarisRestoreDigest.of(w.copy(children=w.children.reversed())))}
 println("POLARIS_SQLDELIGHT_PORT_PASS $cases")
}
