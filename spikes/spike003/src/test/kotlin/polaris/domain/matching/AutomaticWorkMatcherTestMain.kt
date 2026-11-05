package polaris.domain.matching

private val matcher = AutomaticWorkMatcher()

private fun candidate(
    key: String,
    lang: String,
    title: String,
    aliases: Set<String> = emptySet(),
    author: String? = null,
    artist: String? = null,
    ids: Map<String, String> = emptyMap(),
    genres: Set<String> = emptySet(),
    chapters: Set<Double> = emptySet(),
    description: String? = null,
) = WorkCandidate(
    sourceId = key.hashCode().toLong(),
    sourceWorkKey = key,
    language = lang,
    title = title,
    aliases = aliases,
    author = author,
    artist = artist,
    externalIds = ids,
    genres = genres,
    chapterNumbers = chapters,
    description = description,
)

fun main() {
    run {
        val en = candidate("en", "en", "The Beginning After the End", ids = mapOf("anilist" to "123"))
        val pt = candidate("pt", "pt-BR", "O Começo Depois do Fim", ids = mapOf("anilist" to "123"))
        val result = matcher.compare(en, pt)
        check(result.decision == WorkMatchDecision.AUTO_MATCH) { result.toString() }
        check("anilist" in result.evidence.sharedExternalIds)
    }

    run {
        val en = candidate("en", "en", "The Beginning After the End")
        val pt = candidate("pt", "pt-BR", "O Começo Após o Fim", aliases = setOf("The Beginning After the End"))
        val result = matcher.compare(en, pt)
        check(result.decision == WorkMatchDecision.AUTO_MATCH) { result.toString() }
        check(result.evidence.aliasExactMatch)
    }

    run {
        val en = candidate(
            "en", "en", "The Beginning After the End",
            author = "TurtleMe",
            genres = setOf("Fantasy", "Action"),
            chapters = (1..80).map(Int::toDouble).toSet(),
        )
        val pt = candidate(
            "pt", "pt-BR", "O Começo Depois do Fim",
            author = "TurtleMe",
            genres = setOf("Fantasia", "Ação"),
            chapters = (1..78).map(Int::toDouble).toSet(),
        )
        val result = matcher.compare(en, pt)
        check(result.decision == WorkMatchDecision.REVIEW) { result.toString() }
        check(result.shouldAskSemanticProvider) { result.toString() }
    }

    run {
        val one = candidate("one", "en", "Solo-Leveling!!")
        val two = candidate("two", "en", "Solo Leveling")
        val result = matcher.compare(one, two)
        check(result.decision == WorkMatchDecision.AUTO_MATCH) { result.toString() }
    }

    run {
        val one = candidate("one", "en", "A Similar Title", ids = mapOf("anilist" to "111"))
        val two = candidate("two", "en", "A Similar Title", ids = mapOf("anilist" to "999"))
        val result = matcher.compare(one, two)
        check(result.decision == WorkMatchDecision.DIFFERENT) { result.toString() }
    }

    run {
        val one = candidate(
            "one",
            "en",
            "Same Work",
            ids = mapOf("anilist" to "111", "mal" to "222"),
        )
        val two = candidate(
            "two",
            "pt-BR",
            "Same Work",
            ids = mapOf("anilist" to "111", "mal" to "999"),
        )
        val result = matcher.compare(one, two)
        check(result.decision == WorkMatchDecision.DIFFERENT) { result.toString() }
        check("mal" in result.evidence.conflictingExternalNamespaces)
    }

    println("SPIKE003_WORK_MATCHER_TESTS_PASS")
}
