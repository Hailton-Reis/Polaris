package polaris.spike001.backup

/**
 * Standalone planning contract for a future Yomotsu Backup.kt protobuf adapter.
 * No database writes or calls to the Android source manager are performed here.
 * A parent local manga ID is intentionally NOT part of the portable identity.
 */
private const val MERGED_SOURCE_ID = 6969L

data class SourceWorkIdentity(val sourceId: Long, val sourceUrl: String) {
    init {
        require(sourceId != MERGED_SOURCE_ID) { "A linked child cannot be a synthetic merged source" }
        require(sourceUrl.isNotBlank()) { "Source URL/key may not be blank" }
    }
}

data class PortableMergeSettings(
    val infoManga: Boolean,
    val getChapterUpdates: Boolean,
    val chapterSortMode: Long,
    val chapterPriority: Long,
    val downloadChapters: Boolean,
)

data class PortableMergedChild(
    val identity: SourceWorkIdentity,
    val title: String,
    val settings: PortableMergeSettings,
)

data class PortableMergedWork(
    val formatVersion: Int = SUPPORTED_VERSION,
    val archiveWorkKey: String,
    val displayTitle: String,
    val children: List<PortableMergedChild>,
    val rootSettings: PortableMergeSettings,
    val canonicalUuid: String? = null,
    // Exported local ID is diagnostics ONLY. Never resolve a child or parent using it.
    val exportedParentLocalId: Long? = null,
) {
    companion object { const val SUPPORTED_VERSION = 1 }
}

data class LocalSourceWork(val identity: SourceWorkIdentity, val localMangaId: Long)

enum class LinkRecovery { REUSE_EXISTING, CREATE_CHILD_STUB, PENDING_EXTENSION }

data class PlannedChildLink(
    val child: PortableMergedChild,
    val recovery: LinkRecovery,
    val localMangaId: Long?,
    val extensionInstalled: Boolean,
)

data class MergeRestorePlan(
    val archiveWorkKey: String,
    val canonicalUuid: String?,
    val displayTitle: String,
    val rootSettings: PortableMergeSettings,
    val children: List<PlannedChildLink>,
) {
    val pendingCount: Int get() = children.count { it.recovery == LinkRecovery.PENDING_EXTENSION }
    val unavailableSourceCount: Int get() = children.count { !it.extensionInstalled }
    val createCount: Int get() = children.count { it.recovery == LinkRecovery.CREATE_CHILD_STUB }

    /**
     * Bind child IDs returned after creating source-specific stubs. Must be done
     * before writing resolved associations. Missing extensions retain NULL manga_id
     * with their exact sourceId+URL identity in the staged migration-14 table.
     */
    fun bindCreatedChildren(created: List<LocalSourceWork>): List<ResolvedMergeLink> {
        require(created.all { it.localMangaId > 0 }) { "Invalid newly created manga ID" }
        val byKey = created.groupBy { it.identity }
        require(byKey.values.all { it.size == 1 }) { "Duplicate newly created source identity" }
        val expected = children.filter { it.recovery == LinkRecovery.CREATE_CHILD_STUB }.map { it.child.identity }.toSet()
        require(byKey.keys == expected) { "Created children must match the exact planned source IDs and URLs" }
        val existingIds = children.mapNotNull { it.localMangaId }.toSet()
        require(created.none { it.localMangaId in existingIds }) { "Created ID collides with an existing child" }
        require(created.map { it.localMangaId }.distinct().size == created.size) { "Created children reuse one local ID" }
        return children.map { link ->
            val resolvedId = when (link.recovery) {
                LinkRecovery.REUSE_EXISTING -> link.localMangaId
                LinkRecovery.CREATE_CHILD_STUB -> byKey.getValue(link.child.identity).single().localMangaId
                LinkRecovery.PENDING_EXTENSION -> null
            }
            ResolvedMergeLink(link.child.identity, resolvedId, link.child.settings)
        }
    }
}

data class ResolvedMergeLink(
    val identity: SourceWorkIdentity,
    val localMangaId: Long?,
    val settings: PortableMergeSettings,
)

/**
 * Produces an import plan. The Android adapter must use a durable archiveWorkKey
 * (or canonicalUuid where implemented) to find/create the virtual parent, and
 * commit child/root associations transactionally with duplicate-safe upserts.
 */
object MergedBackupRestorePlanner {
    fun plan(
        archived: PortableMergedWork,
        installedRealSourceIds: Set<Long>,
        localSourceWorks: List<LocalSourceWork>,
    ): MergeRestorePlan {
        require(archived.formatVersion == PortableMergedWork.SUPPORTED_VERSION) {
            "Unsupported merged backup version ${archived.formatVersion}"
        }
        require(archived.archiveWorkKey.isNotBlank()) { "Missing archive work identity" }
        require(archived.displayTitle.isNotBlank()) { "Missing virtual title" }
        // One or more is valid: an intentional unlink may leave only one active variant.
        require(archived.children.isNotEmpty()) { "Merged work has no source references" }
        require(archived.children.all { it.title.isNotBlank() }) { "Missing source title" }
        val identities = archived.children.map { it.identity }
        require(identities.size == identities.distinct().size) { "Duplicate archived child identity" }
        require(archived.children.count { it.settings.infoManga } <= 1) { "Multiple info sources in one virtual work" }
        require(!archived.rootSettings.infoManga) { "Root reference cannot also be info manga" }

        val repeatedIds = localSourceWorks.groupBy { it.localMangaId }
        require(localSourceWorks.all { it.localMangaId > 0 }) { "Invalid existing local manga ID" }
        require(repeatedIds.values.all { it.size == 1 }) { "One local ID maps to multiple source works" }
        val localByKey = localSourceWorks.groupBy { it.identity }
        require(localByKey.values.all { it.size == 1 }) { "Ambiguous local source+URL match" }
        val restoredChildren = archived.children.map { child ->
            val local = localByKey[child.identity]?.singleOrNull()
            when {
                local != null -> PlannedChildLink(child, LinkRecovery.REUSE_EXISTING, local.localMangaId, child.identity.sourceId in installedRealSourceIds)
                child.identity.sourceId in installedRealSourceIds -> PlannedChildLink(child, LinkRecovery.CREATE_CHILD_STUB, null, true)
                else -> PlannedChildLink(child, LinkRecovery.PENDING_EXTENSION, null, false)
            }
        }
        return MergeRestorePlan(
            archiveWorkKey = archived.archiveWorkKey,
            canonicalUuid = archived.canonicalUuid,
            displayTitle = archived.displayTitle,
            rootSettings = archived.rootSettings,
            children = restoredChildren,
        )
    }
}
