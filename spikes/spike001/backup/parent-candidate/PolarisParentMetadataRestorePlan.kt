package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle

/**
 * Staging-only v2 parent metadata preflight. No SQLite/Android writes and NOT
 * an authorization to remove PolarisRestoreCoordinator's v2 import block.
 *
 * The Android adapter must take an authoritative UUID-indexed snapshot inside
 * its restoration transaction, verify every disposition there again, and
 * atomically apply the FULL BackupManga to the single UUID-resolved parent.
 * Never resolve parents by title, source URL alone, or local backup manga_id.
 */
object PolarisParentMetadataRestorePlanner {
    private const val VIRTUAL_SOURCE = 6969L

    enum class MetadataDisposition {
        /** Created by this restore, with no preexisting user data. */
        EMPTY_PLACEHOLDER,
        /** Full backed-up state was already applied; replay must not change it. */
        IDENTICAL_TO_ARCHIVE,
        /** Local edits, incomplete comparison, or an unknown current state. */
        CONFLICT_OR_UNVERIFIED,
    }

    data class ExistingParentRow(
        val mangaId: Long,
        val canonicalUuid: String,
        val sourceId: Long,
        val sourceUrl: String,
        val metadataDisposition: MetadataDisposition,
    )

    enum class Operation { CREATE_AND_APPLY, APPLY_TO_EMPTY, ALREADY_IDENTICAL }

    /** A complete archive object, NEVER a lossy projection of title/UUID. */
    data class ParentRestoreCommand(
        val canonicalUuid: String,
        val originalOrdinal: Int,
        val fullBackupManga: BackupManga,
        val mappedCategoryIds: List<Long>,
        val operation: Operation,
        val existingParentId: Long?,
    )

    /**
     * existingByUuid must come from an authoritative UUID ledger; each lookup
     * must return ALL exact matches, including collisions. Missing = new parent.
     * categoryIdMap comes from restoring the archive's category definitions by
     * name, NOT from copying foreign numeric category IDs to this device.
     */
    fun prepare(
        bundle: BackupPolarisBundle,
        ordinaryManga: List<BackupManga>,
        existingByUuid: Map<String, List<ExistingParentRow>>,
        categoryIdMap: Map<Long, Long>,
    ): List<ParentRestoreCommand> {
        bundle.validateSnapshotCoverage(ordinaryManga)
        require(bundle.formatVersion == BackupPolarisBundle.FULL_PARENT_FORMAT_VERSION) {
            "Full-parent metadata planner only accepts a complete v2 archive"
        }
        require(bundle.parentSnapshots.size == bundle.works.size && bundle.works.isNotEmpty())
        val works = bundle.works.associateBy { it.archiveWorkKey }
        val seenExistingIds = mutableSetOf<Long>()
        return bundle.parentSnapshots.map { payload ->
            val uuid = payload.archiveUuid
            val work = requireNotNull(works[uuid]) { "Missing canonical work for parent payload" }
            val snapshot = payload.manga
            require(snapshot.source == VIRTUAL_SOURCE && snapshot.url.isNotBlank() && snapshot.title == work.displayTitle) {
                "Invalid or changed complete virtual parent snapshot"
            }
            val mappedCategories = snapshot.categories.map { archiveId ->
                val localId = requireNotNull(categoryIdMap[archiveId]) {
                    "Unmapped backup category $archiveId for parent $uuid"
                }
                require(localId > 0L) { "Invalid destination category ID" }
                localId
            }
            require(mappedCategories.distinct().size == mappedCategories.size) {
                "Category mapping collapsed distinct parent categories"
            }
            val matches = existingByUuid[uuid].orEmpty()
            check(matches.size <= 1) { "Multiple destination parent rows share one canonical UUID" }
            val existing = matches.singleOrNull()
            if (existing != null) {
                check(existing.mangaId > 0L && existing.canonicalUuid == uuid &&
                    existing.sourceId == VIRTUAL_SOURCE && existing.sourceUrl == snapshot.url) {
                    "Existing UUID belongs to a different/invalid parent identity"
                }
                check(seenExistingIds.add(existing.mangaId)) {
                    "Multiple parent UUIDs resolve to the same destination manga ID"
                }
            }
            val operation = when (existing?.metadataDisposition) {
                null -> Operation.CREATE_AND_APPLY
                MetadataDisposition.EMPTY_PLACEHOLDER -> Operation.APPLY_TO_EMPTY
                MetadataDisposition.IDENTICAL_TO_ARCHIVE -> Operation.ALREADY_IDENTICAL
                MetadataDisposition.CONFLICT_OR_UNVERIFIED -> error(
                    "Destination parent has local changes or unverifiable metadata; refusing to overwrite"
                )
            }
            ParentRestoreCommand(
                canonicalUuid = uuid,
                originalOrdinal = payload.originalOrdinal,
                fullBackupManga = snapshot,
                mappedCategoryIds = mappedCategories,
                operation = operation,
                existingParentId = existing?.mangaId,
            )
        }
    }
}