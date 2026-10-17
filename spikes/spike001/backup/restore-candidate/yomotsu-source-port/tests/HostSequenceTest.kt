package polaris.spike001.backup.restore.yomotsu

import eu.kanade.tachiyomi.data.backup.models.*
import eu.kanade.tachiyomi.data.backup.restore.restorers.MangaRestorer
import polaris.spike001.backup.restore.*
import tachiyomi.data.Database

private val UUID="123e4567-e89b-42d3-a456-426614174000"
private val F = BackupPolarisMergeSettings(false,true,2,0,false)
private fun bundle(extra:Boolean=true,pending:Boolean=false):BackupPolarisBundle = BackupPolarisBundle(
 works=listOf(BackupPolarisWork(UUID,"Book",F,listOf(BackupPolarisLink(11,"/real","Real",F,pending)),UUID)),
 supplementalManga=if(extra)listOf(BackupManga(11,"/real",listOf(BackupChapter("/one",true,true,7)))) else emptyList()
)
private class Parent : PolarisAtomicVirtualWorkPort {
 var calls=0
 var payload:List<RestoredPolarisWork> = emptyList()
 override suspend fun commitAllOrThrow(works:List<RestoredPolarisWork>){calls++;payload=works}
}
private fun make():Triple<PolarisYomotsuStrictRestoreSequence,Parent,MangaRestorer>{
 val db=Database();val restore=MangaRestorer(db)
 val source=YomotsuPolarisSourceRestorePort(restore,db,emptyList())
 val parent=Parent()
 val seq=PolarisYomotsuStrictRestoreSequence(PolarisRestoreCoordinator(source,parent),source)
 return Triple(seq,parent,restore)
}
fun main(){
 var passes=0
 fun test(name:String,block:()->Unit){block();passes++;println("RESTORE_SEQUENCE_PASS $passes $name")}
 fun fail(block:()->Unit){check(runCatching(block).isFailure)}
 test("supplemental snapshot restored before committing parent"){
  val (seq,par,rest)=make();val b=bundle()
  sync{seq.restoreAfterStockOrdinaryJobsOrThrow(b,emptyList(),true,{check(par.calls==0)})}
  check(rest.calls==1&&par.calls==1&&par.payload.single().children.single().realMangaId==100L)
 }
 test("ordinary required snapshot is strictly replayed after normal callback"){
  val(seq,par,rest)=make();val b=bundle(false)
  var awaited=false
  sync{seq.restoreAfterStockOrdinaryJobsOrThrow(b,listOf(BackupManga(11,"/real",listOf(BackupChapter("/one",true,true,7)))),true,{awaited=true})}
  check(awaited&&rest.calls==1&&par.calls==1)
 }
 test("unrelated ordinary source is not replayed"){
  val(seq,par,rest)=make();val b=bundle(true)
  sync{seq.restoreAfterStockOrdinaryJobsOrThrow(b,listOf(BackupManga(55,"/other")),true,{})}
  check(rest.calls==1&&par.calls==1)
 }
 test("failing normal completion barrier prevents writes"){
  val(seq,par,_)=make();fail{sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle(),emptyList(),true,{error("normal failed")})}};check(par.calls==0)
 }
 test("failed required ordinary restore blocks parents"){
  val(seq,par,rest)=make();rest.fail=true
  fail{sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle(false),listOf(BackupManga(11,"/real")),true,{})}};check(par.calls==0)
 }
 test("failed supplemental restoration blocks parents"){
  val(seq,par,rest)=make();rest.fail=true
  fail{sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle(),emptyList(),true,{})}};check(par.calls==0)
 }
 test("incomplete ordinary chapter data blocks parents"){
  val(seq,par,rest)=make();rest.omitChapter=true
  fail{sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle(false),listOf(BackupManga(11,"/real",listOf(BackupChapter("/one")))),true,{})}};check(par.calls==0)
 }
 test("missing required snapshot rejected before callback"){
  val(seq,par,_)=make();var calls=0
  fail{sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle(false),emptyList(),true,{calls++})}}
  check(calls==0&&par.calls==0)
 }
 test("corrupt uuid rejected before callback"){
  val(seq,par,_)=make();val w=bundle().works.single().copy(canonicalUuid="bad")
  var calls=0
  fail{sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle().copy(works=listOf(w)),emptyList(),true,{calls++})}}
  check(calls==0&&par.calls==0)
 }
 test("legacy backup without segment leaves original callback alone"){
  val(seq,par,rest)=make();var calls=0
  check(sync{seq.restoreAfterStockOrdinaryJobsOrThrow(null,emptyList(),true,{calls++})}.isEmpty())
  check(calls==0&&par.calls==0&&rest.calls==0)
 }
 test("library disabled avoids parent and ordinary replay"){
  val(seq,par,rest)=make();var calls=0
  check(sync{seq.restoreAfterStockOrdinaryJobsOrThrow(bundle(),emptyList(),false,{calls++})}.isEmpty())
  check(calls==0&&par.calls==0&&rest.calls==0)
 }
 test("explicit pending null skips source restore"){
  val(seq,par,rest)=make();val b=bundle(false,pending=true)
  sync{seq.restoreAfterStockOrdinaryJobsOrThrow(b,emptyList(),true,{})}
  check(rest.calls==0&&par.payload.single().children.single().realMangaId==null)
 }
 test("preflight can run before any stock restore"){
  val(seq,par,rest)=make();seq.preflightBeforeAnyWrites(bundle(),emptyList(),true)
  check(rest.calls==0&&par.calls==0)
 }
 test("preflight rejects unsupported backup format"){
  val(seq,par,_)=make();fail{seq.preflightBeforeAnyWrites(bundle().copy(formatVersion=999),emptyList(),true)};check(par.calls==0)
 }
 println("POLARIS_YOMOTSU_RESTORE_SEQUENCE_PASS $passes")
}
