package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.parent.BackupPolarisParentPayload
import tachiyomi.data.Database
import kotlin.coroutines.*

private var passed = 0
private val uuid = "123e4567-e89b-42d3-a456-426614174000"
private fun <T> sync(block: suspend () -> T): T {
    var result: Result<T>? = null
    block.startCoroutine(object : Continuation<T> {
        override val context = EmptyCoroutineContext
        override fun resumeWith(value: Result<T>) { result = value }
    })
    return checkNotNull(result).getOrThrow()
}
private fun ok(title: String, action: () -> Unit) { action(); ++passed; println("PASS $passed $title") }
private fun reject(title: String, action: () -> Unit) = ok(title) {
    check(runCatching(action).isFailure) { "Expected rejection: $title" }
}
private class HostBoundCodec : PolarisV2EnvelopeCodec<PolarisV2ProtoBufEnvelope> {
    private var last: PolarisV2ProtoBufEnvelope? = null
    override fun encodeCanonical(value: PolarisV2ProtoBufEnvelope): ByteArray {
        value.validateDecoded()
        last = value
        val m = value.parent.manga
        val fields = listOf(value.formatVersion.toString(), value.work.archiveWorkKey, value.work.displayTitle,
            value.work.canonicalUuid.orEmpty(), value.work.rootSettings.infoManga.toString(),
            value.work.rootSettings.getChapterUpdates.toString(), value.work.rootSettings.chapterPriority.toString(),
            value.work.rootSettings.chapterSortMode.toString(), value.work.rootSettings.downloadChapters.toString(),
            value.parent.archiveUuid, value.parent.originalOrdinal.toString(),m.source.toString(),m.url,m.title,
            m.notes,m.memo.decodeToString(),m.lastModifiedAt.toString(),m.version.toString(),
            m.chapters.size.toString()) + m.chapters.flatMap { listOf(it.url,it.name,it.version.toString()) } +
            listOf(m.categories.size.toString()) + m.categories.map {it.toString()} +
            listOf(value.work.links.size.toString()) + value.work.links.flatMap { link ->
                listOf(link.sourceId.toString(),link.sourceUrl,link.observedTitle,link.isPending.toString(),
                    link.settings.infoManga.toString(),link.settings.getChapterUpdates.toString(),
                    link.settings.chapterSortMode.toString(),link.settings.chapterPriority.toString(),
                    link.settings.downloadChapters.toString())
            } + listOf(value.referencedCategories.size.toString()) + value.referencedCategories.flatMap {
                listOf(it.name,it.order.toString(),it.flags.toString())
            }
        return fields.joinToString(""){"${it.toByteArray().size}:$it"}.toByteArray()
    }
    override fun decodeCanonical(bytes: ByteArray): PolarisV2ProtoBufEnvelope = checkNotNull(last)
}
private data class Fixture(val bundle: BackupPolarisBundle, val manga: BackupManga,
    val work: BackupPolarisWork, val categories: MutableList<BackupCategory>,val codec: HostBoundCodec)
private fun fixture(withCategory: Boolean = false, pending: Boolean = false): Fixture {
    val categoryOrders: List<Long> = if(withCategory) listOf(2L) else emptyList()
    val manga = BackupManga(6969,"archive://old","Parent",categories=categoryOrders,
        chapters=listOf(BackupChapter("/chapter","One",read=true,version=3L)),
        history=listOf(BackupHistory("/chapter",1234L,7)),
        memo="{\"nested\":\"ok\"}".toByteArray(), version=9L,lastModifiedAt=4321L)
    val settings = BackupPolarisMergeSettings(true, chapterPriority=0)
    val work=BackupPolarisWork(uuid,"Parent",uuid,BackupPolarisMergeSettings(chapterPriority=10),
        mutableListOf(BackupPolarisLink(77,if(pending)"/missing" else "/real-101","Source",settings,pending)))
    return Fixture(BackupPolarisBundle(2,listOf(work),listOf(BackupPolarisParentPayload(uuid,manga,0))),
        manga,work,if(withCategory)mutableListOf(BackupCategory("Original",order=2L))else mutableListOf(),HostBoundCodec())
}
private fun dest(f: Fixture, pending: Boolean = false) = PolarisV2BoundFreshRestoreBridge.Destination(
    uuid,if(f.categories.isNotEmpty())mapOf(2L to 71L)else emptyMap(),
    if(pending)emptyMap()else mapOf((77L to "/real-101") to 101L))
private fun bind(f:Fixture=fixture(),pending:Boolean=false,d:PolarisV2BoundFreshRestoreBridge.Destination=dest(f,pending)) =
    PolarisV2BoundFreshRestoreBridge.bindDecoded(f.bundle,emptyList(),f.categories,listOf(d),f.codec)
private fun setup():Triple<SqlDelightPolarisFreshParentAdapter,Database,TestDriver> {
    val driver=TestDriver();val db=Database(driver)
    return Triple(SqlDelightPolarisFreshParentAdapter(db,driver),db,driver)
}
fun main() {
    ok("decoder-owned bound work is accepted and commits") {
        val f=fixture();val (adapter,db,driver)=setup()
        val ids=sync {PolarisV2BoundFreshRestoreBridge.restoreDecodedNewOnly(adapter,f.bundle,emptyList(),f.categories,listOf(dest(f)),f.codec)}
        check(ids==listOf(103L) && db.parent?.title=="Parent" && db.ledger[uuid]!=null && driver.commitCount==1)
    }
    ok("category snapshots travel directly to adapter") {
        val f=fixture(withCategory=true);val (adapter,db,_)=setup()
        sync{adapter.restoreBoundNewOnly(bind(f))};check(db.categories==listOf(71L))
    }
    ok("explicit pending source remains pending") {
        val f=fixture(pending=true);val(adapter,db,_)=setup()
        sync{adapter.restoreBoundNewOnly(bind(f,pending=true))}
        check(db.edges.single{it.manga_source==77L}.manga_id==null)
    }
    reject("refuse unbound opaque-byte work in bound entrypoint") {
        val (adapter,_,_)=setup();val f=fixture();val w=bind(f).single().copy(boundV2Admission=null)
        sync{adapter.restoreBoundNewOnly(listOf(w))}
    }
    reject("reject missing destination before DB writes") {val f=fixture();PolarisV2BoundFreshRestoreBridge.bindDecoded(f.bundle,emptyList(),f.categories,emptyList(),f.codec)}
    reject("reject extra destination before DB writes") {val f=fixture();PolarisV2BoundFreshRestoreBridge.bindDecoded(f.bundle,emptyList(),f.categories,listOf(dest(f),dest(f)),f.codec)}
    reject("reject destination for different UUID") {val f=fixture();PolarisV2BoundFreshRestoreBridge.bindDecoded(f.bundle,emptyList(),f.categories,listOf(dest(f).copy(archiveUuid="other")),f.codec)}
    reject("reject missing resolved source map") {val f=fixture();bind(f,d=dest(f).copy(realChildrenByIdentity=emptyMap()))}
    reject("reject extra resolved source") {val f=fixture();bind(f,d=dest(f).copy(realChildrenByIdentity=dest(f).realChildrenByIdentity+((88L to "/other") to 888L)))}
    reject("reject impossible local ID") {val f=fixture();bind(f,d=dest(f).copy(realChildrenByIdentity=mapOf((77L to "/real-101") to -1L)))}
    reject("reject mapping for pending source") {val f=fixture(pending=true);bind(f,pending=true,d=dest(f).copy(realChildrenByIdentity=mapOf((77L to "/missing") to 101L)))}
    reject("reject missing archive category mapping") {val f=fixture(withCategory=true);bind(f,d=dest(f).copy(categoriesByOrder=emptyMap()))}
    reject("reject extraneous category mapping") {val f=fixture();bind(f,d=dest(f).copy(categoriesByOrder=mapOf(2L to 71L)))}
    reject("reject wrong destination category ID") {val f=fixture(withCategory=true);bind(f,d=dest(f).copy(categoriesByOrder=mapOf(2L to -1L)))}
    reject("reject swapped archive parent reference") {val f=fixture();val w=bind(f).single();val(adapter,_,_)=setup();sync{adapter.restoreBoundNewOnly(listOf(w.copy(archive=BackupManga(6969,"x","Parent"))))}}
    reject("reject substituted canonical bytes even if same admitted model") {val f=fixture();val w=bind(f).single();val(adapter,_,_)=setup();sync{adapter.restoreBoundNewOnly(listOf(w.copy(archiveSnapshotBytes="foreign".toByteArray())))}}
    reject("reject forged digest") {val f=fixture();val w=bind(f).single();val(adapter,_,_)=setup();sync{adapter.restoreBoundNewOnly(listOf(w.copy(archiveDigest="0".repeat(64))))}}
    reject("reject fabricated child URL with valid real child") {val f=fixture();val w=bind(f).single();val(adapter,_,_)=setup();sync{adapter.restoreBoundNewOnly(listOf(w.copy(children=listOf(w.children.single().copy(sourceUrl="/wrong")))))}}
    reject("reject changed root settings") {val f=fixture();val w=bind(f).single();val(adapter,_,_)=setup();sync{adapter.restoreBoundNewOnly(listOf(w.copy(rootSettings=w.rootSettings.copy(chapterPriority=11))))}}
    reject("reject replaced archive category DTO") {val f=fixture(withCategory=true);val w=bind(f).single();val(adapter,_,_)=setup();sync{adapter.restoreBoundNewOnly(listOf(w.copy(archiveCategories=listOf(BackupCategory("Original",order=2L)))))} }
    ok("reject parent title mutation before entering transaction") {val f=fixture();val w=bind(f).single();f.manga.title="Edited";val(adapter,db,d)=setup();check(runCatching{sync{adapter.restoreBoundNewOnly(listOf(w))}}.isFailure);check(db.parent==null&&d.commitCount==0)}
    ok("reject chapter mutation before entering transaction") {val f=fixture();val w=bind(f).single();f.manga.chapters[0].name="Altered";val(adapter,db,_)=setup();check(runCatching{sync{adapter.restoreBoundNewOnly(listOf(w))}}.isFailure);check(db.parent==null)}
    ok("reject category rename before entering transaction") {val f=fixture(withCategory=true);val w=bind(f).single();f.categories[0].name="Renamed";val(adapter,db,_)=setup();check(runCatching{sync{adapter.restoreBoundNewOnly(listOf(w))}}.isFailure);check(db.parent==null)}
    ok("late parent mutation forces rollback before commit") {
        val f=fixture();val w=bind(f).single();val(adapter,db,d)=setup()
        db.beforeParentInsert = {f.manga.title="RACED EDIT"}
        check(runCatching{sync{adapter.restoreBoundNewOnly(listOf(w))}}.isFailure)
        check(db.parent==null && db.chapters.isEmpty() && db.ledger.isEmpty() && d.rollbackCount==1)
    }
    ok("late link mutation forces rollback before commit") {
        val f=fixture();val w=bind(f).single();val(adapter,db,d)=setup()
        db.beforeParentInsert = {f.work.links[0].sourceUrl="/new"}
        check(runCatching{sync{adapter.restoreBoundNewOnly(listOf(w))}}.isFailure)
        check(db.parent==null && db.edges.isEmpty() && db.ledger.isEmpty() && d.rollbackCount==1)
    }
    ok("late category mutation forces rollback before commit") {
        val f=fixture(withCategory=true);val w=bind(f).single();val(adapter,db,d)=setup()
        db.beforeParentInsert = {f.categories[0].name="Late"}
        check(runCatching{sync{adapter.restoreBoundNewOnly(listOf(w))}}.isFailure)
        check(db.parent==null && db.categories.isEmpty() && db.ledger.isEmpty() && d.rollbackCount==1)
    }
    println("POLARIS_V2_BOUND_RESTORE_BRIDGE_PASS $passed")
}
