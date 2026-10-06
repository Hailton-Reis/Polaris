package polaris.domain.canonical

data class CanonicalWork(
    val id: String,
    val preferredTitle: String,
    val originalLanguage: String?,
    val aliases: Set<String> = emptySet(),
    val externalIds: Map<String, String> = emptyMap(),
    val variants: List<SourceVariant> = emptyList(),
)

data class SourceVariant(
    val id: String,
    val sourceId: Long,
    val language: String,
    val title: String,
    val totalChapters: Int,
    val highestChapterNumber: Double?,
    val lastUpdatedEpochMs: Long?,
    val health: SourceHealthSnapshot,
)

data class ChapterVariant(
    val id: String,
    val sourceVariant: SourceVariant,
    val chapterId: Long,
    val chapterNumber: Double?,
    val title: String,
    val scanlator: String? = null,
)

enum class SourceHealthState {
    HEALTHY,
    DEGRADED,
    AUTH_REQUIRED,
    AUTH_EXPIRED,
    CHALLENGED,
    RATE_LIMITED,
    BROKEN,
    UNREACHABLE,
}

data class SourceHealthSnapshot(
    val state: SourceHealthState,
    val successRate: Double = 1.0,
    val averageLatencyMs: Long = 0L,
    val consecutiveFailures: Int = 0,
    val lastSuccessEpochMs: Long? = null,
    val cooldownUntilEpochMs: Long? = null,
) {
    init {
        require(successRate in 0.0..1.0) { "successRate must be between 0 and 1" }
        require(averageLatencyMs >= 0) { "averageLatencyMs must be >= 0" }
        require(consecutiveFailures >= 0) { "consecutiveFailures must be >= 0" }
    }

    fun isUsable(nowEpochMs: Long): Boolean = when (state) {
        SourceHealthState.HEALTHY,
        SourceHealthState.DEGRADED,
        -> true

        SourceHealthState.RATE_LIMITED -> cooldownUntilEpochMs?.let { it <= nowEpochMs } ?: false

        SourceHealthState.AUTH_REQUIRED,
        SourceHealthState.AUTH_EXPIRED,
        SourceHealthState.CHALLENGED,
        SourceHealthState.BROKEN,
        SourceHealthState.UNREACHABLE,
        -> false
    }
}
