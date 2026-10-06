package polaris.domain.discovery

import polaris.domain.canonical.SourceHealthSnapshot
import polaris.domain.canonical.SourceHealthState

private const val NOW = 2_000_000_000_000L

private fun source(id: Long, lang: String, state: SourceHealthState = SourceHealthState.HEALTHY) =
    DiscoverySource(
        sourceId = id,
        language = lang,
        health = SourceHealthSnapshot(state),
    )

fun main() {
    val planner = AliasSearchPlanner()

    val identity = DiscoveryIdentity(
        canonicalTitle = "The Beginning After the End",
        originalLanguage = "en",
        aliases = listOf(
            WorkAlias("O Começo Depois do Fim", "pt-BR", 1.0),
            WorkAlias("O Começo Após o Fim", "pt-BR", 0.9),
            WorkAlias("The Beginning After the End", "en", 1.0),
        ),
    )

    run {
        val tasks = planner.plan(
            identity,
            listOf(source(1, "pt-BR"), source(2, "en")),
            NOW,
        )
        val pt = tasks.first { it.sourceId == 1L }
        val en = tasks.first { it.sourceId == 2L }
        check(pt.queries.first() == "O Começo Depois do Fim") { pt.toString() }
        check(pt.queries.size == 2)
        check(en.queries.first() == "The Beginning After the End") { en.toString() }
    }

    run {
        val tasks = planner.plan(
            identity,
            listOf(source(1, "pt-BR", SourceHealthState.CHALLENGED), source(2, "en")),
            NOW,
        )
        check(tasks.none { it.sourceId == 1L })
        check(tasks.any { it.sourceId == 2L })
    }

    run {
        val noJapaneseAlias = planner.plan(identity, listOf(source(3, "ja")), NOW).single()
        check(noJapaneseAlias.queries == listOf("The Beginning After the End"))
    }

    println("SPIKE009_ALIAS_SEARCH_PLANNER_TESTS_PASS")
}
