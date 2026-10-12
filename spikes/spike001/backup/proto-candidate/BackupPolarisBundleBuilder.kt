package polaris.spike001.backup

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisLink
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisMergeSettings
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisWork

/**
 * Data-safe glue between MergedBackupExportPlanner and the optional protobuf DTO.
 * The caller must serialize additionalRealChildMangaIds via the REAL
 * MangaBackupCreator using identical BackupOptions before invoking this.
 * No Android/database writes happen here.
 */
object BackupPolarisBundleBuilder {
    fun build(
        plan: MergedBackupExportPlan,
        liveVirtualWorks: List<ExportVirtualWork>,
        localRealManga: List<LocalSourceWork>,
        ordinaryManga: List<BackupManga>,
        supplementalManga: List<BackupManga>,
    ): BackupPolarisBundle {
        require(liveVirtualWorks.map { it.archiveWorkKey }.distinct().size == liveVirtualWorks.size) {
            "Duplicated live work keys"
        }
        require(plan.works.map { it.archiveWorkKey }.toSet() == liveVirtualWorks.map { it.archiveWorkKey }.toSet()) {
            "Export plan/live work mismatch"
        }
        val liveByKey = liveVirtualWorks.associateBy { it.archiveWorkKey }
        require(localRealManga.map { it.identity }.distinct().size == localRealManga.size) {
            "Ambiguous local real manga source identity"
        }
        require(localRealManga.map { it.localMangaId }.distinct().size == localRealManga.size) {
            "Ambiguous local real manga IDs"
        }
        val catalog = localRealManga.associateBy { it.localMangaId }
        val expectedSupplemental = plan.additionalRealChildMangaIds.map { localId ->
            requireNotNull(catalog[localId]) { "Missing source child requested by export planner" }.identity.let {
                it.sourceId to it.sourceUrl
            }
        }
        val actualSupplemental = supplementalManga.map { it.source to it.url }
        require(expectedSupplemental.size == expectedSupplemental.toSet().size) {
            "Repeated child snapshot request"
        }
        require(actualSupplemental.size == actualSupplemental.toSet().size &&
            actualSupplemental.toSet() == expectedSupplemental.toSet()) {
            "MangaBackupCreator returned missing, duplicated or unrelated supplementary source data"
        }
        val works = plan.works.map { portable ->
            val live = liveByKey.getValue(portable.archiveWorkKey)
            require(portable.children.size == live.links.size) { "Changed linked child list during export" }
            val links = portable.children.zip(live.links).map { (archived, link) ->
                require(archived.identity == link.identity && archived.title == link.title && archived.settings == link.settings) {
                    "Source link changed while backup was in progress"
                }
                BackupPolarisLink(
                    sourceId = archived.identity.sourceId,
                    sourceUrl = archived.identity.sourceUrl,
                    observedTitle = archived.title,
                    settings = archived.settings.asProto(),
                    isPending = link.localMangaId == null,
                )
            }
            BackupPolarisWork(
                archiveWorkKey = portable.archiveWorkKey,
                displayTitle = portable.displayTitle,
                rootSettings = portable.rootSettings.asProto(),
                links = links,
                canonicalUuid = portable.canonicalUuid,
            )
        }
        return BackupPolarisBundle(works = works, supplementalManga = supplementalManga).also {
            it.validateSnapshotCoverage(ordinaryManga)
        }
    }

    private fun PortableMergeSettings.asProto() = BackupPolarisMergeSettings(
        infoManga, getChapterUpdates, chapterSortMode, chapterPriority, downloadChapters,
    )
}
