package polaris.spike001.backup.restore.yomotsu

import eu.kanade.tachiyomi.data.backup.models.*
import eu.kanade.tachiyomi.data.backup.restore.restorers.MangaRestorer
import polaris.spike001.backup.restore.*
import tachiyomi.data.Database

private const val UUID_L="123e4567-e89b-42d3-a456-426614174000"
private val FLAGS_L=BackupPolarisMergeSettings(false,true,2,0,false)
private fun backupL(extra:Boolean=true,pending:Boolean=false,uuid:String=UUID_L)=BackupPolarisBundle(
 works=listOf(BackupPolarisWork(UUID_L,"Title",FLAGS_L,
  listOf(BackupPolarisLink(12,"/a","Source",FLAGS_L,pending)),uuid)),
 supplementalManga=if(extra) listOf(BackupManga(12,"/a",listOf(BackupChapter("/1",true,true,6)))) else emptyList()
)
private class ParentL:PolarisAtomicVirtualWorkPort {
 var calls=0
 var restored:List<RestoredPolarisWork> = emptyList()
 override suspend fun commitAllOrThrow(works:List<RestoredPolarisWork>){calls++;restored=works}
}
private data class HarnessL(val lifecycle:PolarisBackupRestorerLifecycle,val parent:ParentL,val restorer:MangaRestorer,val db:Database)
private fun harnessL():HarnessL {
 val db=Database();val manga=MangaRestorer(db)
 val source=YomotsuPolarisSourceRestorePort(manga,db,emptyList())
 val parents=ParentL()
 return HarnessL(PolarisBackupRestorerLifecycle(
   PolarisYomotsuStrictRestoreSequence(PolarisRestoreCoordinator(source,parents),source)),parents,manga,db)
}
fun main(){
 var passed=0
 fun test(label:String, run:()->Unit){run();passed++;println("BACKUP_RESTORER_LIFECYCLE_PASS $passed $label")}
 fun fails(block:()->Unit){check(runCatching(block).isFailure)}
 test("legacy archive executes stock exactly once; no polaris parents") {
  val h=harnessL();var runs=0
  check(sync{h.lifecycle.restoreAfterDecodedPreflight(null, emptyList(),true){runs++}}.isEmpty())
  check(runs==1&&h.parent.calls==0&&h.restorer.calls==0)
 }
 test("library disabled still executes stock once, never links virtual parent") {
  val h=harnessL();var runs=0
  check(sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),emptyList(),false){runs++}}.isEmpty())
  check(runs==1&&h.parent.calls==0&&h.restorer.calls==0)
 }
 test("invalid archive UUID is rejected before stock jobs and before parent writes") {
  val h=harnessL();var runs=0
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(uuid="invalid"),emptyList(),true){runs++}}}
  check(runs==0&&h.parent.calls==0&&h.restorer.calls==0)
 }
 test("unsupported format fails before stock jobs") {
  val h=harnessL();var runs=0
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL().copy(formatVersion=99),emptyList(),true){runs++}}}
  check(runs==0&&h.parent.calls==0)
 }
 test("missing child snapshot fails preflight before stock writes") {
  val h=harnessL();var runs=0
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(extra=false),emptyList(),true){runs++}}}
  check(runs==0&&h.parent.calls==0)
 }
 test("stock hard exception stops before strict supplemental and parent") {
  val h=harnessL();var runs=0
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),emptyList(),true){runs++;error("stock failed")}}}
  check(runs==1&&h.parent.calls==0&&h.restorer.calls==0)
 }
 test("stock is completed before strict supplemental source restore and parent") {
  val h=harnessL();var runs=0;var finished=false
  sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),emptyList(),true){runs++;check(h.parent.calls==0);finished=true}}
  check(runs==1&&finished&&h.restorer.calls==1&&h.parent.calls==1)
 }
 test("ordinary linked child is strictly replayed after stock; not twice in Polaris") {
  val h=harnessL();var runs=0
  val ordinary=listOf(BackupManga(12,"/a",listOf(BackupChapter("/1",true,true,6))))
  sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(extra=false),ordinary,true){runs++}}
  check(runs==1&&h.restorer.calls==1&&h.parent.calls==1)
 }
 test("unrelated ordinary backup is not retried by Polaris") {
  val h=harnessL();val unrelated=listOf(BackupManga(300,"/unrelated"))
  sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),unrelated,true){}}
  check(h.restorer.calls==1&&h.parent.calls==1)
 }
 test("required ordinary failure after stock completion blocks parent") {
  val h=harnessL();h.restorer.fail=true
  val ordinary=listOf(BackupManga(12,"/a",listOf(BackupChapter("/1"))))
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(extra=false),ordinary,true){}}}
  check(h.parent.calls==0)
 }
 test("failed supplemental restores block parent after stock completion") {
  val h=harnessL();h.restorer.fail=true
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),emptyList(),true){}}}
  check(h.parent.calls==0)
 }
 test("database chapter errors propagate through lifecycle") {
  val h=harnessL();h.db.chaptersQueries.fail=true
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),emptyList(),true){}}}
  check(h.parent.calls==0)
 }
 test("pending link avoids all source writes after original job") {
  val h=harnessL();var runs=0
  val b=backupL(extra=false,pending=true)
  sync{h.lifecycle.restoreAfterDecodedPreflight(b,emptyList(),true){runs++}}
  check(runs==1&&h.restorer.calls==0&&h.parent.calls==1&&h.parent.restored.single().children.single().realMangaId==null)
 }
 test("restored child ID is returned only after stock callback") {
  val h=harnessL();var began=false
  val works=sync{h.lifecycle.restoreAfterDecodedPreflight(backupL(),emptyList(),true){
    began=true
    check(h.db.polarisRestoreQueries.ids.isEmpty())
  }}
  check(began&&works.single().children.single().realMangaId==100L)
 }
 test("duplicate source key is rejected by preflight before jobs") {
  val h=harnessL();var runs=0
  val b=backupL()
  val w=b.works.single()
  fails{sync{h.lifecycle.restoreAfterDecodedPreflight(b.copy(works=listOf(w.copy(links=w.links+w.links))),emptyList(),true){runs++}}}
  check(runs==0&&h.parent.calls==0)
 }
 test("no work in valid empty Polaris bundle runs only original path") {
  val h=harnessL();var runs=0
  val b=BackupPolarisBundle()
  val result=sync{h.lifecycle.restoreAfterDecodedPreflight(b,emptyList(),true){runs++}}
  check(result.isEmpty()&&runs==1&&h.parent.calls==0&&h.restorer.calls==0)
 }
 println("POLARIS_BACKUP_RESTORER_LIFECYCLE_PASS $passed")
}
