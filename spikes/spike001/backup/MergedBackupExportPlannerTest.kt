package polaris.spike001.backup

private var cases = 0
private fun scenarioExport(name: String, action: () -> Unit) {
    action()
    cases += 1
    println("EXPORT_PASS ${cases.toString().padStart(2, '0')}: $name")
}
private fun failsExport(action: () -> Unit) = check(runCatching(action).isFailure)

fun main() {
    val a = SourceWorkIdentity(11, "/a")
    val b = SourceWorkIdentity(12, "/b")
    val c = SourceWorkIdentity(13, "/c")
    val settingsA = PortableMergeSettings(true, true, 2, 0, true)
    val settingsB = PortableMergeSettings(false, false, 2, 1, false)
    val root = PortableMergeSettings(false, false, 2, Int.MAX_VALUE.toLong(), false)
    val rows = listOf(LocalSourceWork(a, 100), LocalSourceWork(b, 200), LocalSourceWork(c, 300))
    val base = ExportVirtualWork(
        parentLocalId = 900, parentSourceId = 6969,
        archiveWorkKey = "uuid-work-one", displayTitle = "Work One",
        links = listOf(ExportMergedChildLink(a, 100, "A", settingsA), ExportMergedChildLink(b, 200, "B", settingsB)),
        rootSettings = root,
    )
    fun export(
        works: List<ExportVirtualWork> = listOf(base),
        catalog: List<LocalSourceWork> = rows,
        normal: Set<Long> = setOf(900),
        enabled: Boolean = true,
    ) = MergedBackupExportPlanner.plan(works, catalog, normal, enabled)

    scenarioExport("Unfavorited real children are included despite being absent from ordinary favorites") {
        check(export().additionalRealChildMangaIds == listOf(100L, 200L))
    }
    scenarioExport("Already exported favorite child is not backed up twice") {
        check(export(normal = setOf(900L, 100L)).additionalRealChildMangaIds == listOf(200L))
    }
    scenarioExport("Both children in ordinary backup need no additional snapshots") {
        check(export(normal = setOf(900L, 100L, 200L)).additionalRealChildMangaIds.isEmpty())
    }
    scenarioExport("Two virtual parents share one source snapshot without duplication") {
        val second = base.copy(parentLocalId = 901, archiveWorkKey = "uuid-work-two", links = listOf(base.links[1], ExportMergedChildLink(c,300,"C",settingsB)))
        check(export(works = listOf(base,second)).additionalRealChildMangaIds == listOf(100L,200L,300L))
    }
    scenarioExport("Export keeps exact original source URL and per-link flags") {
        val w = export().works.single()
        check(w.children[0].identity == a && w.children[1].identity == b)
        check(w.children.map { it.settings } == listOf(settingsA,settingsB))
        check(w.rootSettings == root)
    }
    scenarioExport("Export is usable by the existing portable restore planner on another device") {
        val item = export().works.single()
        val plan = MergedBackupRestorePlanner.plan(item, setOf(11,12), listOf(LocalSourceWork(a,1001)))
        check(plan.createCount == 1 && plan.children[0].localMangaId == 1001L)
        check(plan.bindCreatedChildren(listOf(LocalSourceWork(b,2002))).map { it.localMangaId } == listOf(1001L,2002L))
    }
    scenarioExport("An intentional unlink is never inferred from the local catalog") {
        val one = base.copy(links = listOf(base.links[0]))
        val plan = export(works = listOf(one))
        check(plan.works.single().children.single().identity == a)
        check(plan.additionalRealChildMangaIds == listOf(100L))
    }
    scenarioExport("Orphaned child reference keeps stable source ID+URL with no fabricated manga ID") {
        val orphan = base.copy(links = listOf(base.links[0], base.links[1].copy(localMangaId = null)))
        val plan = export(works = listOf(orphan))
        check(plan.additionalRealChildMangaIds == listOf(100L))
        check(plan.pendingSourceWorks == setOf(b))
        check(plan.works.single().children[1].identity == b)
    }
    scenarioExport("Disabled library-entry option produces no multifonte export") {
        check(export(enabled=false) == MergedBackupExportPlan(emptyList(),emptyList(),emptySet()))
    }
    scenarioExport("Broken saved child ID fails closed rather than silently omitting read state") {
        val wrong = base.copy(links = listOf(base.links[0].copy(localMangaId=777),base.links[1]))
        failsExport { export(works=listOf(wrong)) }
    }
    scenarioExport("Child manga URL mismatch fails closed") {
        val wrong = base.copy(links = listOf(base.links[0].copy(identity=c),base.links[1]))
        failsExport { export(works=listOf(wrong)) }
    }
    scenarioExport("Duplicate local source+URL among manga rows fails closed") {
        failsExport { export(catalog=rows+LocalSourceWork(a,400)) }
    }
    scenarioExport("Duplicate local ID assigned to different sources fails closed") {
        failsExport { export(catalog=rows+LocalSourceWork(SourceWorkIdentity(77,"/d"),100)) }
    }
    scenarioExport("Nonvirtual parent cannot be exported as a virtual work") {
        failsExport { export(works=listOf(base.copy(parentSourceId=11))) }
    }
    scenarioExport("Duplicate virtual work identifiers are rejected") {
        failsExport { export(works=listOf(base,base.copy(parentLocalId=901))) }
    }
    scenarioExport("Duplicate child references are rejected") {
        failsExport { export(works=listOf(base.copy(links=base.links+base.links[0]))) }
    }
    scenarioExport("Invalid metadata root or two metadata sources are rejected") {
        failsExport { export(works=listOf(base.copy(rootSettings=settingsA))) }
        failsExport { export(works=listOf(base.copy(links=listOf(base.links[0],base.links[1].copy(settings=settingsA))))) }
    }
    scenarioExport("Foreign signed-negative source IDs remain valid") {
        val negative=SourceWorkIdentity(-77,"/foreign")
        val work=base.copy(links=listOf(ExportMergedChildLink(negative,400,"Foreign",settingsA)))
        check(export(works=listOf(work),catalog=rows+LocalSourceWork(negative,400)).additionalRealChildMangaIds==listOf(400L))
    }
    scenarioExport("A source record may not point to its own virtual parent") {
        val wrong=base.copy(links=listOf(base.links[0].copy(localMangaId=900)))
        failsExport { export(works=listOf(wrong)) }
    }
    scenarioExport("A pending reference is exported even when no matching child row exists") {
        val orphan=base.copy(links=listOf(base.links[0],base.links[1].copy(localMangaId=null)))
        val plan=export(works=listOf(orphan),catalog=listOf(rows[0]))
        check(plan.pendingSourceWorks==setOf(b) && plan.additionalRealChildMangaIds==listOf(100L))
    }
    println("MERGED_BACKUP_EXPORT_PLANNER_PASS $cases")
}
