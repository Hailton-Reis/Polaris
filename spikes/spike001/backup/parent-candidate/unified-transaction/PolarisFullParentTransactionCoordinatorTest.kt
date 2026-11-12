package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.*
import polaris.spike001.backup.restore.*
import kotlin.coroutines.*

private const val U1 = "123e4567-e89b-42d3-a456-426614174000"
private const val U2 = "123e4567-e89b-42d3-a456-426614174001"
private var passed = 0
private fun ok(label: String, test: () -> Unit) { test(); println("PASS ${++passed} $label") }
private fun reject(label: String, test: () -> Unit) = ok(label) { check(runCatching(test).isFailure) { "Expected hard failure: $label" } }
private fun <T> blocking(block: suspend () -> T): T {
    var complete: Result<T>? = null
    block.startCoroutine(object : Continuation<T> {
        override val context: CoroutineContext = EmptyCoroutineContext
        override fun resumeWith(result: Result<T>) { complete = result }
    })
    return checkNotNull(complete) { "Unexpected async suspension; fixture is synchronous" }.getOrThrow()
}
private val root = BackupPolarisMergeSettings(false, false, 2, 999, false)
private val primary = BackupPolarisMergeSettings(true, true, 2, 1, true)
private val secondary = BackupPolarisMergeSettings(false, true, 1, 3, false)
private fun archiveWork(uuid: String, title: String = "Polaris $uuid") = BackupPolarisWork(
    uuid, title, root,
    listOf(BackupPolarisLink(77, "/source/$uuid", "Source", primary, false),
           BackupPolarisLink(88, "/pending/$uuid", "Pending", secondary, true)), uuid,
)
private fun archiveParent(uuid: String, title: String = "Polaris $uuid") =
    BackupPolarisParentPayload(uuid, BackupManga(6969, "merged://legacy/$uuid", title,
        notes = "Notes $uuid", categories = listOf(4, 7),
        chapters = listOf("/c1", "/c2"), history = listOf("/c1"),
        tracking = listOf("tracker"), memo = byteArrayOf(4, 0, 7)), 0)
private fun bundle(vararg uuids: String): BackupPolarisBundle = BackupPolarisBundle(2,
    uuids.map { archiveWork(it) }, emptyList(),
    uuids.mapIndexed { index, uuid -> archiveParent(uuid).copy(originalOrdinal=index) })
private fun ordinary(vararg uuids: String) = uuids.map { BackupManga(77, "/source/$it", "Source") }
private fun resolved(uuid: String): RestoredPolarisWork = RestoredPolarisWork(uuid, "Polaris $uuid", root,
    listOf(RestoredPolarisLink(77,"/source/$uuid", if(uuid==U1) 101 else 102,false,primary),
           RestoredPolarisLink(88,"/pending/$uuid",null,true,secondary)))
private fun categories() = listOf(PolarisArchivedCategory(4,"Read"), PolarisArchivedCategory(7,"Favorites"))
private data class Stored(
    val id:Long, val uuid:String, val source:Long=6969,
    val url:String="merged://polaris/$uuid", val title:String="Polaris $uuid",
    val metadata:BackupManga?=null, val categoryIds:List<Long> = emptyList(),
    val links:RestoredPolarisWork?=null, val dirty:Boolean=false,
)

private class FakePort : PolarisFullParentAtomicTransactionPort {
    var stored = mutableListOf<Stored>()
    var availableCategories = mutableMapOf("Read" to listOf(91L), "Favorites" to listOf(92L))
    var childIds = mutableMapOf((77L to "/source/$U1") to listOf(101L), (77L to "/source/$U2") to listOf(102L))
    var failAfterWrite: Int? = null
    var skipMetadata = false
    var urlCollision = false
    var transactions = 0
    var commits = 0
    var writes = 0
    var assertions = 0
    var physicalReads = 0
    var events = mutableListOf<String>()
    override suspend fun <T> transaction(block: suspend PolarisFullParentTransaction.() -> T): T {
        transactions++
        val before = stored.toList()
        val fake = object : PolarisFullParentTransaction {
            val shadow = before.toMutableList()
            var writesInTransaction = 0
            fun same(a: BackupManga?, b: BackupManga): Boolean = a != null &&
                a.source == b.source && a.url == b.url && a.title == b.title &&
                a.notes == b.notes && a.categories == b.categories &&
                a.chapters == b.chapters && a.history == b.history &&
                a.tracking == b.tracking && a.memo.contentEquals(b.memo)
            override suspend fun findAllParentsClaimingUuid(uuid: String): List<PolarisParentMetadataRestorePlanner.ExistingParentRow> {
                physicalReads++
                return shadow.filter { it.uuid == uuid }.map { existing ->
                    val mode = when {
                        existing.dirty -> PolarisParentMetadataRestorePlanner.MetadataDisposition.CONFLICT_OR_UNVERIFIED
                        existing.metadata == null -> PolarisParentMetadataRestorePlanner.MetadataDisposition.EMPTY_PLACEHOLDER
                        else -> PolarisParentMetadataRestorePlanner.MetadataDisposition.IDENTICAL_TO_ARCHIVE
                    }
                    PolarisParentMetadataRestorePlanner.ExistingParentRow(
                        existing.id, existing.uuid, existing.source, existing.url, mode)
                }
            }
            override suspend fun localCategoryIdsByName(name: String): List<Long> = availableCategories[name].orEmpty().also { physicalReads++ }
            override suspend fun exactRealChildIds(source: Long, url: String): List<Long> = childIds[source to url].orEmpty().also { physicalReads++ }
            override suspend fun requireNoUntrackedParentIdentity(uuid: String, destinationUrl: String) {
                check(!urlCollision && shadow.none { it.url == destinationUrl || it.uuid == uuid }) { "Untracked parent collision" }
                events.add("identity:$uuid")
            }
            fun afterWrite() {
                writesInTransaction++; writes++
                if (failAfterWrite == writesInTransaction) error("Injected transactional failure")
            }
            override suspend fun createAndApplyFullParent(
                command: PolarisParentMetadataRestorePlanner.ParentRestoreCommand, associations: RestoredPolarisWork
            ): Long {
                val newId = (shadow.maxOfOrNull { it.id } ?: 500L) + 1L
                shadow.add(Stored(newId, command.canonicalUuid, url=command.destinationUrl,
                    metadata=if(skipMetadata) null else command.fullBackupManga,
                    categoryIds=command.mappedCategoryIds, links=associations))
                events.add("write:${command.canonicalUuid}")
                afterWrite()
                return newId
            }
            override suspend fun applyToVerifiedEmptyParent(
                parentId: Long, command: PolarisParentMetadataRestorePlanner.ParentRestoreCommand, associations: RestoredPolarisWork
            ) {
                val index = shadow.indexOfFirst { it.id == parentId }
                check(index >= 0 && shadow[index].metadata == null && !shadow[index].dirty) { "Not empty" }
                shadow[index]=shadow[index].copy(metadata=if(skipMetadata) null else command.fullBackupManga,
                    categoryIds=command.mappedCategoryIds, links=associations)
                events.add("apply:${command.canonicalUuid}")
                afterWrite()
            }
            override suspend fun assertExactFullParentState(
                parentId: Long, command: PolarisParentMetadataRestorePlanner.ParentRestoreCommand, associations: RestoredPolarisWork
            ) {
                assertions++
                val rows = shadow.filter { it.id == parentId }
                check(rows.size == 1) { "Missing or duplicated parent" }
                val found = rows.single()
                check(!found.dirty && found.uuid == command.canonicalUuid && found.source == 6969L &&
                    found.url == command.destinationUrl && found.title == command.fullBackupManga.title &&
                    same(found.metadata,command.fullBackupManga) && found.categoryIds == command.mappedCategoryIds &&
                    found.links == associations) { "Physical full-parent readback differs" }
                events.add("readback:${command.canonicalUuid}")
            }
        }
        return try {
            val value = block(fake)
            stored = fake.shadow
            commits++
            events.add("commit")
            value
        } catch(t:Throwable) {
            stored=before.toMutableList()
            events.add("rollback")
            throw t
        }
    }
}
private fun run(port: FakePort, vararg uuids:String,
    archive: BackupPolarisBundle = bundle(*uuids),
    plain:List<BackupManga> = ordinary(*uuids),
    works:List<RestoredPolarisWork> = uuids.map { resolved(it) },
    cats:List<PolarisArchivedCategory> = categories()
) = blocking { PolarisFullParentTransactionCoordinator(port).restore(archive,plain,works,cats) }
private fun seeded(port:FakePort, uuid:String=U1, id:Long=501):Long {
    run(port,uuid)
    return port.stored.single { it.uuid==uuid }.id
}
fun main() {
    ok("fresh complete parent is created under UUID URL") {
        val p=FakePort();val out=run(p,U1)
        check(out.parentIdsByUuid == mapOf(U1 to 501L) && p.stored.single().url=="merged://polaris/$U1")
        check(p.commits==1 && p.assertions==1 && p.transactions==1)
    }
    ok("preserves complete host BackupManga including notes, history and memo") {
        val p=FakePort();run(p,U1);val m=checkNotNull(p.stored.single().metadata)
        check(m.notes=="Notes $U1" && m.history==listOf("/c1") && m.memo.contentEquals(byteArrayOf(4,0,7)))
    }
    ok("pending source association remains NULL") {
        val p=FakePort();run(p,U1);check(p.stored.single().links!!.children[1].realMangaId==null)
    }
    ok("category order resolves to destination IDs inside transaction") {
        val p=FakePort();run(p,U1);check(p.stored.single().categoryIds==listOf(91L,92L))
    }
    ok("exact replay returns existing parent and no new writes") {
        val p=FakePort();val id=seeded(p);val w=p.writes;check(run(p,U1).parentIdsByUuid[U1]==id)
        check(p.writes==w && p.assertions==2 && p.stored.size==1)
    }
    ok("precreated empty placeholder receives full metadata on same ID") {
        val p=FakePort();p.stored.add(Stored(867,U1))
        check(run(p,U1).parentIdsByUuid[U1]==867L && p.stored.single().metadata!=null)
    }
    reject("replay refuses locally edited data") {
        val p=FakePort();seeded(p);p.stored[0]=p.stored[0].copy(dirty=true);run(p,U1)
    }
    reject("replay readback rejects changed local chapter state") {
        val p=FakePort();seeded(p)
        p.stored[0]=p.stored[0].copy(metadata=BackupManga(6969,"merged://other","Changed"))
        run(p,U1)
    }
    ok("two parents and their metadata commit in one transaction") {
        val p=FakePort();val out=run(p,U1,U2)
        check(out.parentIdsByUuid.size==2 && out.parentIdsByUuid.values.toSet().size==2)
        check(p.commits==1 && p.transactions==1 && p.stored.size==2 && p.assertions==2)
    }
    ok("injected second write failure rolls back first parent") {
        val p=FakePort();p.failAfterWrite=2
        check(runCatching{run(p,U1,U2)}.isFailure)
        check(p.stored.isEmpty() && p.commits==0 && p.events.last()=="rollback")
    }
    ok("failed readback rolls back new parent") {
        val p=FakePort();p.skipMetadata=true
        check(runCatching{run(p,U1)}.isFailure)
        check(p.stored.isEmpty() && p.commits==0)
    }
    ok("failed readback rolls back update to existing empty parent") {
        val p=FakePort();p.stored.add(Stored(900,U1));p.skipMetadata=true
        check(runCatching{run(p,U1)}.isFailure)
        check(p.stored.single().id==900L && p.stored.single().metadata==null)
    }
    reject("resolved child changed local source identity") {
        val p=FakePort();p.childIds[77L to "/source/$U1"]=listOf(999);run(p,U1)
    }
    reject("ambiguous child lookup rejects before any parent write") {
        val p=FakePort();p.childIds[77L to "/source/$U1"]=listOf(101,202);run(p,U1)
    }
    reject("missing resolved source child rejects") {
        val p=FakePort();p.childIds.clear();run(p,U1)
    }
    ok("pending key is never resolved even if database has a match") {
        val p=FakePort();p.childIds[88L to "/pending/$U1"]=listOf(888);run(p,U1)
        check(p.stored.single().links!!.children.last().realMangaId==null)
    }
    reject("missing category name fails before a write") {
        val p=FakePort();p.availableCategories.remove("Read");run(p,U1)
    }
    reject("ambiguous destination category by name fails") {
        val p=FakePort();p.availableCategories["Read"]=listOf(91,92);run(p,U1)
    }
    reject("two archive category orders cannot map to same destination ID") {
        val p=FakePort();p.availableCategories["Read"]=listOf(92);run(p,U1)
    }
    reject("duplicate archive order rejects") {
        run(FakePort(),U1,cats=categories()+PolarisArchivedCategory(4,"Other"))
    }
    reject("duplicate archive category names rejects") {
        run(FakePort(),U1,cats=listOf(PolarisArchivedCategory(4,"Read"),PolarisArchivedCategory(7,"Read")))
    }
    reject("archived category order missing") {
        run(FakePort(),U1,cats=listOf(PolarisArchivedCategory(4,"Read")))
    }
    reject("portable source differs from resolved child URL") {
        val works=listOf(resolved(U1).copy(children=listOf(resolved(U1).children[0].copy(sourceUrl="/wrong"),resolved(U1).children[1])))
        run(FakePort(),U1,works=works)
    }
    reject("child pending link cannot silently become resolved") {
        val w=resolved(U1);run(FakePort(),U1,works=listOf(w.copy(children=w.children.mapIndexed { i,x -> if(i==1)x.copy(realMangaId=123,wasPending=false) else x })))
    }
    reject("non-pending child cannot disappear") {
        val w=resolved(U1);run(FakePort(),U1,works=listOf(w.copy(children=w.children.mapIndexed { i,x -> if(i==0)x.copy(realMangaId=null,wasPending=true) else x })))
    }
    reject("child settings change after archive decoded") {
        val w=resolved(U1);run(FakePort(),U1,works=listOf(w.copy(children=w.children.mapIndexed { i,x -> if(i==0)x.copy(settings=secondary) else x })))
    }
    reject("root settings change during restore") {
        run(FakePort(),U1,works=listOf(resolved(U1).copy(rootSettings=secondary)))
    }
    reject("work title change during restore") {
        run(FakePort(),U1,works=listOf(resolved(U1).copy(title="Changed")))
    }
    reject("reordered links cannot silently align unrelated source") {
        val w=resolved(U1);run(FakePort(),U1,works=listOf(w.copy(children=w.children.reversed())))
    }
    reject("resolved work UUID differs from archive") {
        run(FakePort(),U1,works=listOf(resolved(U2)))
    }
    reject("duplicate resolved work UUID fails") {
        run(FakePort(),U1,U2,works=listOf(resolved(U1),resolved(U1)))
    }
    reject("same local real ID across distinct source identities is unsafe") {
        val w2=resolved(U2);val shifted=w2.copy(children=w2.children.mapIndexed{i,x->if(i==0)x.copy(realMangaId=101L) else x})
        run(FakePort(),U1,U2,works=listOf(resolved(U1),shifted))
    }
    reject("duplicate virtual parent rows reject before write") {
        val p=FakePort();p.stored.add(Stored(501,U1));p.stored.add(Stored(502,U1));run(p,U1)
    }
    reject("wrong UUID URL on existing parent rejects") {
        val p=FakePort();p.stored.add(Stored(700,U1,url="merged://legacy/5"));run(p,U1)
    }
    reject("wrong source on existing parent rejects") {
        val p=FakePort();p.stored.add(Stored(700,U1,source=77));run(p,U1)
    }
    reject("untracked UUID URL collision is not reused") {
        val p=FakePort();p.urlCollision=true;run(p,U1)
    }
    reject("two parent UUIDs cannot claim same existing manga ID") {
        val p=FakePort();p.stored.add(Stored(501,U1));p.stored.add(Stored(501,U2));run(p,U1,U2)
    }
    ok("existing one plus fresh second commit under same transaction") {
        val p=FakePort();val id=seeded(p,U1);val out=run(p,U1,U2)
        check(out.parentIdsByUuid[U1]==id && out.parentIdsByUuid[U2]!=id && p.stored.size==2)
    }
    reject("v1 cannot use v2 full-parent transaction") {
        run(FakePort(),U1,archive=BackupPolarisBundle(1, listOf(archiveWork(U1))))
    }
    reject("ordinary lane virtual parent causes duplicate protection") {
        run(FakePort(),U1,plain=ordinary(U1)+archiveParent(U1).manga)
    }
    reject("missing ordinary child snapshot fails before transaction") {
        run(FakePort(),U1,plain=emptyList())
    }
    reject("wrong full-parent snapshot title aborts") {
        val b=bundle(U1).copy(parentSnapshots=listOf(archiveParent(U1,title="Wrong")))
        run(FakePort(),U1,archive=b)
    }
    ok("validation fails before transaction begins") {
        val p=FakePort();check(runCatching { run(p,U1,plain=emptyList()) }.isFailure)
        check(p.transactions==0 && p.writes==0)
    }
    ok("transaction validates physical children before writing any parent") {
        val p=FakePort();p.childIds[77L to "/source/$U2"]=emptyList()
        check(runCatching{run(p,U1,U2)}.isFailure)
        check(p.writes==0 && p.stored.isEmpty())
    }
    println("POLARIS_FULL_PARENT_UNIFIED_KOTLIN_PASS $passed")
}