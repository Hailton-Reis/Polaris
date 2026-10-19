package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.parent.PolarisParentMetadataRestorePlanner as Planner

private const val U1 = "123e4567-e89b-42d3-a456-426614174000"
private const val U2 = "123e4567-e89b-42d3-a456-426614174001"
private var cases = 0
private fun ok(name: String, checkBlock: () -> Unit) {
    checkBlock(); cases++; println("PASS $cases $name")
}
private fun fail(name: String, checkBlock: () -> Unit) = ok(name) {
    check(runCatching { checkBlock() }.isFailure)
}
private val root = BackupPolarisMergeSettings(false, false, 0, 0, false)
private val child = BackupPolarisMergeSettings(true, true, 0, 1, true)
private fun work(uuid: String = U1, title: String = "One") = BackupPolarisWork(
    uuid, title, root, listOf(BackupPolarisLink(77L, "/child/$uuid", "Child", child)), uuid,
)
private fun parent(uuid: String = U1, title: String = "One", ordinal: Int = 1,
    url: String = "merged://$uuid", categories: List<Long> = listOf(4,7)) =
    BackupPolarisParentPayload(uuid, BackupManga(6969L, url, title, notes = "KEEP NOTES",
        categories = categories, chapters = listOf("/chapter/1"), history = listOf("/read"),
        tracking = listOf("anilist"), memo = byteArrayOf(4,5,6)), ordinal)
private fun archive() = BackupPolarisBundle(2, listOf(work()), emptyList(), listOf(parent()))
private fun ordinary(uuid: String = U1) = listOf(BackupManga(77L, "/child/$uuid", "Child"))
private val mapping = mapOf(4L to 91L, 7L to 92L)
private fun existing(uuid: String = U1, state: Planner.MetadataDisposition = Planner.MetadataDisposition.EMPTY_PLACEHOLDER,
    id: Long = 500L, url: String = "merged://polaris/$uuid", source: Long = 6969L) =
    Planner.ExistingParentRow(id, uuid, source, url, state)
private fun plan(b: BackupPolarisBundle = archive(), ordinary: List<BackupManga> = ordinary(),
    rows: Map<String,List<Planner.ExistingParentRow>> = emptyMap(), cats: Map<Long,Long> = mapping) =
    Planner.prepare(b, ordinary, rows, cats)

fun main() {
    ok("new parent preserves full snapshot by reference") {
        val b=archive(); val result=plan(b).single()
        check(result.operation==Planner.Operation.CREATE_AND_APPLY && result.existingParentId==null)
        check(result.fullBackupManga===b.parentSnapshots.single().manga)
        check(result.fullBackupManga.notes=="KEEP NOTES" && result.fullBackupManga.chapters==listOf("/chapter/1"))
        check(result.fullBackupManga.history==listOf("/read") && result.fullBackupManga.tracking==listOf("anilist"))
        check(result.fullBackupManga.memo.contentEquals(byteArrayOf(4,5,6)))
    }
    ok("archives category IDs mapped into destination category IDs") {
        check(plan().single().mappedCategoryIds==listOf(91L,92L))
    }
    ok("empty precreated matching parent is reused, not duplicated") {
        val p=plan(rows=mapOf(U1 to listOf(existing()))).single()
        check(p.operation==Planner.Operation.APPLY_TO_EMPTY && p.existingParentId==500L)
    }
    ok("identical replay becomes no-op on same stable parent") {
        val p=plan(rows=mapOf(U1 to listOf(existing(state=Planner.MetadataDisposition.IDENTICAL_TO_ARCHIVE)))).single()
        check(p.operation==Planner.Operation.ALREADY_IDENTICAL && p.existingParentId==500L)
    }
    fail("local changes refuse overwrite") {
        plan(rows=mapOf(U1 to listOf(existing(state=Planner.MetadataDisposition.CONFLICT_OR_UNVERIFIED))))
    }
    fail("two rows claim one UUID") { plan(rows=mapOf(U1 to listOf(existing(),existing(id=501)))) }
    fail("invalid local ID refused") { plan(rows=mapOf(U1 to listOf(existing(id=0)))) }
    fail("foreign source row cannot hijack UUID") { plan(rows=mapOf(U1 to listOf(existing(source=77L)))) }
    fail("URL mismatch refuses silent relink") { plan(rows=mapOf(U1 to listOf(existing(url="merged://different")))) }
    fail("UUID ledger mismatch refused") { plan(rows=mapOf(U1 to listOf(existing(uuid=U2)))) }
    fail("missing category mapping refused") { plan(cats=mapOf(4L to 91L)) }
    fail("foreign category ID refused") { plan(cats=mapOf(4L to 91L,7L to -1L)) }
    fail("distinct archive categories cannot collapse into one local category") { plan(cats=mapOf(4L to 91L,7L to 91L)) }
    ok("empty category list needs no mapping") {
        val b=archive().copy(parentSnapshots=listOf(parent(categories=emptyList())))
        check(plan(b,cats=emptyMap()).single().mappedCategoryIds.isEmpty())
    }
    fail("v1 cannot be interpreted as full-parent restore") {
        plan(archive().copy(formatVersion=1,parentSnapshots=emptyList()))
    }
    fail("no snapshot must fail rather than create empty parent") {
        plan(archive().copy(parentSnapshots=emptyList()))
    }
    fail("ordinary virtual parent duplication refused") {
        plan(ordinary=ordinary()+parent().manga)
    }
    fail("missing child snapshot refused") { plan(ordinary=emptyList()) }
    fail("snapshot with different parent source refused") {
        val b=archive().copy(parentSnapshots=listOf(parent().copy(manga=BackupManga(77L,"/child/$U1","One"))))
        plan(b)
    }
    fail("snapshot parent title changed refused") {
        plan(archive().copy(parentSnapshots=listOf(parent(title="Changed"))))
    }
    ok("two distinct parents have one plan each and distinct category mappings") {
        val b=archive().copy(works=listOf(work(),work(U2,"Two")),
            parentSnapshots=listOf(parent(),parent(U2,"Two",ordinal=2)))
        val p=plan(b,ordinary()+ordinary(U2),rows=mapOf(U1 to listOf(existing())) )
        check(p.map { it.canonicalUuid }==listOf(U1,U2))
        check(p.map { it.operation }==listOf(Planner.Operation.APPLY_TO_EMPTY,Planner.Operation.CREATE_AND_APPLY))
    }
    fail("two UUIDs cannot reuse same local manga ID") {
        val b=archive().copy(works=listOf(work(),work(U2,"Two")),
            parentSnapshots=listOf(parent(),parent(U2,"Two",ordinal=2)))
        plan(b,ordinary()+ordinary(U2),rows=mapOf(U1 to listOf(existing()),U2 to listOf(existing(U2,id=500L))))
    }
    ok("unknown unrelated UUID ledger entries do not affect this archive") {
        check(plan(rows=mapOf(U2 to listOf(existing(U2)))).single().operation==Planner.Operation.CREATE_AND_APPLY)
    }
    fail("duplicate archive UUID rejected by v2") {
        val b=archive().copy(works=listOf(work(),work()),parentSnapshots=listOf(parent(),parent(ordinal=2)))
        plan(b)
    }
    fail("v2 ordinal collision rejected") {
        val b=archive().copy(works=listOf(work(),work(U2,"Two")),
            parentSnapshots=listOf(parent(),parent(U2,"Two",ordinal=1)))
        plan(b,ordinary()+ordinary(U2))
    }
    ok("archived source URL differs from the UUID-stable destination parent URL") {
        val result = plan(rows=mapOf(U1 to listOf(existing(url="merged://polaris/$U1")))).single()
        check(result.operation == Planner.Operation.APPLY_TO_EMPTY)
        check(result.destinationUrl == "merged://polaris/$U1")
        check(result.fullBackupManga.url == "merged://$U1")
    }
    fail("reject replay against legacy local URL lacking UUID-stable destination identity") {
        plan(rows=mapOf(U1 to listOf(existing(url="merged://$U1"))))
    }
    ok("new parent operation targets UUID-stable local URL without mutating archive") {
        val result = plan().single()
        check(result.destinationUrl == "merged://polaris/$U1")
        check(result.fullBackupManga.url == "merged://$U1")
    }
    println("POLARIS_PARENT_METADATA_RESTORE_PLAN_PASS $cases")
}
