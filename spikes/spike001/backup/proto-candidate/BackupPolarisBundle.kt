package eu.kanade.tachiyomi.data.backup.models

import kotlinx.serialization.Serializable
import kotlinx.serialization.protobuf.ProtoNumber

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
) {
    companion object { const val CURRENT_FORMAT_VERSION = 1 }

    /** Call immediately after decoding, before modifying any destination database. */
    fun validateForImport() {
        require(formatVersion == CURRENT_FORMAT_VERSION) { "Unsupported Polaris backup version: $formatVersion" }
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
)

@Serializable
data class BackupPolarisMergeSettings(
    @ProtoNumber(1) val infoManga: Boolean,
    @ProtoNumber(2) val getChapterUpdates: Boolean,
    @ProtoNumber(3) val chapterSortMode: Long,
    @ProtoNumber(4) val chapterPriority: Long,
    @ProtoNumber(5) val downloadChapters: Boolean,
)
