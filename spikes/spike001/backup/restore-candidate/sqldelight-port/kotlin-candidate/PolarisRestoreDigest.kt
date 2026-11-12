package polaris.spike001.backup.restore.sqldelight

import polaris.spike001.backup.restore.RestoredPolarisWork
import java.security.MessageDigest

/**
 * A versioned and length-prefixed fingerprint of the exact association snapshot.
 * Includes settings, local child IDs and root flags so retries cannot silently
 * restore links deliberately removed or modified by the user after import.
 * Fingerprints are LOCAL ledger entries, never portable backup identities.
 */
object PolarisRestoreDigest {
    fun of(work: RestoredPolarisWork): String {
        val text = buildString {
            fun field(value: String) { append(value.length).append(':').append(value) }
            field("polaris-restore-ledger-v1")
            field(work.archiveUuid)
            field(work.title)
            with(work.rootSettings) {
                field(infoManga.toString()); field(getChapterUpdates.toString())
                field(chapterSortMode.toString()); field(chapterPriority.toString())
                field(downloadChapters.toString())
            }
            field(work.children.size.toString())
            work.children.forEach { link ->
                field(link.sourceId.toString()); field(link.sourceUrl)
                field(link.realMangaId?.toString() ?: "<pending>")
                field(link.wasPending.toString())
                with(link.settings) {
                    field(infoManga.toString()); field(getChapterUpdates.toString())
                    field(chapterSortMode.toString()); field(chapterPriority.toString())
                    field(downloadChapters.toString())
                }
            }
        }
        return MessageDigest.getInstance("SHA-256")
            .digest(text.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }
    }
}
