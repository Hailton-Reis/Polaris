package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.BackupCategory
import eu.kanade.tachiyomi.data.backup.models.BackupManga
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundle

/**
 * Staging-only. Converts ONE already decoded v2 backup to new-parent work and
 * ties each work to the SAME decoded graph with a re-verifiable admission.
 * Android must supply its real ProtoBuf codec, not a host stand-in.
 * Never enables the production v2 coordinator.
 */
object PolarisV2BoundFreshRestoreBridge {
    data class Destination(
        val archiveUuid: String,
        val categoriesByOrder: Map<Long, Long>,
        /** ONLY resolved children; pending links must NOT have local IDs. */
        val realChildrenByIdentity: Map<Pair<Long, String>, Long>,
        val technical: PolarisBackupMangaSqlProjection.TechnicalState =
            PolarisBackupMangaSqlProjection.TechnicalState(),
    )

    fun bindDecoded(
        bundle: BackupPolarisBundle,
        ordinary: List<BackupManga>,
        originalCategories: List<BackupCategory>,
        destinations: List<Destination>,
        codec: PolarisV2EnvelopeCodec<PolarisV2ProtoBufEnvelope>,
    ): List<SqlDelightPolarisFreshParentAdapter.FreshWork> {
        require(bundle.formatVersion == 2 && bundle.works.isNotEmpty()) { "POLARIS_BOUND_EXPECT_V2" }
        bundle.validateSnapshotCoverage(ordinary)
        val expectedUuids = bundle.works.map { it.archiveWorkKey }
        require(expectedUuids.distinct().size == expectedUuids.size &&
            destinations.map { it.archiveUuid }.distinct().size == destinations.size &&
            destinations.map { it.archiveUuid }.toSet() == expectedUuids.toSet()) {
            "POLARIS_BOUND_DESTINATION_COVERAGE"
        }
        val byUuid = destinations.associateBy { it.archiveUuid }
        return expectedUuids.map { uuid ->
            val destination = byUuid.getValue(uuid)
            val admission = PolarisV2DecodedEnvelopeGateway.admitDecodedParent(
                bundle, ordinary, originalCategories, uuid, codec,
            )
            admission.verifyBeforeTransaction()
            val envelope = admission.decoded
            val resolvedKeys = envelope.work.links.filterNot { it.isPending }
                .map { it.sourceId to it.sourceUrl }.toSet()
            require(destination.realChildrenByIdentity.keys == resolvedKeys &&
                destination.realChildrenByIdentity.values.all { it > 0L }) {
                "POLARIS_BOUND_RESOLVED_CHILD_COVERAGE"
            }
            val orderKeys = envelope.parent.manga.categories.toSet()
            require(destination.categoriesByOrder.keys == orderKeys &&
                destination.categoriesByOrder.values.all { it > 0L } &&
                destination.categoriesByOrder.values.distinct().size == orderKeys.size) {
                "POLARIS_BOUND_CATEGORY_COVERAGE"
            }
            fun settings(s: eu.kanade.tachiyomi.data.backup.models.BackupPolarisMergeSettings) =
                SqlDelightPolarisFreshParentAdapter.LinkSettings(
                    infoManga = s.infoManga,
                    getChapterUpdates = s.getChapterUpdates,
                    chapterSortMode = s.chapterSortMode,
                    chapterPriority = s.chapterPriority,
                    downloadChapters = s.downloadChapters,
                )
            val children = envelope.work.links.map { link ->
                SqlDelightPolarisFreshParentAdapter.ChildLink(
                    link.sourceId, link.sourceUrl,
                    if (link.isPending) null else destination.realChildrenByIdentity.getValue(link.sourceId to link.sourceUrl),
                    settings(link.settings),
                )
            }
            SqlDelightPolarisFreshParentAdapter.FreshWork(
                archiveUuid = uuid,
                archiveDigest = admission.sha256,
                archiveSnapshotBytes = admission.canonicalBytes(),
                archive = envelope.parent.manga,
                categoryIdsByArchiveOrder = destination.categoriesByOrder.toMap(),
                children = children,
                rootSettings = settings(envelope.work.rootSettings),
                technical = destination.technical,
                archiveCategories = envelope.referencedCategories,
                boundV2Admission = admission,
            )
        }
    }

    suspend fun restoreDecodedNewOnly(
        adapter: SqlDelightPolarisFreshParentAdapter,
        bundle: BackupPolarisBundle,
        ordinary: List<BackupManga>,
        originalCategories: List<BackupCategory>,
        destinations: List<Destination>,
        codec: PolarisV2EnvelopeCodec<PolarisV2ProtoBufEnvelope>,
    ): List<Long> {
        val works = bindDecoded(bundle, ordinary, originalCategories, destinations, codec)
        return adapter.restoreBoundNewOnly(works)
    }
}
