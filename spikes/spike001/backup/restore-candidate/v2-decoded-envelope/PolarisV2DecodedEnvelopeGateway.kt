package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.BackupCategory
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle

/**
 * Staging decoder-owned admission. This API never accepts raw payload/digest
 * pairs; it creates the canonical envelope FROM the decoded, validated v2 DTO.
 * Must be invoked before any stock MangaRestorer or SQLDelight DB writes.
 */
object PolarisV2DecodedEnvelopeGateway {
    fun admitDecodedParent(
        bundle: BackupPolarisBundle,
        ordinaryManga: List<BackupManga>,
        originalArchiveCategories: List<BackupCategory>,
        archiveUuid: String,
        codec: PolarisV2EnvelopeCodec<PolarisV2ProtoBufEnvelope>,
    ): PolarisV2SnapshotAdmission<PolarisV2ProtoBufEnvelope> {
        require(bundle.formatVersion == 2) { "POLARIS_V2_NOT_FULL_PARENT" }
        bundle.validateSnapshotCoverage(ordinaryManga)
        val work = requireNotNull(bundle.works.singleOrNull { it.archiveWorkKey == archiveUuid }) {
            "POLARIS_V2_NO_UNIQUE_ARCHIVED_WORK"
        }
        val parent = requireNotNull(bundle.parentSnapshots.singleOrNull { it.archiveUuid == archiveUuid }) {
            "POLARIS_V2_NO_UNIQUE_PARENT_SNAPSHOT"
        }
        val usedOrders = parent.manga.categories
        check(usedOrders.distinct().size == usedOrders.size) { "POLARIS_V2_DUPLICATE_CATEGORY_ORDER" }
        val byOrder = originalArchiveCategories.groupBy { it.order }
        val categories = usedOrders.map { order ->
            val choices = byOrder[order].orEmpty()
            check(choices.size == 1) { "POLARIS_V2_MISSING_OR_AMBIGUOUS_ARCHIVE_CATEGORY" }
            choices.single()
        }
        val envelope = PolarisV2ProtoBufEnvelope(
            formatVersion = bundle.formatVersion,
            work = work,
            parent = parent,
            referencedCategories = categories,
        )
        envelope.validateDecoded()
        return PolarisV2SnapshotAdmission.fromDecoded(envelope, codec)
    }
}
