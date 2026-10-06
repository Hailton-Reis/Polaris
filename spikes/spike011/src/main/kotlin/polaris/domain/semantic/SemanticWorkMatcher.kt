package polaris.domain.semantic

import polaris.domain.matching.WorkCandidate
import polaris.domain.matching.WorkMatchResult

data class SemanticAlias(
    val value: String,
    val language: String? = null,
)

data class SemanticWorkMatchRequest(
    val left: WorkCandidate,
    val right: WorkCandidate,
    val localEvidence: WorkMatchResult,
)

data class SemanticWorkMatchResponse(
    val sameWork: Boolean,
    val confidence: Double,
    val canonicalTitle: String?,
    val aliases: List<SemanticAlias> = emptyList(),
    val reasonCode: String,
) {
    init {
        require(confidence in 0.0..1.0)
    }
}

interface SemanticWorkMatcherProvider {
    suspend fun compare(request: SemanticWorkMatchRequest): SemanticWorkMatchResponse
}

enum class SemanticMergeDecision {
    CONFIRM_MATCH,
    REQUIRE_USER_REVIEW,
    REJECT_MATCH,
}

data class SemanticMergeResult(
    val decision: SemanticMergeDecision,
    val response: SemanticWorkMatchResponse,
)

class SemanticWorkMatchPolicy(
    private val autoConfirmThreshold: Double = 0.90,
    private val reviewThreshold: Double = 0.65,
) {
    fun decide(
        request: SemanticWorkMatchRequest,
        response: SemanticWorkMatchResponse,
    ): SemanticMergeResult {
        val hardConflict = request.localEvidence.evidence.conflictingExternalNamespaces.isNotEmpty()
        val decision = when {
            hardConflict -> SemanticMergeDecision.REJECT_MATCH
            !response.sameWork -> SemanticMergeDecision.REJECT_MATCH
            response.confidence >= autoConfirmThreshold -> SemanticMergeDecision.CONFIRM_MATCH
            response.confidence >= reviewThreshold -> SemanticMergeDecision.REQUIRE_USER_REVIEW
            else -> SemanticMergeDecision.REJECT_MATCH
        }
        return SemanticMergeResult(decision, response)
    }
}
