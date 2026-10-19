package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisLink
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisMergeSettings
import java.util.UUID

/** One child association for an atomic virtual-parent restore transaction. */
data class RestoredPolarisLink(
    val sourceId: Long,
    val sourceUrl: String,
    val realMangaId: Long?,
    val wasPending: Boolean,
    val settings: BackupPolarisMergeSettings,
)

data class RestoredPolarisWork(
    val archiveUuid: String,
    val title: String,
    val rootSettings: BackupPolarisMergeSettings,
    val children: List<RestoredPolarisLink>,
)

/**
 * The REAL Android implementation must restore a complete BackupManga
 * (chapters, read progress, history, tracking as selected). Failures MUST throw.
 * Lookup must return every exact source+URL match, not only one arbitrary row.
 */
interface PolarisSourceRestorePort {
    suspend fun restoreSupplementalMangaOrThrow(snapshot: BackupManga)
    suspend fun findMangaIdsBySourceAndUrl(sourceId: Long, sourceUrl: String): List<Long>
}

/**
 * The REAL Android implementation must commit ALL parent UUID reuse/create,
 * root and child-reference changes in ONE SQLDelight transaction, with a
 * database-backed uniqueness/restore ledger, no title-based guessing.
 * An incomplete commit MUST throw. There is no production implementation yet.
 */
interface PolarisAtomicVirtualWorkPort {
    suspend fun commitAllOrThrow(works: List<RestoredPolarisWork>)
}

/**
 * Fail-closed, child-first protocol for the optional Polaris backup segment.
 * Host tested against fake ports; NOT a wired Yomotsu/Android restore.
 */
class PolarisRestoreCoordinator(
    private val children: PolarisSourceRestorePort,
    private val parents: PolarisAtomicVirtualWorkPort,
) {
    /** Call this immediately after decoding, before ANY normal restore jobs. */
    fun preflight(bundle: BackupPolarisBundle?, ordinary: List<BackupManga>, libraryEntries: Boolean) {
        if (!libraryEntries || bundle == null) return
        bundle.validateSnapshotCoverage(ordinary)
        // v2 includes complete parent BackupManga data. Until a transactional
        // metadata applier is wired to the UUID-resolved parent ID, importing
        // it here would silently discard categories, notes and user progress.
        // Fail BEFORE stock MangaRestorer writes any child/parent records.
        require(bundle.parentSnapshots.isEmpty()) {
            "Full-parent v2 restore requires atomic metadata applier; blocked before database writes"
        }
        for (work in bundle.works) {
            val uuid = work.canonicalUuid
            require(uuid != null && uuid == work.archiveWorkKey && isCanonicalUuid(uuid)) {
                "Archive work key must equal the durable canonical parent UUID"
            }
        }
    }

    /**
     * Await a *verified*, complete ordinary MangaRestorer, then restore
     * supplemental real mangas, validate real IDs, and only then commit parents.
     * The await function MUST throw if any ordinary manga restore failed:
     * Yomotsu's stock restoreManga() catches some errors and cannot be used
     * without an adapter that collects and propagates them.
     */
    suspend fun restore(
        bundle: BackupPolarisBundle?,
        ordinary: List<BackupManga>,
        libraryEntries: Boolean,
        awaitVerifiedOrdinaryRestore: suspend () -> Unit,
    ): List<RestoredPolarisWork> {
        if (!libraryEntries || bundle == null) return emptyList()
        preflight(bundle, ordinary, true)
        // Barrier: this must not silently swallow an ordinary backup failure.
        awaitVerifiedOrdinaryRestore()
        for (snapshot in bundle.supplementalManga) {
            children.restoreSupplementalMangaOrThrow(snapshot)
        }
        val realKeys = bundle.works.flatMap { it.links }.filterNot { it.isPending }
            .map { it.sourceId to it.sourceUrl }.distinct()
        val resolved = linkedMapOf<Pair<Long, String>, Long>()
        for ((sourceId, sourceUrl) in realKeys) {
            val ids = children.findMangaIdsBySourceAndUrl(sourceId, sourceUrl)
            check(ids.size == 1 && ids.single() > 0L) {
                "Resolved child is absent or ambiguous after restoring source-specific snapshots"
            }
            resolved[sourceId to sourceUrl] = ids.single()
        }
        // A corrupt local database must not map two different source identities
        // onto the same real manga row, even if per-key lookup returns one ID.
        check(resolved.values.distinct().size == resolved.size) {
            "A local manga ID maps to different source identities"
        }
        val workPlans = bundle.works.map { work ->
            RestoredPolarisWork(
                archiveUuid = work.archiveWorkKey,
                title = work.displayTitle,
                rootSettings = work.rootSettings,
                children = work.links.map { link: BackupPolarisLink ->
                    RestoredPolarisLink(
                        sourceId = link.sourceId,
                        sourceUrl = link.sourceUrl,
                        realMangaId = if (link.isPending) null else resolved.getValue(link.sourceId to link.sourceUrl),
                        wasPending = link.isPending,
                        settings = link.settings,
                    )
                },
            )
        }
        if (workPlans.isNotEmpty()) {
            parents.commitAllOrThrow(workPlans)
        }
        return workPlans
    }

    private fun isCanonicalUuid(value: String): Boolean =
        runCatching { UUID.fromString(value).toString() == value }.getOrDefault(false)
}
