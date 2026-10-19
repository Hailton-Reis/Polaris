package eu.kanade.tachiyomi.data.backup.models

import kotlinx.serialization.Serializable
import kotlinx.serialization.protobuf.ProtoNumber
import polaris.spike001.backup.parent.BackupPolarisParentPayload
import java.util.UUID

/**
 * Candidate Polaris field inside the existing Yomotsu gzip+ProtoBuf backup.
 * Do NOT wire into production before issue #2 Android + SQLDelight acceptance.
 *
 * Both source ID AND source URL are required for portable child identities.
 * Local manga/merged IDs are never serialized in this record.
 */
@Serializable
data class BackupPolarisBundle(
    @ProtoNumber(1) val formatVersion: Int = CURRENT_FORMAT_VERSION,
    @ProtoNumber(2) val works: List<BackupPolarisWork> = emptyList(),
    // Full BackupManga records, generated with existing MangaBackupCreator,
    // only for linked real children absent from ordinary backupManga.
    @ProtoNumber(3) val supplementalManga: List<BackupManga> = emptyList(),
    // v2 stores the FULL original BackupManga of each virtual parent, not just UUID/title.
    // Tag 4 is additive; tags 1..3 and the outer Backup.polaris tag 107 are unchanged.
    @ProtoNumber(4) val parentSnapshots: List<BackupPolarisParentPayload> = emptyList(),
) {
    companion object {
        const val CURRENT_FORMAT_VERSION = 1 // legacy candidate with no parent payloads
        const val FULL_PARENT_FORMAT_VERSION = 2
    }

    /** Call immediately after decoding, before modifying any destination database. */
    fun validateForImport() {
        require(formatVersion == CURRENT_FORMAT_VERSION || formatVersion == FULL_PARENT_FORMAT_VERSION) {
            "Unsupported Polaris backup version: $formatVersion"
        }
        if (formatVersion == CURRENT_FORMAT_VERSION) {
            require(parentSnapshots.isEmpty()) { "v1 cannot silently carry v2 parent snapshots" }
        } else {
            require(works.isNotEmpty()) { "v2 parent format requires at least one virtual work" }
            require(parentSnapshots.size == works.size) { "Each v2 work needs one complete parent snapshot" }
            require(parentSnapshots.map { it.archiveUuid }.distinct().size == parentSnapshots.size) {
                "Repeated v2 parent UUID"
            }
            require(parentSnapshots.map { it.originalOrdinal }.distinct().size == parentSnapshots.size) {
                "Repeated v2 original index"
            }
            val byUuid = works.associateBy { it.archiveWorkKey }
            val parentUrls = mutableSetOf<String>()
            for (payload in parentSnapshots) {
                val work = requireNotNull(byUuid[payload.archiveUuid]) { "Orphan v2 parent snapshot" }
                require(runCatching { UUID.fromString(payload.archiveUuid).toString() == payload.archiveUuid }
                    .getOrDefault(false)) { "Noncanonical v2 parent UUID" }
                require(work.canonicalUuid == payload.archiveUuid && work.archiveWorkKey == payload.archiveUuid) {
                    "V2 parent UUID must agree with the canonical work identity"
                }
                require(payload.originalOrdinal >= 0 && payload.manga.source == 6969L &&
                    payload.manga.url.isNotBlank() && payload.manga.title == work.displayTitle) {
                    "V2 full parent metadata is missing or inconsistent"
                }
                require(parentUrls.add(payload.manga.url)) { "Two v2 parent snapshots have the same virtual URL" }
            }
        }
        require(works.map { it.archiveWorkKey }.distinct().size == works.size) { "Duplicate archive work key" }
        val identities = works.flatMap { work ->
            require(work.archiveWorkKey.isNotBlank() && work.displayTitle.isNotBlank()) { "Missing portable work key/title" }
            require(work.links.isNotEmpty()) { "Virtual work missing active/pending child links" }
            require(!work.rootSettings.infoManga) { "Virtual root cannot be metadata source" }
            require(work.links.count { it.settings.infoManga } <= 1) { "Multiple metadata sources" }
            val variants = work.links.map { link ->
                require(link.sourceId != 6969L && link.sourceUrl.isNotBlank()) { "Invalid child source identity" }
                require(link.observedTitle.isNotBlank()) { "Missing linked source title" }
                link.sourceId to link.sourceUrl
            }
            require(variants.distinct().size == variants.size) { "Repeated source identity within one virtual work" }
            variants
        }.toSet()
        val snapshotKeys = supplementalManga.map { snapshot ->
            require(snapshot.source != 6969L && snapshot.url.isNotBlank()) { "Invalid real-source snapshot" }
            snapshot.source to snapshot.url
        }
        require(snapshotKeys.distinct().size == snapshotKeys.size) { "Duplicate supplementary manga snapshot" }
        require(snapshotKeys.all { it in identities }) { "Supplementary manga is not linked to any exported work" }
        // Do not materialize a real manga for an association explicitly
        // marked pending; another virtual work may still resolve the same key.
        val resolvedIdentities = works.flatMap { work ->
            work.links.filterNot { it.isPending }.map { it.sourceId to it.sourceUrl }
        }.toSet()
        require(snapshotKeys.all { it in resolvedIdentities }) {
            "Supplementary manga only referenced by pending links must not be restored"
        }
    }

    /**
     * Refuse an incomplete backup: every resolved child needs a corresponding
     * real BackupManga, either ordinary or supplemental. Only genuinely pending
     * source references may omit an actual manga row.
     */
    fun validateSnapshotCoverage(ordinaryManga: List<BackupManga>) {
        validateForImport()
        // Importing a virtual manga through the ordinary Yomotsu restorer AND
        // recreating it from a Polaris UUID produces two parents. Until the
        // portable bundle preserves parent categories/notes and defines safe
        // reuse of the original row, reject this mixed-format archive.
        require(works.isEmpty() || ordinaryManga.none { it.source == 6969L }) {
            "A Polaris archive cannot also carry legacy virtual parents in ordinary manga backups"
        }
        val normal = ordinaryManga.map { it.source to it.url }
        val extra = supplementalManga.map { it.source to it.url }
        require(normal.distinct().size == normal.size) { "Ambiguous normal manga identities" }
        require(normal.none { it in extra }) { "Child snapshot appears in both normal and supplemental backup" }
        val saved = (normal + extra).toSet()
        require(works.flatMap { it.links }.filterNot { it.isPending }.all {
            (it.sourceId to it.sourceUrl) in saved
        }) { "Missing real-child snapshot; refusing incomplete multisource backup" }
    }
}

@Serializable
data class BackupPolarisWork(
    // Stable backup identity; never derive this from local DB IDs or titles.
    @ProtoNumber(1) val archiveWorkKey: String,
    @ProtoNumber(2) val displayTitle: String,
    @ProtoNumber(3) val rootSettings: BackupPolarisMergeSettings,
    // Explicit active or pending links. Never infer removed links from titles.
    @ProtoNumber(4) val links: List<BackupPolarisLink>,
    @ProtoNumber(5) val canonicalUuid: String? = null,
)

@Serializable
data class BackupPolarisLink(
    @ProtoNumber(1) val sourceId: Long,
    @ProtoNumber(2) val sourceUrl: String,
    @ProtoNumber(3) val observedTitle: String,
    @ProtoNumber(4) val settings: BackupPolarisMergeSettings,
    // The association's local manga row was absent when exported; no fabricated ID.
    @ProtoNumber(5) val isPending: Boolean = false,
)

@Serializable
data class BackupPolarisMergeSettings(
    @ProtoNumber(1) val infoManga: Boolean,
    @ProtoNumber(2) val getChapterUpdates: Boolean,
    @ProtoNumber(3) val chapterSortMode: Long,
    @ProtoNumber(4) val chapterPriority: Long,
    @ProtoNumber(5) val downloadChapters: Boolean,
)
