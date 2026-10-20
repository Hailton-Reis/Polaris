package polaris.spike001.backup.restore

import eu.kanade.tachiyomi.data.backup.models.BackupCategory
import eu.kanade.tachiyomi.data.backup.models.BackupPolarisWork
import polaris.spike001.backup.parent.BackupPolarisParentPayload
import kotlinx.serialization.Serializable
import kotlinx.serialization.protobuf.ProtoNumber
import kotlinx.serialization.protobuf.ProtoBuf
import java.util.UUID

/**
 * Staging only. An inner, canonical v2 fingerprint envelope created FROM
 * decoded ProtoBuf DTOs; not a substitute for the top-level archive's tag 107.
 *
 * Its link snapshots capture observed title, root settings, pending bit and
 * portable source+URL, while parent carries all BackupManga fields. Local DB
 * IDs and category destination IDs are purposefully not serialized.
 */
@Serializable
data class PolarisV2ProtoBufEnvelope(
    @ProtoNumber(1) val formatVersion: Int,
    @ProtoNumber(2) val work: BackupPolarisWork,
    @ProtoNumber(3) val parent: BackupPolarisParentPayload,
    @ProtoNumber(4) val referencedCategories: List<BackupCategory>,
) {
    fun validateDecoded() {
        require(formatVersion == 2) { "POLARIS_V2_UNSUPPORTED_ENVELOPE" }
        require(work.canonicalUuid != null &&
            runCatching { UUID.fromString(work.canonicalUuid).toString() == work.canonicalUuid }.getOrDefault(false) &&
            work.archiveWorkKey == work.canonicalUuid &&
            parent.archiveUuid == work.canonicalUuid && parent.manga.source == 6969L) {
            "POLARIS_V2_PARENT_IDENTITY_MISMATCH"
        }
        require(parent.originalOrdinal >= 0 && parent.manga.title == work.displayTitle &&
            work.links.isNotEmpty() && !work.rootSettings.infoManga &&
            work.links.count { it.settings.infoManga } == 1) {
            "POLARIS_V2_PARENT_WORK_MISMATCH"
        }
        val orders = parent.manga.categories
        require(orders.distinct().size == orders.size &&
            referencedCategories.size == orders.size &&
            referencedCategories.map { it.order }.toSet() == orders.toSet() &&
            referencedCategories.map { it.name }.distinct().size == referencedCategories.size &&
            referencedCategories.all { it.name.isNotBlank() }) {
            "POLARIS_V2_CATEGORY_SNAPSHOT_MISMATCH"
        }
        require(work.links.map { it.sourceId to it.sourceUrl }.distinct().size == work.links.size &&
            work.links.all { it.sourceId != 6969L && it.sourceUrl.isNotBlank() &&
                it.observedTitle.isNotBlank() } &&
            (work.links.map { it.settings.chapterPriority } + work.rootSettings.chapterPriority)
                .distinct().size == work.links.size + 1) {
            "POLARIS_V2_INVALID_PORTABLE_LINKS"
        }
    }
}

/** Compile against the pinned real Kotlinx ProtoBuf dependency in Android. */
class PolarisV2ProtoBufCodec(private val proto: ProtoBuf) : PolarisV2EnvelopeCodec<PolarisV2ProtoBufEnvelope> {
    override fun encodeCanonical(value: PolarisV2ProtoBufEnvelope): ByteArray {
        value.validateDecoded()
        return proto.encodeToByteArray(PolarisV2ProtoBufEnvelope.serializer(), value)
    }
    override fun decodeCanonical(bytes: ByteArray): PolarisV2ProtoBufEnvelope =
        proto.decodeFromByteArray(PolarisV2ProtoBufEnvelope.serializer(), bytes).also { it.validateDecoded() }
}
