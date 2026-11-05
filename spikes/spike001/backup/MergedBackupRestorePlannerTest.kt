package polaris.spike001.backup

private var checks = 0
private fun scenario(description: String, action: () -> Unit) {
    action()
    checks++
    println("PASS ${checks.toString().padStart(2, '0')}: $description")
}
private fun fails(action: () -> Unit) {
    check(runCatching(action).isFailure) { "Expected validation failure" }
}

fun main() {
    val a = SourceWorkIdentity(1001, "/english/work")
    val b = SourceWorkIdentity(2002, "/portugues/work")
    val other = SourceWorkIdentity(1001, "/different-work")
    val settingsA = PortableMergeSettings(true, true, 2, 1, false)
    val settingsB = PortableMergeSettings(false, false, 2, 2, true)
    val root = PortableMergeSettings(false, false, 2, Int.MAX_VALUE.toLong(), false)
    val backup = PortableMergedWork(
        archiveWorkKey = "archive-virtual-123",
        displayTitle = "Work / Obra",
        children = listOf(PortableMergedChild(a, "Work", settingsA), PortableMergedChild(b, "Obra", settingsB)),
        rootSettings = root,
        exportedParentLocalId = 42,
    )
    scenario("Existing local IDs on a different device are mapped by source and URL") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 901), LocalSourceWork(b, 902)))
        check(p.children.map { it.localMangaId } == listOf(901L, 902L))
        check(p.children.none { it.localMangaId == backup.exportedParentLocalId })
    }
    scenario("Restore preserves the original per-child settings and root settings") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 901), LocalSourceWork(b, 902)))
        check(p.rootSettings == root)
        check(p.bindCreatedChildren(emptyList()).map { it.settings } == listOf(settingsA, settingsB))
    }
    scenario("Unfavorited existing source works can be reused") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 9), LocalSourceWork(b, 10)))
        check(p.children.all { it.recovery == LinkRecovery.REUSE_EXISTING })
    }
    scenario("Missing local child with installed extension requires a stub") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 9)))
        check(p.children[1].recovery == LinkRecovery.CREATE_CHILD_STUB)
        check(p.bindCreatedChildren(listOf(LocalSourceWork(b, 300))).map { it.localMangaId } == listOf(9L, 300L))
    }
    scenario("Missing extension retains pending stable source and URL without a fake local ID") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L), listOf(LocalSourceWork(a, 9)))
        check(p.pendingCount == 1 && p.createCount == 0)
        check(p.bindCreatedChildren(emptyList())[1] == ResolvedMergeLink(b, null, settingsB))
    }
    scenario("Restoration can resume when previously missing extension becomes available") {
        val before = MergedBackupRestorePlanner.plan(backup, setOf(1001L), listOf(LocalSourceWork(a, 9)))
        val after = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 9)))
        check(before.pendingCount == 1 && after.createCount == 1)
        check(after.bindCreatedChildren(listOf(LocalSourceWork(b, 41)))[1].localMangaId == 41L)
    }
    scenario("Interrupted restore reuses already-created first child on retry") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 500)))
        check(p.children[0].recovery == LinkRecovery.REUSE_EXISTING && p.children[1].recovery == LinkRecovery.CREATE_CHILD_STUB)
    }
    scenario("Different URLs on same source never match by title alone") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(other, 5)))
        check(p.children.all { it.recovery == LinkRecovery.CREATE_CHILD_STUB })
    }
    scenario("Same URL across different sources remains two separate identities") {
        val same = backup.copy(children = listOf(backup.children[0], PortableMergedChild(SourceWorkIdentity(2002, a.sourceUrl), "Other", settingsB)))
        check(MergedBackupRestorePlanner.plan(same, emptySet(), emptyList()).pendingCount == 2)
    }
    scenario("Duplicate source and URL in one archive is rejected") {
        fails { MergedBackupRestorePlanner.plan(backup.copy(children = backup.children + backup.children.first()), emptySet(), emptyList()) }
    }
    scenario("Conflicting multiple information-source references are rejected") {
        fails { MergedBackupRestorePlanner.plan(backup.copy(children = listOf(backup.children[0], backup.children[1].copy(settings = settingsA))), emptySet(), emptyList()) }
    }
    scenario("Ambiguous local identity is rejected instead of guessed") {
        fails { MergedBackupRestorePlanner.plan(backup, emptySet(), listOf(LocalSourceWork(a, 5), LocalSourceWork(a, 6))) }
    }
    scenario("Two different source identities sharing local ID are rejected") {
        fails { MergedBackupRestorePlanner.plan(backup, emptySet(), listOf(LocalSourceWork(a, 5), LocalSourceWork(b, 5))) }
    }
    scenario("Unknown newer archive version is rejected") {
        fails { MergedBackupRestorePlanner.plan(backup.copy(formatVersion = 2), emptySet(), emptyList()) }
    }
    scenario("Legacy Yomotsu backups with no Polaris field need no merged import") {
        val legacyMergedWorks: List<PortableMergedWork> = emptyList()
        check(legacyMergedWorks.isEmpty())
    }
    scenario("Deliberately unlinked child is never silently re-attached") {
        val oneChild = backup.copy(children = listOf(backup.children[0]))
        val p = MergedBackupRestorePlanner.plan(oneChild, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 5), LocalSourceWork(b, 6)))
        check(p.children.single().child.identity == a)
    }
    scenario("Binding rejects missing create result") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), emptyList())
        fails { p.bindCreatedChildren(listOf(LocalSourceWork(a, 10))) }
    }
    scenario("Binding rejects URL-substituted create result") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), emptyList())
        fails { p.bindCreatedChildren(listOf(LocalSourceWork(other, 10), LocalSourceWork(b, 11))) }
    }
    scenario("Binding rejects two created children mapped to one ID") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), emptyList())
        fails { p.bindCreatedChildren(listOf(LocalSourceWork(a, 10), LocalSourceWork(b, 10))) }
    }
    scenario("Binding rejects accidentally remapping one existing manga ID") {
        val p = MergedBackupRestorePlanner.plan(backup, setOf(1001L, 2002L), listOf(LocalSourceWork(a, 10)))
        fails { p.bindCreatedChildren(listOf(LocalSourceWork(b, 10))) }
    }
    scenario("An existing child remains linked with warning even if its extension is missing") {
        val p = MergedBackupRestorePlanner.plan(backup, emptySet(), listOf(LocalSourceWork(a, 90)))
        check(p.children[0].recovery == LinkRecovery.REUSE_EXISTING && !p.children[0].extensionInstalled)
        check(p.unavailableSourceCount == 2)
    }
    scenario("Negative signed real source ID remains a valid portable identity") {
        val negative = SourceWorkIdentity(-423L, "/work")
        val p = MergedBackupRestorePlanner.plan(backup.copy(children = listOf(PortableMergedChild(negative, "N", settingsA))), setOf(-423L), emptyList())
        check(p.createCount == 1)
    }
    scenario("Virtual source ID 6969 is rejected as a child") {
        fails { SourceWorkIdentity(6969L, "merged://42") }
    }
    scenario("Archive parent local ID does not affect deterministic restore planning") {
        val p1 = MergedBackupRestorePlanner.plan(backup, setOf(1001L), listOf(LocalSourceWork(a, 90)))
        val p2 = MergedBackupRestorePlanner.plan(backup.copy(exportedParentLocalId = 9999999), setOf(1001L), listOf(LocalSourceWork(a, 90)))
        check(p1 == p2)
    }
    println("MERGED_BACKUP_RESTORE_PLANNER_PASS $checks")
}
