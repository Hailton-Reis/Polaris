package polaris.domain.matching

data class WorkCandidate(
    val sourceId: Long,
    val sourceWorkKey: String,
    val language: String,
    val title: String,
    val aliases: Set<String> = emptySet(),
    val author: String? = null,
    val artist: String? = null,
    val description: String? = null,
    val genres: Set<String> = emptySet(),
    val externalIds: Map<String, String> = emptyMap(),
    val chapterNumbers: Set<Double> = emptySet(),
)

enum class WorkMatchDecision {
    AUTO_MATCH,
    REVIEW,
    DIFFERENT,
}

data class WorkMatchEvidence(
    val score: Double,
    val titleSimilarity: Double,
    val aliasExactMatch: Boolean,
    val sharedExternalIds: Map<String, String>,
    val conflictingExternalNamespaces: Set<String>,
    val authorMatch: Boolean,
    val artistMatch: Boolean,
    val genreSimilarity: Double,
    val descriptionSimilarity: Double,
    val chapterSimilarity: Double,
    val reasons: List<String>,
)

data class WorkMatchResult(
    val decision: WorkMatchDecision,
    val evidence: WorkMatchEvidence,
    val shouldAskSemanticProvider: Boolean,
)
