package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle
import polaris.spike001.backup.restore.RestoredPolarisWork

/** The order values in BackupManga.categories refer to BackupCategory.order, NOT origin DB IDs. */
data class PolarisArchivedCategory(val order: Long, val name: String)

/**
 * A SINGLE transaction must enclose root creation/reuse, full metadata, notes,
 * memo, categories, chapters, history, tracking, excluded scanlators, source
 * edges, and the UUID restore ledger. Do not implement these with a chain of
 * independent Database.transaction calls or stock MangaRestorer.restore().
 * This is a staging interface, not a SQLDelight implementation.
 */
interface PolarisFullParentAtomicTransactionPort {
    suspend fun <T> transaction(block: suspend PolarisFullParentTransaction.() -> T): T
}

/** All methods are evaluated using the same write-locked, rollback-capable DB transaction. */
interface PolarisFullParentTransaction {
    /** Must report every ledger OR pre-ledger virtual manga claiming UUID, including collisions. */
    suspend fun findAllParentsClaimingUuid(uuid: String): List<PolarisParentMetadataRestorePlanner.ExistingParentRow>

    /** Resolve the destination category by exact archived NAME. Must return every matching local ID. */
    suspend fun localCategoryIdsByName(name: String): List<Long>

    /** Return every local manga ID matching the exact source and URL. */
    suspend fun exactRealChildIds(source: Long, url: String): List<Long>

    /** Reject an unledgered parent URL/memo collision. Must query physical DB, not an in-memory cache. */
    suspend fun requireNoUntrackedParentIdentity(uuid: String, destinationUrl: String)

    /** Creates parent, UUID ledger, links and ALL original parent metadata in this transaction. */
    suspend fun createAndApplyFullParent(
        command: PolarisParentMetadataRestorePlanner.ParentRestoreCommand,
        associations: RestoredPolarisWork,
    ): Long

    /** Recheck EMPTY in the transaction, then apply ALL metadata + links to the same ID. */
    suspend fun applyToVerifiedEmptyParent(
        parentId: Long,
        command: PolarisParentMetadataRestorePlanner.ParentRestoreCommand,
        associations: RestoredPolarisWork,
    )

    /**
     * Mandatory physical readback, ALSO for replay. Must compare every persisted
     * full BackupManga field plus categories, chapters, history, tracking, memo,
     * scanlator exclusions, source edges/flags and UUID-ledger identity.
     * Reject skipped/missing rows, user edits, or unverifiable fields.
     */
    suspend fun assertExactFullParentState(
        parentId: Long,
        command: PolarisParentMetadataRestorePlanner.ParentRestoreCommand,
        associations: RestoredPolarisWork,
    )
}

/** Staging result; returned ONLY if the surrounding transaction committed. */
data class PolarisFullParentRestoreResult(val parentIdsByUuid: Map<String, Long>)

/**
 * Validates archive/restore topology without writes, then validates identities,
 * category name mapping and parent UUIDs again inside ONE transaction BEFORE
 * calling any write operation. Physical validation is mandatory after each
 * parent and on unchanged replays. The Android v2 preflight remains blocked.
 */
class PolarisFullParentTransactionCoordinator(
    private val port: PolarisFullParentAtomicTransactionPort,
) {
    suspend fun restore(
        bundle: BackupPolarisBundle,
        ordinaryManga: List<BackupManga>,
        resolvedWorks: List<RestoredPolarisWork>,
        archiveCategories: List<PolarisArchivedCategory>,
    ): PolarisFullParentRestoreResult {
        bundle.validateSnapshotCoverage(ordinaryManga)
        require(bundle.formatVersion == BackupPolarisBundle.FULL_PARENT_FORMAT_VERSION) {
            "This coordinator requires full-parent v2; v1 belongs to the existing coordinator"
        }
        require(bundle.works.isNotEmpty() && bundle.works.size == bundle.parentSnapshots.size)
        require(resolvedWorks.size == bundle.works.size)
        require(archiveCategories.map { it.order }.distinct().size == archiveCategories.size) {
            "Duplicate archived category order"
        }
        require(archiveCategories.map { it.name }.distinct().size == archiveCategories.size &&
            archiveCategories.all { it.name.isNotBlank() }) { "Ambiguous archived category name" }
        val categoriesByOrder = archiveCategories.associate { it.order to it.name }
        val portableByUuid = bundle.works.associateBy { it.archiveWorkKey }
        require(portableByUuid.size == bundle.works.size) { "Duplicate archive works" }
        val resolvedByUuid = resolvedWorks.associateBy { it.archiveUuid }
        require(resolvedByUuid.size == resolvedWorks.size && resolvedByUuid.keys == portableByUuid.keys) {
            "Resolved and portable UUID sets differ"
        }
        val globalRealIds = mutableMapOf<Long, Pair<Long, String>>()
        for (work in resolvedWorks) {
            val portable = portableByUuid.getValue(work.archiveUuid)
            require(portable.displayTitle == work.title && portable.rootSettings == work.rootSettings &&
                portable.links.size == work.children.size) { "Parent flags/title/links changed during child restore" }
            val seenSources = mutableSetOf<Pair<Long, String>>()
            portable.links.zip(work.children).forEach { (link, resolved) ->
                val identity = link.sourceId to link.sourceUrl
                require(identity.first != 6969L && identity.second.isNotBlank() && seenSources.add(identity)) {
                    "Invalid or repeated child source identity"
                }
                require(resolved.sourceId == link.sourceId && resolved.sourceUrl == link.sourceUrl &&
                    resolved.settings == link.settings && resolved.wasPending == link.isPending &&
                    (resolved.realMangaId == null) == link.isPending) {
                    "Resolved child identity, settings or pending state drifted"
                }
                val id = resolved.realMangaId
                if (id != null) {
                    require(id > 0) { "Invalid real manga ID" }
                    val previous = globalRealIds.putIfAbsent(id, identity)
                    require(previous == null || previous == identity) {
                        "One local real manga ID was assigned to distinct source identities"
                    }
                }
            }
        }
        val referencedOrders = bundle.parentSnapshots.flatMap { it.manga.categories }.distinct()
        require(referencedOrders.all { it in categoriesByOrder }) { "Missing archived category order/name" }

        // The actual SQLDelight driver must support transaction + rollback here.
        return port.transaction {
            val mappings = linkedMapOf<Long, Long>()
            for (order in referencedOrders) {
                val ids = localCategoryIdsByName(categoriesByOrder.getValue(order))
                check(ids.size == 1 && ids.single() > 0L) { "Missing or ambiguous destination category name" }
                mappings[order] = ids.single()
            }
            check(mappings.values.distinct().size == mappings.size) {
                "Different archived categories collapsed onto one destination category"
            }
            for (work in resolvedWorks) {
                for (link in work.children) {
                    val id = link.realMangaId ?: continue // explicit pending stays NULL
                    check(exactRealChildIds(link.sourceId, link.sourceUrl) == listOf(id)) {
                        "Real child was changed or duplicated before the atomic parent write"
                    }
                }
            }
            val uuids = bundle.parentSnapshots.map { it.archiveUuid }
            val parents = uuids.associateWith { uuid -> findAllParentsClaimingUuid(uuid) }
            val plan = PolarisParentMetadataRestorePlanner.prepare(bundle, ordinaryManga, parents, mappings)
            val result = linkedMapOf<String, Long>()
            val seenIds = mutableSetOf<Long>()
            for (command in plan) {
                val work = resolvedByUuid.getValue(command.canonicalUuid)
                val parentId = when (command.operation) {
                    PolarisParentMetadataRestorePlanner.Operation.CREATE_AND_APPLY -> {
                        requireNoUntrackedParentIdentity(command.canonicalUuid, command.destinationUrl)
                        createAndApplyFullParent(command, work)
                    }
                    PolarisParentMetadataRestorePlanner.Operation.APPLY_TO_EMPTY -> {
                        val id = checkNotNull(command.existingParentId)
                        applyToVerifiedEmptyParent(id, command, work)
                        id
                    }
                    PolarisParentMetadataRestorePlanner.Operation.ALREADY_IDENTICAL ->
                        checkNotNull(command.existingParentId)
                }
                check(parentId > 0L && seenIds.add(parentId)) { "Parent insert/reuse returned invalid/duplicate manga ID" }
                // This is NOT optional: prevents a port from silently omitting metadata.
                assertExactFullParentState(parentId, command, work)
                result[command.canonicalUuid] = parentId
            }
            PolarisFullParentRestoreResult(result)
        }
    }
}