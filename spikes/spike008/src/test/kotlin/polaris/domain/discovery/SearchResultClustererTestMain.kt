package polaris.domain.discovery

import polaris.domain.matching.WorkCandidate

private fun work(
    source: Long,
    key: String,
    lang: String,
    title: String,
    aliases: Set<String> = emptySet(),
    author: String? = null,
    ids: Map<String, String> = emptyMap(),
    chapters: Set<Double> = emptySet(),
) = WorkCandidate(
    sourceId = source,
    sourceWorkKey = key,
    language = lang,
    title = title,
    aliases = aliases,
    author = author,
    externalIds = ids,
    chapterNumbers = chapters,
)

fun main() {
    val clusterer = SearchResultClusterer()

    run {
        val result = clusterer.cluster(
            listOf(
                work(1, "a", "en", "The Beginning After the End", ids = mapOf("anilist" to "123")),
                work(2, "b", "pt-BR", "O Começo Depois do Fim", ids = mapOf("anilist" to "123")),
                work(3, "c", "en", "Another Work", ids = mapOf("anilist" to "999")),
            ),
        )
        check(result.clusters.size == 2) { result.toString() }
        check(result.clusters.first().members.size == 2)
    }

    run {
        val result = clusterer.cluster(
            listOf(
                work(
                    1, "a", "en", "The Beginning After the End",
                    author = "TurtleMe",
                    chapters = (1..80).map(Int::toDouble).toSet(),
                ),
                work(
                    2, "b", "pt-BR", "O Começo Depois do Fim",
                    author = "TurtleMe",
                    chapters = (1..78).map(Int::toDouble).toSet(),
                ),
            ),
        )
        check(result.clusters.size == 2) { result.toString() }
        check(result.semanticReviewPairs.size == 1) { result.toString() }
    }

    run {
        val result = clusterer.cluster(
            listOf(
                work(1, "a", "en", "Solo-Leveling!!"),
                work(2, "b", "en", "Solo Leveling"),
            ),
        )
        check(result.clusters.single().members.size == 2)
    }

    run {
        val result = clusterer.cluster(
            listOf(
                work(1, "a", "en", "Same Title", ids = mapOf("anilist" to "1")),
                work(2, "b", "en", "Same Title", ids = mapOf("anilist" to "2")),
            ),
        )
        check(result.clusters.size == 2)
    }

    run {
        // A<->B and B<->C look identical by title, but A and C have conflicting
        // trusted external IDs. Transitive clustering must not bridge that conflict.
        val result = clusterer.cluster(
            listOf(
                work(1, "a", "en", "Same Title", ids = mapOf("anilist" to "1")),
                work(2, "b", "en", "Same Title"),
                work(3, "c", "en", "Same Title", ids = mapOf("anilist" to "2")),
            ),
        )
        check(result.clusters.size == 2) { result.toString() }
        check(result.clusters.maxOf { it.members.size } == 2) { result.toString() }
    }

    println("SPIKE008_SEARCH_CLUSTERER_TESTS_PASS")
}
