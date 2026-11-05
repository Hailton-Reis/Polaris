package polaris.spike001.backup.yomotsu

import eu.kanade.tachiyomi.data.backup.create.BackupOptions
import eu.kanade.tachiyomi.data.backup.create.creators.MangaBackupCreator
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import kotlinx.serialization.json.*
import polaris.spike001.backup.uuid.YomotsuMergedWorkUuidStore
import tachiyomi.domain.manga.model.*
import tachiyomi.domain.manga.repository.*
import java.util.UUID
import kotlin.coroutines.*

private var checks=0
private fun checkCase(label:String, block:()->Unit){block(); checks++;println("EXPORT_ADAPTER_PASS $checks: $label")}
private fun fail(block:()->Unit){check(runCatching(block).isFailure)}
private fun <T> runSuspended(block:suspend ()->T):T {
 var result:Result<T>?=null
 block.startCoroutine(object:Continuation<T>{override val context=EmptyCoroutineContext;override fun resumeWith(value:Result<T>){result=value}})
 return checkNotNull(result).getOrThrow()
}
private const val UUID_A="123e4567-e89b-42d3-a456-426614174000"
private const val UUID_B="123e4567-e89b-42d3-a456-426614174001"
private class Db(vararg rows:Manga):MangaRepository {
 val byId=rows.associateBy{it.id}.toMutableMap();var writes=0
 override suspend fun getMangaById(id:Long)=byId.getValue(id)
 override suspend fun update(update:MangaUpdate):Boolean {writes++;byId[update.id]=byId.getValue(update.id).copy(memo=checkNotNull(update.memo));return true}
}
private class Links:MangaMergeRepository{
 val byParent=mutableMapOf<Long,List<MergedMangaReference>>()
 override suspend fun getReferencesById(id:Long)=byParent.getValue(id)
}
private data class Setup(val db:Db,val refs:Links,val creator:MangaBackupCreator,val exporter:PolarisYomotsuBackupExporter)
private fun parent(id:Long,uuid:String?=UUID_A)=Manga(id,6969,"merged://$id","Merged $id",true,if(uuid==null)JsonObject() else JsonObject(mapOf("polaris.merge.work.uuid" to JsonPrimitive(uuid))))
private fun child(id:Long,src:Long,url:String)=Manga(id,src,url,"Source $id",false)
private fun ref(p:Long,c:Long?,src:Long,url:String,priority:Int=1)=MergedMangaReference(p,"merged://$p",c,url,src,priority==0,true,2,priority)
private fun refs(p:Long)=listOf(ref(p,100,11,"/a",0),ref(p,200,12,"/b",1),ref(p,p,6969,"merged://$p",99))
private fun setup(parents:List<Manga> = listOf(parent(900)),children:List<Manga> = listOf(child(100,11,"/a"),child(200,12,"/b"))):Setup {
 val db=Db(*(parents+children).toTypedArray());val links=Links();parents.forEach{links.byParent[it.id]=refs(it.id)}
 val creator=MangaBackupCreator()
 return Setup(db,links,creator,PolarisYomotsuBackupExporter(db,links,YomotsuMergedWorkUuidStore(db){UUID.fromString(UUID_A)},creator))
}
private fun normal(m:Manga)=BackupManga(m.source,m.url)
private fun collect(s:Setup,ordinary:List<Manga>,options:BackupOptions=BackupOptions())=
 runSuspended{s.exporter.collect(ordinary,ordinary.map(::normal),options)}
fun main(){
 checkCase("Both nonfavorite real children are supplemental full source snapshots") {
  val s=setup();val b=collect(s,listOf(s.db.byId.getValue(900)))!!
  check(b.supplementalManga.map{it.source to it.url}==listOf(11L to "/a",12L to "/b"));check(b.supplementalManga.all{it.fakeChapters.isNotEmpty()})
 }
 checkCase("Already-included child excluded from supplements") {
  val s=setup();val b=collect(s,listOf(s.db.byId.getValue(900),s.db.byId.getValue(100)))!!
  check(b.supplementalManga.map{it.url}==listOf("/b"))
 }
 checkCase("Forward identical BackupOptions to MangaBackupCreator") {
  val s=setup();val opts=BackupOptions(chapters=false,tracking=false)
  val b=collect(s,listOf(s.db.byId.getValue(900)),opts)!!
  check(s.creator.lastOptions===opts && b.supplementalManga.all{it.fakeChapters.isEmpty()})
 }
 checkCase("Shared children of two virtual works have one source snapshot") {
  val s=setup(parents=listOf(parent(900),parent(901,UUID_B)))
  val b=collect(s,listOf(s.db.byId.getValue(900),s.db.byId.getValue(901)))!!
  check(b.works.size==2 && b.supplementalManga.size==2)
 }
 checkCase("NULL source reference survives as pending without invented manga") {
  val s=setup();s.refs.byParent[900]=listOf(ref(900,100,11,"/a",0),ref(900,null,12,"/b"),ref(900,900,6969,"merged://900"))
  val b=collect(s,listOf(s.db.byId.getValue(900)))!!
  check(b.works.single().links[1].isPending && b.supplementalManga.size==1)
 }
 checkCase("No virtual root aborts export") {
  val s=setup();s.refs.byParent[900]=refs(900).dropLast(1)
  fail{collect(s,listOf(s.db.byId.getValue(900)))}
 }
 checkCase("Wrong real manga source URL aborts export") {
  val s=setup();s.refs.byParent[900]=listOf(ref(900,100,99,"/wrong",0),ref(900,900,6969,"merged://900"))
  fail{collect(s,listOf(s.db.byId.getValue(900)))}
 }
 checkCase("Resolved-to-pending mutation during chapter copy aborts export") {
  val s=setup();s.creator.onBackup={s.refs.byParent[900]=listOf(ref(900,100,11,"/a",0),ref(900,null,12,"/b"),ref(900,900,6969,"merged://900"))}
  fail{collect(s,listOf(s.db.byId.getValue(900)))}
 }
 checkCase("Changed virtual parent title during chapter copy aborts export") {
  val s=setup();s.creator.onBackup={s.db.byId[900]=s.db.byId.getValue(900).copy(title="Changed")}
  fail{collect(s,listOf(s.db.byId.getValue(900)))}
 }
 checkCase("No library options means no optional bundle and no DB writes") {
  val s=setup();check(collect(s,listOf(s.db.byId.getValue(900)),BackupOptions(libraryEntries=false))==null)
  check(s.creator.calls==0 && s.db.writes==0)
 }
 checkCase("No virtual works means no optional bundle") {
  val s=setup();check(collect(s,listOf(s.db.byId.getValue(100)))==null && s.creator.calls==0)
 }
 checkCase("Newly generated UUID is persisted and used for portable identity") {
  val s=setup(parents=listOf(parent(900,uuid=null)))
  val b=collect(s,listOf(s.db.byId.getValue(900)))!!
  check(b.works.single().archiveWorkKey==UUID_A && s.db.writes==1)
 }
 println("POLARIS_YOMOTSU_EXPORT_ADAPTER_PASS $checks")
}
