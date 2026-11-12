package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.restore.PolarisRestoreCoordinator
import polaris.spike001.backup.restore.PolarisAtomicVirtualWorkPort
import polaris.spike001.backup.restore.PolarisSourceRestorePort
import polaris.spike001.backup.restore.RestoredPolarisWork

private const val U1 = "123e4567-e89b-42d3-a456-426614174000"
private const val U2 = "123e4567-e89b-42d3-a456-426614174001"
private var checks = 0
private fun yes(name: String, block: () -> Unit) { block(); checks++; println("PASS $checks $name") }
private fun no(name: String, block: () -> Unit) = yes(name) { check(runCatching(block).isFailure) }
private val settings = BackupPolarisMergeSettings(false, false, 2, 999, false)
private val childSettings = BackupPolarisMergeSettings(true, true, 2, 1, true)
private fun w(uuid: String = U1, title: String = "My work", url: String = "/chapter") =
    BackupPolarisWork(uuid, title, settings,
        listOf(BackupPolarisLink(11, url, "Child", childSettings)), uuid)
private fun m(url: String = "merged://original", title: String = "My work") =
    BackupManga(6969, url, title, notes = "MY NOTES", categories = listOf(4,7),
        chapters = listOf("/c1"), history = listOf("/h1"), tracking = listOf("t1"),
        memo = byteArrayOf(0,1,2,3))
private fun p(uuid: String = U1, ordinal: Int = 1, url: String = "merged://original", title: String = "My work") =
    BackupPolarisParentPayload(uuid, m(url,title), ordinal)
private fun full() = BackupPolarisBundle(formatVersion=2,works=listOf(w()),
    parentSnapshots=listOf(p()))
private fun valid(x: BackupPolarisBundle = full())=x.validateSnapshotCoverage(listOf(BackupManga(11, "/chapter", "Child")))
private fun split() = PolarisParentSnapshotPartitioner.partition(listOf(
    CapturedMangaSnapshot(101,11,"/chapter",BackupManga(11,"/chapter","Child")),
    CapturedMangaSnapshot(900,6969,"merged://original",m()),
),listOf(ExpectedVirtualParent(900,U1,"merged://original","My work")))
private val coordinator by lazy {
    PolarisRestoreCoordinator(object : PolarisSourceRestorePort {
        override suspend fun restoreSupplementalMangaOrThrow(snapshot: BackupManga) = Unit
        override suspend fun findMangaIdsBySourceAndUrl(sourceId:Long,sourceUrl:String)=listOf(101L)
    },object : PolarisAtomicVirtualWorkPort {
        override suspend fun commitAllOrThrow(works:List<RestoredPolarisWork>) = Unit
    })
}
fun main(){
    yes("v2 exact full parent payload validates") { valid() }
    yes("v2 preserves full notes categories chapters history tracks memo") {
        val data=full().parentSnapshots.single().manga
        check(data.notes=="MY NOTES"&&data.categories==listOf(4L,7L)&&data.chapters==listOf("/c1") && data.history==listOf("/h1")&&data.tracking==listOf("t1")&&data.memo.contentEquals(byteArrayOf(0,1,2,3)))
    }
    no("v2 cannot contain no works") { valid(full().copy(works=emptyList())) }
    no("v2 cannot omit parent payload") { valid(full().copy(parentSnapshots=emptyList())) }
    no("v2 cannot contain extra parent payload") { valid(full().copy(parentSnapshots=full().parentSnapshots+full().parentSnapshots.first())) }
    no("v2 parent UUID cannot drift from work") { valid(full().copy(parentSnapshots=listOf(p(U2)))) }
    no("v2 parent UUID must be canonical") { valid(full().copy(works=listOf(w("NOT_UUID")),parentSnapshots=listOf(p("NOT_UUID")))) }
    no("v2 invalid parent original index") { valid(full().copy(parentSnapshots=listOf(p(ordinal=-1)))) }
    no("v2 cannot use real child in virtual parent slot") { valid(full().copy(parentSnapshots=listOf(BackupPolarisParentPayload(U1,BackupManga(11,"/chapter"),1)))) }
    no("v2 cannot lose parent title") { valid(full().copy(parentSnapshots=listOf(p(title="Changed")))) }
    no("v2 cannot use empty parent URL") { valid(full().copy(parentSnapshots=listOf(p(url="")))) }
    no("v2 must preserve canonical UUID") { valid(full().copy(works=listOf(w().copy(canonicalUuid=null)))) }
    no("v2 cannot carry duplicated parent URLs") {
        valid(full().copy(works=listOf(w(),w(U2,"Second","/other")),parentSnapshots=listOf(p(),p(U2,2,"merged://original","Second"))))
    }
    no("v2 cannot carry duplicate original ordinal") {
        valid(full().copy(works=listOf(w(),w(U2,"Second","/other")),parentSnapshots=listOf(p(),p(U2,1,"merged://second","Second"))))
    }
    no("v2 missing resolved child is invalid") { full().validateSnapshotCoverage(emptyList()) }
    no("v2 ordinary virtual parent is rejected to prevent duplicate") { full().validateSnapshotCoverage(listOf(BackupManga(11,"/chapter"),m())) }
    yes("v1 model remains readable without v2 payload") { BackupPolarisBundle(works=listOf(w())).validateForImport() }
    no("v1 cannot contain v2 payload") { BackupPolarisBundle(works=listOf(w()),parentSnapshots=listOf(p())).validateForImport() }
    no("unknown v3 is rejected") { full().copy(formatVersion=3).validateForImport() }
    yes("partition assembler makes valid v2 without ordinary virtual parent") {
        val base=BackupPolarisBundle(works=listOf(w()))
        val out=PolarisParentBundleAssembler.assemble(base,split())
        check(out.formatVersion==2&&out.parentSnapshots.size==1 && out.parentSnapshots.first().manga.notes=="MY NOTES")
    }
    no("assembler refuses missing captured full metadata") {
        PolarisParentBundleAssembler.assemble(BackupPolarisBundle(works=listOf(w()),parentSnapshots=emptyList()),
            split().copy(virtualParents=emptyList()))
    }
    no("assembler refuses UUID matching different parent") {
        PolarisParentBundleAssembler.assemble(BackupPolarisBundle(works=listOf(w(U2))),split())
    }
    no("assembler rejects v2 as source to prevent nested reassembly") { PolarisParentBundleAssembler.assemble(full(),split()) }
    no("assembler refuses ordinary virtual parent leak") {
        PolarisParentBundleAssembler.assemble(BackupPolarisBundle(works=listOf(w())),split().copy(ordinaryManga=listOf(m(),BackupManga(11,"/chapter")),originalCount=3))
    }
    no("coordinator blocks v2 before any restore port writes") { coordinator.preflight(full(),listOf(BackupManga(11,"/chapter")),true) }
    yes("coordinator still handles empty v1 legacy model") { coordinator.preflight(BackupPolarisBundle(),emptyList(),true) }
    println("POLARIS_PARENT_V2_HOST_PASS $checks")
}
