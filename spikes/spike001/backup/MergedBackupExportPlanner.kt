package polaris.spike001.backup

/**
 * Host-only export selection for the future Yomotsu BackupCreator adapter.
 * The adapter MUST pass every selected child ID through MangaBackupCreator to
 * capture the real source manga's chapters/history/tracking according to the
 * same backup options; this planner does not serialize backup bytes.
 */
data class ExportMergedChildLink(
    val identity: SourceWorkIdentity,
    val localMangaId: Long?,
    val title: String,
    val settings: PortableMergeSettings,
)

data class ExportVirtualWork(
    val parentLocalId: Long,
    val parentSourceId: Long,
    val archiveWorkKey: String,
    val displayTitle: String,
    val links: List<ExportMergedChildLink>,
    val rootSettings: PortableMergeSettings,
    val canonicalUuid: String? = null,
)

data class MergedBackupExportPlan(
    val works: List<PortableMergedWork>,
    /** Real child manga IDs not already included in the normal Yomotsu backup. */
    val additionalRealChildMangaIds: List<Long>,
    /** Links kept without a local manga row. Never infer these from titles. */
    val pendingSourceWorks: Set<SourceWorkIdentity>,
)

object MergedBackupExportPlanner {
    private const val MERGED_SOURCE_ID = 6969L

    fun plan(
        virtualWorks: List<ExportVirtualWork>,
        persistedRealChildren: List<LocalSourceWork>,
        alreadySelectedMangaIds: Set<Long>,
        libraryEntriesEnabled: Boolean,
    ): MergedBackupExportPlan {
        if (!libraryEntriesEnabled) return MergedBackupExportPlan(emptyList(), emptyList(), emptySet())

        require(persistedRealChildren.all { it.localMangaId > 0 }) { "Real children must have positive local IDs" }
        require(persistedRealChildren.map { it.identity }.distinct().size == persistedRealChildren.size) {
            "Ambiguous persisted source ID+URL; refusing to export incomplete backup"
        }
        require(persistedRealChildren.map { it.localMangaId }.distinct().size == persistedRealChildren.size) {
            "One persisted manga ID maps to multiple source identities"
        }
        val byId = persistedRealChildren.associateBy { it.localMangaId }
        require(virtualWorks.map { it.parentLocalId }.distinct().size == virtualWorks.size) { "Duplicate virtual parent ID" }
        require(virtualWorks.map { it.archiveWorkKey }.distinct().size == virtualWorks.size) { "Duplicate portable work key" }
        val additional = linkedSetOf<Long>()
        val pending = linkedSetOf<SourceWorkIdentity>()
        val portable = virtualWorks.map { work ->
            require(work.parentSourceId == MERGED_SOURCE_ID && work.parentLocalId > 0) {
                "Export parent must be a persisted virtual manga"
            }
            require(work.archiveWorkKey.isNotBlank() && work.displayTitle.isNotBlank()) { "Missing portable identity/title" }
            require(work.links.isNotEmpty()) { "An exported virtual work requires at least one active link" }
            require(work.links.map { it.identity }.distinct().size == work.links.size) { "Duplicate child link" }
            require(work.links.count { it.settings.infoManga } <= 1) { "Multiple metadata source links" }
            require(!work.rootSettings.infoManga) { "Invalid root settings" }
            val children = work.links.map { link ->
                require(link.title.isNotBlank()) { "Missing source title" }
                val saved = link.localMangaId?.let { id ->
                    require(id > 0 && id != work.parentLocalId) { "Invalid source manga ID" }
                    requireNotNull(byId[id]) { "Linked real manga missing from local database snapshot" }
                }
                require(saved == null || saved.identity == link.identity) {
                    "Saved manga source ID+URL differs from association; refusing silent data loss"
                }
                // A dangling NULL reference is still portable even if there is a
                // separately saved local manga with that identity: don't invent
                // a new association on backup/export.
                if (saved == null) {
                    pending += link.identity
                } else if (saved.localMangaId !in alreadySelectedMangaIds) {
                    additional += saved.localMangaId
                }
                PortableMergedChild(link.identity, link.title, link.settings)
            }
            PortableMergedWork(
                archiveWorkKey = work.archiveWorkKey,
                displayTitle = work.displayTitle,
                children = children,
                rootSettings = work.rootSettings,
                canonicalUuid = work.canonicalUuid,
                exportedParentLocalId = work.parentLocalId,
            )
        }
        return MergedBackupExportPlan(portable, additional.toList(), pending)
    }
}
