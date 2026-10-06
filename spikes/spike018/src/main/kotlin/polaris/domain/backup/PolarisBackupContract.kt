package polaris.domain.backup

/**
 * Provider-neutral backup contract. Android may serialize this with kotlinx.serialization.
 * Transient source-health observations are intentionally optional.
 */
data class PolarisBackup(
    val schemaVersion: Int = CURRENT_SCHEMA_VERSION,
    val exportedAtEpochMs: Long,
    val works: List<BackupWork>,
    val linkOverrides: List<BackupWorkLinkOverride> = emptyList(),
) {
    init { require(schemaVersion > 0) }
    companion object { const val CURRENT_SCHEMA_VERSION = 1 }
}

data class BackupWorkLinkOverride(
    val leftSourceId: Long,
    val leftSourceWorkKey: String,
    val rightSourceId: Long,
    val rightSourceWorkKey: String,
    val decision: String,
    val createdAtEpochMs: Long,
)

data class BackupWork(
    val stableKey: String,
    val preferredTitle: String,
    val originalLanguage: String?,
    val aliases: List<BackupAlias> = emptyList(),
    val externalIds: Map<String, String> = emptyMap(),
    val variants: List<BackupSourceVariant> = emptyList(),
    val chapters: List<BackupCanonicalChapter> = emptyList(),
    val translationScopeKey: String = "polaris:$stableKey",
)

data class BackupAlias(
    val value: String,
    val language: String? = null,
    val confidence: Double = 1.0,
    val provenance: String,
)

data class BackupSourceVariant(
    val sourceId: Long,
    val sourceWorkKey: String,
    val language: String,
    val observedTitle: String,
)

data class BackupCanonicalChapter(
    val season: Int? = null,
    val number: Double? = null,
    val part: Int? = null,
    val kind: String,
    val semanticKey: String? = null,
    val read: Boolean,
    val bookmarked: Boolean,
    val lastVariantHint: BackupVariantHint? = null,
    val variants: List<BackupChapterVariant> = emptyList(),
)

data class BackupVariantHint(
    val sourceId: Long,
    val sourceWorkKey: String,
    val chapterUrl: String,
)

data class BackupChapterVariant(
    val sourceId: Long,
    val sourceWorkKey: String,
    val chapterUrl: String,
    val observedName: String,
    val scanlator: String? = null,
)

data class RestoreResolution(
    val matchedSourceVariants: Int,
    val unresolvedSourceVariants: Int,
    val matchedChapterVariants: Int,
    val unresolvedChapterVariants: Int,
)

object PolarisRestorePolicy {
    fun validate(backup: PolarisBackup) {
        require(backup.schemaVersion <= PolarisBackup.CURRENT_SCHEMA_VERSION) {
            "Backup schema ${backup.schemaVersion} is newer than supported ${PolarisBackup.CURRENT_SCHEMA_VERSION}"
        }
        backup.linkOverrides.forEach { override ->
            require(
                override.leftSourceId != override.rightSourceId ||
                    override.leftSourceWorkKey != override.rightSourceWorkKey,
            ) { "A work-link override cannot reference the same source work twice" }
            require(
                override.decision == "FORCE_SAME_WORK" ||
                    override.decision == "FORCE_DIFFERENT_WORK",
            ) { "Invalid work-link override decision" }
        }
        backup.works.forEach { work ->
            require(
                work.stableKey.matches(
                    Regex("[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"),
                ),
            ) { "Invalid canonical work UUID" }
            require(work.preferredTitle.isNotBlank())
            require(work.translationScopeKey.isNotBlank())
            work.aliases.forEach { require(it.confidence in 0.0..1.0) }
            val duplicateVariant = work.variants
                .groupBy { it.sourceId to it.sourceWorkKey }
                .any { it.value.size > 1 }
            require(!duplicateVariant) { "Duplicate source variant in ${work.stableKey}" }
        }
    }
}
