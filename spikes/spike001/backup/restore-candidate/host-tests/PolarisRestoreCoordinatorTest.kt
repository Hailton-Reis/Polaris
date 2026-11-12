package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.*
import kotlin.coroutines.*

private const val A = "123e4567-e89b-42d3-a456-426614174000"
private const val B = "123e4567-e89b-42d3-a456-426614174001"
private var number = 0
private fun scenario(label: String, run: () -> Unit) {
    run(); number++; println("RESTORE_COORDINATOR_PASS $number $label")
}
private fun rejected(run: () -> Unit) { check(runCatching(run).isFailure) }
private fun <T> call(suspendBlock: suspend () -> T): T {
    var result: Result<T>? = null
    suspendBlock.startCoroutine(object : Continuation<T> {
        override val context: CoroutineContext = EmptyCoroutineContext
        override fun resumeWith(value: Result<T>) { result = value }
    })
    return checkNotNull(result).getOrThrow()
}
private val settings = BackupPolarisMergeSettings(false,true,2,1,false)
private fun link(source: Long, url: String, pending: Boolean=false) =
    BackupPolarisLink(source,url,"Work "+url,settings,pending)
private fun work(uuid: String=A, links: List<BackupPolarisLink> = listOf(link(11,"/a"),link(12,"/b"))) =
    BackupPolarisWork(uuid,"Work",settings,links,uuid)
private fun archive(works: List<BackupPolarisWork> = listOf(work()), extra: List<BackupManga> = listOf(BackupManga(12,"/b"))) =
    BackupPolarisBundle(works=works,supplementalManga=extra)
private class Fake : PolarisSourceRestorePort, PolarisAtomicVirtualWorkPort {
    val ids = mutableMapOf<Pair<Long,String>,List<Long>>((11L to "/a") to listOf(101L))
    val steps = mutableListOf<String>()
    var failure: Pair<Long,String>? = null
    var failCommit = false
    var committed: List<RestoredPolarisWork>? = null
    override suspend fun restoreSupplementalMangaOrThrow(snapshot: BackupManga) {
        steps += "supplement:" + snapshot.source + ":" + snapshot.url
        if (failure == snapshot.source to snapshot.url) error("child restore failed")
        ids[snapshot.source to snapshot.url] = listOf(202L)
    }
    override suspend fun findMangaIdsBySourceAndUrl(sourceId: Long, sourceUrl: String): List<Long> {
        steps += "lookup:" + sourceId + ":" + sourceUrl
        return ids[sourceId to sourceUrl].orEmpty()
    }
    override suspend fun commitAllOrThrow(works: List<RestoredPolarisWork>) {
        steps += "atomic-parents"
        if (failCommit) error("transaction failure")
        committed = works
    }
}
private fun restore(
    f: Fake, bundle: BackupPolarisBundle? = archive(),
    ordinary: List<BackupManga> = listOf(BackupManga(11,"/a")),
    enabled: Boolean = true,
    normal: suspend () -> Unit = {f.steps += "ordinary-done"},
) = call { PolarisRestoreCoordinator(f,f).restore(bundle,ordinary,enabled,normal) }

fun main() {
    scenario("Ordinary then supplemental child, then one parent commit") {
        val f=Fake();val restored=restore(f).single()
        check(f.steps == listOf("ordinary-done","supplement:12:/b","lookup:11:/a","lookup:12:/b","atomic-parents"))
        check(restored.children.map{it.realMangaId}==listOf(101L,202L))
    }
    scenario("Preserves true source IDs and URLs") {
        val f=Fake();check(restore(f).single().children.map{it.sourceId to it.sourceUrl}==listOf(11L to "/a",12L to "/b"))
    }
    scenario("Ordinary child failure blocks all subsequent stages") {
        val f=Fake();rejected{restore(f,normal={error("ordinary failed")})};check(f.steps.isEmpty())
    }
    scenario("Supplemental child restore failure blocks parent writes") {
        val f=Fake();f.failure=12L to "/b";rejected{restore(f)};check(f.committed==null)
    }
    scenario("Missing real child after restore blocks parent") {
        val f=Fake();f.ids.clear();rejected{restore(f)};check(f.committed==null)
    }
    scenario("Duplicate source URL candidates block parent") {
        val f=Fake();f.ids[11L to "/a"]=listOf(101,102).map(Int::toLong);rejected{restore(f)};check(f.committed==null)
    }
    scenario("Two real sources cannot reuse one local manga ID") {
        val f=Fake();f.ids[11L to "/a"]=listOf(202L);rejected{restore(f)};check(f.committed==null)
    }
    scenario("Explicitly pending link stays NULL even if real row exists") {
        val f=Fake();f.ids[12L to "/b"]=listOf(202L)
        val b=archive(works=listOf(work(links=listOf(link(11,"/a"),link(12,"/b",true)))),extra=emptyList())
        val w=restore(f,b).single();check(w.children.last().realMangaId==null && w.children.last().wasPending)
    }
    scenario("Same child can be pending for one work and resolved for another") {
        val f=Fake();val b=archive(works=listOf(work(links=listOf(link(11,"/a"),link(12,"/b",true))),work(B,listOf(link(12,"/b")))))
        val ws=restore(f,b);check(ws[0].children.last().realMangaId==null && ws[1].children.single().realMangaId==202L)
    }
    scenario("Library restore option disabled is a no-op") {
        val f=Fake();check(restore(f,enabled=false).isEmpty() && f.steps.isEmpty())
    }
    scenario("Legacy backup without Polaris segment is a no-op") {
        val f=Fake();check(restore(f,bundle=null).isEmpty() && f.steps.isEmpty())
    }
    scenario("Unknown portable backup version fails preflight") {
        val f=Fake();rejected{restore(f,bundle=archive().copy(formatVersion=2))};check(f.steps.isEmpty())
    }
    scenario("Missing resolved snapshot fails before ordinary restore") {
        val f=Fake();rejected{restore(f,bundle=archive(extra=emptyList()))};check(f.steps.isEmpty())
    }
    scenario("Invalid parent UUID fails before any writes") {
        val f=Fake();rejected{restore(f,bundle=archive(works=listOf(work("not-uuid"))))};check(f.steps.isEmpty())
    }
    scenario("Parent archive ID must agree with canonical UUID") {
        val f=Fake();rejected{restore(f,bundle=archive(works=listOf(work().copy(canonicalUuid=B))))};check(f.steps.isEmpty())
    }
    scenario("Duplicate parent archive key is rejected") {
        val f=Fake();rejected{restore(f,bundle=archive(works=listOf(work(),work()),extra=emptyList()))};check(f.steps.isEmpty())
    }
    scenario("Atomic parent writer failures propagate to caller") {
        val f=Fake();f.failCommit=true;rejected{restore(f)};check(f.committed==null)
    }
    scenario("Multiple parents are submitted for one atomic commit") {
        val f=Fake();val r=restore(f,bundle=archive(works=listOf(work(),work(B))))
        check(r.size==2 && f.steps.count{it=="atomic-parents"}==1)
    }
    scenario("Pending-only work does not need child snapshots") {
        val f=Fake();val b=archive(works=listOf(work(links=listOf(link(11,"/gone",true)))),extra=emptyList())
        val w=restore(f,b,ordinary=emptyList()).single();check(w.children.single().realMangaId==null)
    }
    scenario("Malformed synthetic child rejected independently of restore jobs") {
        val f=Fake();rejected{PolarisRestoreCoordinator(f,f).preflight(
            archive(works=listOf(work(links=listOf(link(6969,"/fake")))),extra=emptyList()),
            emptyList(),true
        )};check(f.steps.isEmpty())
    }
    println("POLARIS_YOMOTSU_RESTORE_COORDINATOR_PASS $number")
}
