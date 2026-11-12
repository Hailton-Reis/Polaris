package polaris.spike001.backup.yomotsu

import eu.kanade.tachiyomi.data.backup.create.BackupOptions
import eu.kanade.tachiyomi.data.backup.create.creators.MangaBackupCreator
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle
import polaris.spike001.backup.BackupPolarisBundleBuilder
import polaris.spike001.backup.ExportMergedChildLink
import polaris.spike001.backup.ExportVirtualWork
import polaris.spike001.backup.LocalSourceWork
import polaris.spike001.backup.MergedBackupExportPlanner
import polaris.spike001.backup.PortableMergeSettings
import polaris.spike001.backup.SourceWorkIdentity
import polaris.spike001.backup.uuid.YomotsuMergedWorkUuidStore
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository
import tachiyomi.domain.manga.repository.MangaRepository

/**
 * Candidate exporter using exact pinned Yomotsu repository and MangaBackupCreator APIs.
 * Must not be installed into production until Android/SQLDelight/real Protobuf gates pass.
 * Does not create an archive: returns only the optional full-data Polaris bundle.
 */
class PolarisYomotsuBackupExporter(
    private val mangas: MangaRepository,
    private val merges: MangaMergeRepository,
    private val ids: YomotsuMergedWorkUuidStore,
    private val backupManga: MangaBackupCreator,
) {
    suspend fun collect(
        ordinary: List<Manga>,
        ordinarySnapshots: List<BackupManga>,
        options: BackupOptions,
    ): BackupPolarisBundle? {
        if (!options.libraryEntries) return null
        val parents = ordinary.filter { it.source == 6969L }
        if (parents.isEmpty()) return null
        require(parents.map { it.id }.distinct().size == parents.size) { "Duplicate merged parent in ordinary backup" }
        require(ordinary.map { it.id }.distinct().size == ordinary.size) { "Duplicate manga ID in ordinary backup" }
        val uuidByParent = ids.ensureDistinct(parents.map { it.id })
        val catalog = linkedMapOf<Long, LocalSourceWork>()

        suspend fun capture(): List<ExportVirtualWork> = parents.map { selected ->
            val current = mangas.getMangaById(selected.id)
            require(current.source == 6969L && current.url == selected.url && current.title == selected.title && current.favorite) {
                "Virtual parent changed during backup; retry"
            }
            require(ids.ensure(current.id) == uuidByParent.getValue(current.id)) {
                "Virtual identity changed during backup"
            }
            val refs = merges.getReferencesById(current.id)
            require(refs.all { it.mergeId == current.id && it.mergeUrl == current.url }) {
                "Merge references do not belong to the selected parent"
            }
            val roots = refs.filter { it.mangaSourceId == 6969L }
            require(roots.size == 1) { "Missing or repeated virtual root reference" }
            val root = roots.single()
            require(root.mangaId == current.id && root.mangaUrl == current.url && !root.isInfoManga) {
                "Virtual root points to the wrong manga"
            }
            val children = refs.filter { it.mangaSourceId != 6969L }.map { ref ->
                val child = ref.mangaId?.let { localId ->
                    require(localId > 0) { "Invalid real-source manga ID" }
                    mangas.getMangaById(localId).also {
                        require(it.source == ref.mangaSourceId && it.url == ref.mangaUrl && it.source != 6969L) {
                            "Merge link points to a different source identity"
                        }
                        val local = LocalSourceWork(SourceWorkIdentity(it.source, it.url), it.id)
                        require(catalog.putIfAbsent(it.id, local) == null || catalog[it.id] == local) {
                            "Conflicting source identity for the same manga ID"
                        }
                    }
                }
                ExportMergedChildLink(
                    identity = SourceWorkIdentity(ref.mangaSourceId, ref.mangaUrl),
                    localMangaId = child?.id,
                    title = child?.title ?: ref.mangaUrl, // pending links have no title in merged.sq
                    settings = ref.toSettings(),
                )
            }
            ExportVirtualWork(
                parentLocalId = current.id,
                parentSourceId = current.source,
                archiveWorkKey = uuidByParent.getValue(current.id),
                displayTitle = current.title,
                links = children,
                rootSettings = root.toSettings(),
                canonicalUuid = uuidByParent.getValue(current.id),
            )
        }

        val before = capture()
        val plan = MergedBackupExportPlanner.plan(before, catalog.values.toList(), ordinary.map { it.id }.toSet(), true)
        val supplements = backupManga(
            plan.additionalRealChildMangaIds.map { mangas.getMangaById(it) }, options,
        )
        // Re-read AFTER full chapter/history/tracking snapshot construction. No
        // parent/link change may be silently accepted between plan and encoding.
        val after = capture()
        return BackupPolarisBundleBuilder.build(plan, after, catalog.values.toList(), ordinarySnapshots, supplements)
    }

    private fun MergedMangaReference.toSettings() = PortableMergeSettings(
        infoManga = isInfoManga,
        getChapterUpdates = getChapterUpdates,
        chapterSortMode = chapterSortMode.toLong(),
        chapterPriority = chapterPriority.toLong(),
        downloadChapters = downloadChapters,
    )
}
