package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.*
import tachiyomi.data.Database
import kotlin.coroutines.*

private var passed=0
private fun <T> runBlockingHost(block:suspend()->T):T {
    var result:Result<T>?=null
    block.startCoroutine(object:Continuation<T>{
        override val context=EmptyCoroutineContext
        override fun resumeWith(value:Result<T>){result=value}
    })
    return checkNotNull(result).getOrThrow()
}
private fun ok(msg:String, block:()->Unit) {block();passed++; println("PASS $passed $msg")}
private fun reject(msg:String,block:()->Unit) = ok(msg) {check(runCatching(block).isFailure){"EXPECTED REJECT: $msg"}}
private val uuid="123e4567-e89b-42d3-a456-426614174000"
private fun work(archive:BackupManga=BackupManga(source=6969,url="merged://archive-url",title="Parent",
    chapters=listOf(BackupChapter("/one","Chapter One",read=true,lastPageRead=4,version=3)),
    history=listOf(BackupHistory("/one",1234,7)), categories=emptyList(),
    memo="{\"nested\":\"ok\"}".encodeToByteArray(),version=9,lastModifiedAt=4321),
    id:String=uuid,digest:String="a".repeat(64),child:SqlDelightPolarisFreshParentAdapter.ChildLink?=null
):SqlDelightPolarisFreshParentAdapter.FreshWork {
    val source=child?:SqlDelightPolarisFreshParentAdapter.ChildLink(77,"/real-101",101,
        SqlDelightPolarisFreshParentAdapter.LinkSettings(infoManga=true,chapterPriority=0))
    return SqlDelightPolarisFreshParentAdapter.FreshWork(id,digest,archive,emptyMap(),listOf(source),
        SqlDelightPolarisFreshParentAdapter.LinkSettings(chapterPriority=10))
}
private fun setup():Triple<SqlDelightPolarisFreshParentAdapter,Database,TestDriver>{
    val driver=TestDriver();val db=Database(driver)
    return Triple(SqlDelightPolarisFreshParentAdapter(db,driver),db,driver)
}
fun main(){
  ok("writes full parent/chapter/history/edges/ledger and commits") {
    val (adapter,db,driver)=setup()
    val ids=runBlockingHost {adapter.restoreNewOnly(listOf(work()))}
    check(ids==listOf(103L)&&db.parent?.version==9L&&db.parent?.last_modified_at==4321L)
    check(db.chapters.size==1&&db.history.size==1&&db.edges.size==2&&db.ledger.size==1)
    check(driver.commitCount==1&&driver.rollbackCount==0)
  }
  ok("root edge always points to reserved ID") {val (a,db,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work()))};check(db.edges.single{it.manga_source==6969L}.manga_id==103L)}
  ok("history binds to newly inserted chapter ID") {val(a,db,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work()))};check(db.history.single().chapter_id==db.chapters.single()._id)}
  ok("transaction driver uses BEGIN IMMEDIATE and deferred FK") {val(a,_,d)=setup();runBlockingHost{a.restoreNewOnly(listOf(work()))};check(d.statements.first()=="BEGIN IMMEDIATE"&& d.statements.any{it.contains("defer_foreign_keys = ON")})}
  ok("commit clears deferred FK mode") {val(a,_,d)=setup();runBlockingHost{a.restoreNewOnly(listOf(work()))};check(d.deferred==0L)}
  reject("reject empty batch") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(emptyList())}}
  reject("reject duplicated UUID within batch") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work(),work()))}}
  reject("reject invalid UUID") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work(id="invalid")))}}
  reject("reject invalid digest") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work(digest="not-a-sha")))}}
  reject("reject invalid virtual source") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work(BackupManga(1,"a","t"))))}}
  reject("reject missing source child") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work(child=SqlDelightPolarisFreshParentAdapter.ChildLink(77,"/not-found",101,SqlDelightPolarisFreshParentAdapter.LinkSettings(infoManga=true,chapterPriority=0)))))}}
  reject("reject two info sources absent") {val(a,_,_)=setup();runBlockingHost{a.restoreNewOnly(listOf(work(child=SqlDelightPolarisFreshParentAdapter.ChildLink(77,"/real-101",101,SqlDelightPolarisFreshParentAdapter.LinkSettings(infoManga=false,chapterPriority=0)))))}}
  reject("reject duplicate edge priorities") {val(a,_,_)=setup();val w=work().copy(rootSettings=SqlDelightPolarisFreshParentAdapter.LinkSettings(chapterPriority=0));runBlockingHost{a.restoreNewOnly(listOf(w))}}
  reject("reject root info flag") {val(a,_,_)=setup();val w=work().copy(rootSettings=SqlDelightPolarisFreshParentAdapter.LinkSettings(infoManga=true,chapterPriority=10));runBlockingHost{a.restoreNewOnly(listOf(w))}}
  ok("rollback when parent insert itself fails") {val(a,db,d)=setup();db.forceInsertParentFailure=true;check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure);check(db.parent==null&&db.ledger.isEmpty()&&db.chapters.isEmpty()&&db.edges.isEmpty()&&d.rollbackCount==1)}
  ok("rollback if title changes at final physical readback") {val(a,db,d)=setup();db.tamperParent=true;check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure);check(db.parent==null&&db.ledger.isEmpty()&&db.chapters.isEmpty()&&d.rollbackCount==1)}
  ok("reject physical source child disappearing") {val(a,db,d)=setup();db.missingPhysicalChild=true;check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure);check(db.parent==null&&db.chapters.isEmpty()&&d.rollbackCount==1)}
  ok("duplicate import never replaces user parent or ledger") {val(a,db,d)=setup();runBlockingHost{a.restoreNewOnly(listOf(work()))};check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure);check(db.parent?.title=="Parent"&&db.ledger.size==1&&d.rollbackCount==1)}
  ok("fails closed on driver foreign keys disabled") {val(a,db,d)=setup();d.foreignKeys=0;check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure);check(db.parent==null&&d.rollbackCount==1)}
  ok("reject wrong outgoing root source") {val(a,_,_)=setup();val w=work().copy(rootSettings=SqlDelightPolarisFreshParentAdapter.LinkSettings(chapterPriority=10,downloadChapters=true));check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(w))}}.isFailure)}
  ok("restores category, tracking and excluded scanlator columns") {
    val (a,db,_)=setup()
    val archive=BackupManga(source=6969,url="archive://old",title="Full Parent",
        categories=listOf(2L),tracking=listOf(BackupTracking(syncId=4,libraryId=5,mediaId=999,
            title="Remote",score=7.5f,totalChapters=12)),excludedScanlators=listOf("Group"))
    val w=work(archive).copy(categoryIdsByArchiveOrder=mapOf(2L to 71L))
    runBlockingHost {a.restoreNewOnly(listOf(w))}
    check(db.categories.single().category_id==71L)
    check(db.tracks.single().remote_id==999L && db.tracks.single().score==7.5)
    check(db.exclusions.single().scanlator=="Group")
  }
  ok("rollback if persisted tracker score drifts") {
    val (a,db,d)=setup();db.tamperTrack=true
    val w=work(BackupManga(source=6969,url="archive://old",title="Full Parent",
        tracking=listOf(BackupTracking(syncId=4,libraryId=5,mediaId=999,score=7.5f))))
    check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(w))}}.isFailure)
    check(db.tracks.isEmpty()&&db.parent==null&&d.rollbackCount==1)
  }
  ok("rollback if persisted history duration drifts") {
    val(a,db,d)=setup();db.tamperHistory=true
    check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure)
    check(db.history.isEmpty()&&db.parent==null&&d.rollbackCount==1)
  }
  ok("rollback if merged edge priority is altered") {
    val(a,db,d)=setup();db.tamperEdge=true
    check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work()))}}.isFailure)
    check(db.edges.isEmpty()&&db.parent==null&&d.rollbackCount==1)
  }
  ok("rollback if a prepared category is removed in readback") {
    val(a,db,d)=setup();db.tamperCategory=true
    val archive=BackupManga(source=6969,url="archive://old",title="Full Parent",categories=listOf(2L))
    check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work(archive).copy(categoryIdsByArchiveOrder=mapOf(2L to 71L))))}}.isFailure)
    check(db.categories.isEmpty()&&db.parent==null&&d.rollbackCount==1)
  }
  ok("a bad second work undoes writes from first") {
    val(a,db,d)=setup();val second=work(id="223e4567-e89b-42d3-a456-426614174001",digest="b".repeat(64))
    check(runCatching{runBlockingHost{a.restoreNewOnly(listOf(work(),second))}}.isFailure)
    check(db.parent==null&&db.history.isEmpty()&&db.edges.isEmpty()&&db.ledger.isEmpty()&&d.rollbackCount==1)
  }
  ok("pending child is preserved when no physical row exists") {
    val(a,db,_)=setup();val w=work(child=SqlDelightPolarisFreshParentAdapter.ChildLink(77,"/not-found",null,
        SqlDelightPolarisFreshParentAdapter.LinkSettings(infoManga=true,chapterPriority=0)))
    runBlockingHost{a.restoreNewOnly(listOf(w))}
    check(db.edges.single{it.manga_source==77L}.manga_id==null)
  }
  reject("pending child must not auto-resolve in transaction") {
    val(a,_,_)=setup();val w=work(child=SqlDelightPolarisFreshParentAdapter.ChildLink(77,"/real-101",null,
        SqlDelightPolarisFreshParentAdapter.LinkSettings(infoManga=true,chapterPriority=0)))
    runBlockingHost{a.restoreNewOnly(listOf(w))}
  }
  println("POLARIS_FRESH_PARENT_ADAPTER_HOST_PASS $passed")
}
