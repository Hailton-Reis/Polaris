package polaris.domain.semantic

import polaris.domain.matching.AutomaticWorkMatcher
import polaris.domain.matching.WorkCandidate

private fun work(
    id: String,
    language: String,
    title: String,
    externalIds: Map<String, String> = emptyMap(),
    author: String? = null,
    chapters: Set<Double> = emptySet(),
) = WorkCandidate(
    sourceId = id.hashCode().toLong(),
    sourceWorkKey = id,
    language = language,
    title = title,
    externalIds = externalIds,
    author = author,
    chapterNumbers = chapters,
)

fun main() {
    val matcher = AutomaticWorkMatcher()
    val policy = SemanticWorkMatchPolicy()

    run {
        val left = work("a", "en", "The Beginning After the End", author = "TurtleMe", chapters = (1..80).map(Int::toDouble).toSet())
        val right = work("b", "pt-BR", "O Começo Depois do Fim", author = "TurtleMe", chapters = (1..79).map(Int::toDouble).toSet())
        val local = matcher.compare(left, right)
        val response = SemanticWorkMatchResponse(
            sameWork = true,
            confidence = 0.96,
            canonicalTitle = "The Beginning After the End",
            aliases = listOf(SemanticAlias("O Começo Depois do Fim", "pt-BR")),
            reasonCode = "translated_title_same_author_structure",
        )
        val request = SemanticWorkMatchRequest(left, right, local)
        val result = policy.decide(request, response)
        check(result.decision == SemanticMergeDecision.CONFIRM_MATCH)
        check(SemanticWorkMatchPrompt.userPrompt(request).contains("TurtleMe"))
    }

    run {
        val left = work("a", "en", "Same Title", externalIds = mapOf("anilist" to "1"))
        val right = work("b", "en", "Same Title", externalIds = mapOf("anilist" to "2"))
        val local = matcher.compare(left, right)
        val response = SemanticWorkMatchResponse(
            sameWork = true,
            confidence = 0.99,
            canonicalTitle = "Same Title",
            reasonCode = "model_thinks_same",
        )
        val result = policy.decide(SemanticWorkMatchRequest(left, right, local), response)
        check(result.decision == SemanticMergeDecision.REJECT_MATCH)
    }

    run {
        val left = work("a", "en", "Title One")
        val right = work("b", "pt-BR", "Título Um")
        val local = matcher.compare(left, right)
        val response = SemanticWorkMatchResponse(true, 0.78, "Title One", reasonCode = "possible_translation")
        val result = policy.decide(SemanticWorkMatchRequest(left, right, local), response)
        check(result.decision == SemanticMergeDecision.REQUIRE_USER_REVIEW)
    }

    println("SPIKE011_SEMANTIC_MATCHER_TESTS_PASS")
}
