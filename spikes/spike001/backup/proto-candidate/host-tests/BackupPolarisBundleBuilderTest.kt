package polaris.spike001.backup

import eu.kanade.tachiyomi.data.backup.models.BackupManga

private var count = 0
private fun test(name: String, body: () -> Unit) { body(); count++; println("BUILDER_PASS $count: $name") }
private fun fails(body: () -> Unit) { check(runCatching(body).isFailure) }

fun main() {
    val a = SourceWorkIdentity(10, "/a")
    val b = SourceWorkIdentity(20, "/b")
    val c = SourceWorkIdentity(30, "/c")
    val settings = PortableMergeSettings(false, true, 2, 1, false)
    val root = settings.copy(getChapterUpdates=false, chapterPriority=999)
    val catalog = listOf(LocalSourceWork(a,101), LocalSourceWork(b,102), LocalSourceWork(c,103))
    val work = ExportVirtualWork(900, 6969, "work-A", "A title", listOf(
        ExportMergedChildLink(a,101,"a",settings.copy(infoManga=true)),
        ExportMergedChildLink(b,102,"b",settings),
    ), root)
    fun assemble(
        works: List<ExportVirtualWork> = listOf(work),
        normal: List<BackupManga> = listOf(BackupManga(10,"/a")),
        extra: List<BackupManga> = listOf(BackupManga(20,"/b")),
        pool: List<LocalSourceWork> = catalog,
        replace: ((MergedBackupExportPlan) -> MergedBackupExportPlan)? = null,
    ): eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle {
        val plan = MergedBackupExportPlanner.plan(works,pool,setOf(900,101),true)
        return BackupPolarisBundleBuilder.build(replace?.invoke(plan) ?: plan,works,pool,normal,extra)
    }
    test("Resolved nonfavorite child included once") {
        val dto = assemble()
        check(dto.supplementalManga.map {it.url} == listOf("/b"))
        check(dto.works.single().links.none {it.isPending})
    }
    test("Missing supplementary snapshots rejected") { fails { assemble(extra=emptyList()) } }
    test("Wrong source URL rejected") { fails { assemble(extra=listOf(BackupManga(20,"/WRONG"))) } }
    test("Wrong source ID rejected") { fails { assemble(extra=listOf(BackupManga(10,"/b"))) } }
    test("Duplicated supplementary snapshots rejected") { fails {assemble(extra=listOf(BackupManga(20,"/b"),BackupManga(20,"/b")))} }
    test("Unexpected supplementary records rejected") { fails { assemble(extra=listOf(BackupManga(20,"/b"),BackupManga(30,"/c"))) } }
    test("Same snapshot cannot occur in both backup sections") { fails {assemble(normal=listOf(BackupManga(10,"/a"),BackupManga(20,"/b")))} }
    test("Missing already-selected ordinary child rejected") { fails { assemble(normal=emptyList()) } }
    test("Duplicate ordinary source identity rejected") { fails { assemble(normal=listOf(BackupManga(10,"/a"),BackupManga(10,"/a"))) } }
    test("Pending orphan requires no fabricated child snapshot") {
        val orphan=work.copy(links=listOf(work.links[0],work.links[1].copy(localMangaId=null)))
        val dto=assemble(works=listOf(orphan),extra=emptyList())
        check(dto.works.single().links[1].isPending)
        dto.validateSnapshotCoverage(listOf(BackupManga(10,"/a")))
    }
    test("Resolved link in one parent, pending in another retains separate flags") {
        val pending=work.copy(parentLocalId=901,archiveWorkKey="work-B",links=listOf(work.links[1].copy(localMangaId=null)))
        val dto=assemble(works=listOf(work,pending),normal=listOf(BackupManga(10,"/a")))
        check(!dto.works[0].links[1].isPending && dto.works[1].links[0].isPending)
        check(dto.supplementalManga.size==1)
    }
    test("Two resolved parents sharing child snapshot avoid repeats") {
        val second=work.copy(parentLocalId=901,archiveWorkKey="work-B",links=listOf(work.links[1]))
        val dto=assemble(works=listOf(work,second))
        check(dto.supplementalManga.size == 1)
    }
    test("Linked source changed between planning and payload assembly rejected") {
        val changed=work.copy(links=listOf(work.links[0].copy(title="new title"),work.links[1]))
        val plan=MergedBackupExportPlanner.plan(listOf(work),catalog,setOf(900,101),true)
        fails { BackupPolarisBundleBuilder.build(plan,listOf(changed),catalog,listOf(BackupManga(10,"/a")),listOf(BackupManga(20,"/b"))) }
    }
    test("Archive identity changed after planning rejected") { fails { assemble(replace={ it.copy(works=it.works.map { w -> w.copy(archiveWorkKey="other") }) }) } }
    test("Missing persisted source child ID rejected") { fails { assemble(pool=catalog.filterNot { it.localMangaId==102L }) } }
    test("No virtual works means no export payload") {
        val result = assemble(works=emptyList(),normal=emptyList(),extra=emptyList())
        check(result.works.isEmpty() && result.supplementalManga.isEmpty())
    }
    test("Pending child status changing after planning aborts the backup") {
        val planned = MergedBackupExportPlanner.plan(listOf(work),catalog,setOf(900,101),true)
        val live = work.copy(links=listOf(work.links[0],work.links[1].copy(localMangaId=null)))
        fails { BackupPolarisBundleBuilder.build(planned,listOf(live),catalog,listOf(BackupManga(10,"/a")),listOf(BackupManga(20,"/b"))) }
    }
    test("New child row appearing after planning requires a fresh snapshot") {
        val orphan=work.copy(links=listOf(work.links[0],work.links[1].copy(localMangaId=null)))
        val planned=MergedBackupExportPlanner.plan(listOf(orphan),catalog,setOf(900,101),true)
        fails { BackupPolarisBundleBuilder.build(planned,listOf(work),catalog,listOf(BackupManga(10,"/a")),emptyList()) }
    }
    test("Changing only parent ID or canonical UUID after planning aborts export") {
        val planned=MergedBackupExportPlanner.plan(listOf(work),catalog,setOf(900,101),true)
        for (changed in listOf(work.copy(parentLocalId=999), work.copy(canonicalUuid="different"))) {
            fails { BackupPolarisBundleBuilder.build(planned,listOf(changed),catalog,listOf(BackupManga(10,"/a")),listOf(BackupManga(20,"/b"))) }
        }
    }
    println("POLARIS_BACKUP_BUNDLE_BUILDER_PASS $count")
}
