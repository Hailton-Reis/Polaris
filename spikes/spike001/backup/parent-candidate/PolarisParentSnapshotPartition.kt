package polaris.spike001.backup.parent

import eu.kanade.tachiyomi.data.backup.models.BackupManga
import kotlinx.serialization.Serializable
import kotlinx.serialization.protobuf.ProtoNumber
import java.util.UUID

/** FULL pinned Yomotsu BackupManga; nothing (categories/notes/memo/chapters/history/tracking) is dropped. */
@Serializable
data class BackupPolarisParentPayload(
    @ProtoNumber(1) val archiveUuid: String,
    @ProtoNumber(2) val manga: BackupManga,
    @ProtoNumber(3) val originalOrdinal: Int,
)

/** Captured from selected Manga.zip(MangaBackupCreator(...)) before splitting any ordinary backups. */
data class CapturedMangaSnapshot(
    val localMangaId: Long,
    val selectedSource: Long,
    val selectedUrl: String,
    val snapshot: BackupManga,
)

/** Captured directly from the UUID-aware exporter, NOT inferred from titles/URLs. */
data class ExpectedVirtualParent(
    val localMangaId: Long,
    val archiveUuid: String,
    val selectedUrl: String,
    val selectedTitle: String,
)

/** Staged two-lane archive layout; does NOT write DB rows or serialize a final APK backup. */
data class PolarisParentPartition(
    val ordinaryManga: List<BackupManga>,
    val virtualParents: List<BackupPolarisParentPayload>,
    val originalCount: Int,
) {
    /** Proves the staging split is bijective before any external encode or restore. */
    fun reassembleOriginalOrder(): List<BackupManga> {
        require(originalCount == ordinaryManga.size + virtualParents.size)
        val ordered = arrayOfNulls<BackupManga>(originalCount)
        for (p in virtualParents) {
            require(p.originalOrdinal in 0 until originalCount && ordered[p.originalOrdinal] == null)
            ordered[p.originalOrdinal] = p.manga
        }
        val iterator = ordinaryManga.iterator()
        for (i in ordered.indices) {
            if (ordered[i] == null) {
                check(iterator.hasNext()) { "Ordinary manga count changed after parent split" }
                ordered[i] = iterator.next()
            }
        }
        check(!iterator.hasNext()) { "Extra ordinary mangas after parent split" }
        return ordered.map { checkNotNull(it) }
    }
}

object PolarisParentSnapshotPartitioner {
    private const val VIRTUAL_SOURCE = 6969L

    /**
     * A conservative backup PRODUCER staging gate: require all selected virtual mangas
     * to be paired with an explicit stable UUID and full original BackupManga payload.
     * The eventual importer must create/reuse one parent per UUID and apply FULL
     * payload on that exact resulting ID, in a reviewed transaction. Not implemented here.
     */
    fun partition(
        captured: List<CapturedMangaSnapshot>,
        parents: List<ExpectedVirtualParent>,
    ): PolarisParentPartition {
        require(parents.isNotEmpty()) { "Use ordinary Yomotsu backup for zero virtual parents" }
        require(captured.map { it.localMangaId }.distinct().size == captured.size) { "Repeated local manga ID" }
        require(parents.map { it.localMangaId }.distinct().size == parents.size) { "Repeated parent manga ID" }
        require(parents.map { it.archiveUuid }.distinct().size == parents.size) { "Repeated parent UUID" }
        for (parent in parents) {
            require(runCatching { UUID.fromString(parent.archiveUuid).toString() == parent.archiveUuid }.getOrDefault(false)) {
                "Noncanonical parent UUID"
            }
            require(parent.localMangaId > 0L && parent.selectedUrl.isNotBlank() && parent.selectedTitle.isNotBlank())
        }
        for (item in captured) {
            require(item.localMangaId > 0L) { "Invalid local manga ID" }
            require(item.snapshot.source == item.selectedSource && item.snapshot.url == item.selectedUrl) {
                "MangaBackupCreator snapshot changed source/URL or order"
            }
        }
        val expected = parents.associateBy { it.localMangaId }
        val ordinary = mutableListOf<BackupManga>()
        val parentPayloads = mutableListOf<BackupPolarisParentPayload>()
        captured.forEachIndexed { i, entry ->
            if (entry.selectedSource != VIRTUAL_SOURCE) {
                require(entry.localMangaId !in expected) { "Expected parent is not virtual" }
                ordinary.add(entry.snapshot)
            } else {
                val parent = requireNotNull(expected[entry.localMangaId]) {
                    "Virtual manga has no archive UUID; refuse accidental data loss"
                }
                require(entry.selectedUrl == parent.selectedUrl && entry.snapshot.title == parent.selectedTitle) {
                    "Virtual parent title or URL changed during snapshot creation"
                }
                parentPayloads.add(BackupPolarisParentPayload(parent.archiveUuid, entry.snapshot, i))
            }
        }
        require(parentPayloads.size == parents.size) { "Expected virtual parent was not captured" }
        require(ordinary.none { it.source == VIRTUAL_SOURCE }) { "Virtual parent leaked to ordinary backup" }
        return PolarisParentPartition(ordinary, parentPayloads, captured.size).also { p ->
            // Identity preservation includes every mutable field on the actual BackupManga object.
            // Serialization and post-restore identity handling remain separate blockers.
            check(p.reassembleOriginalOrder().zip(captured).all { (a, b) -> a === b.snapshot }) {
                "Parent split did not preserve original complete BackupManga objects"
            }
        }
    }
}
