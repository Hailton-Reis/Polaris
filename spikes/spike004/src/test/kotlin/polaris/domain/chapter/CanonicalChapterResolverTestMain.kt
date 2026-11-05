package polaris.domain.chapter

private fun chapter(
    source: String,
    id: Long,
    name: String,
    number: Double? = null,
    lang: String = "pt-BR",
) = SourceChapterCandidate(source, id, lang, name, number)

fun main() {
    val resolver = CanonicalChapterResolver()

    run {
        val groups = resolver.resolve(
            listOf(
                chapter("a", 1, "Capítulo 10,5", 10.5),
                chapter("b", 2, "Chapter 10.5", 10.5, "en"),
            ),
        )
        check(groups.size == 1) { groups.toString() }
        check(groups.single().key.number == 10.5)
        check(groups.single().variants.size == 2)
    }

    run {
        val groups = resolver.resolve(
            listOf(
                chapter("a", 1, "Season 1 - Chapter 1", 1.0),
                chapter("b", 2, "Season 2 - Chapter 1", 1.0),
            ),
        )
        check(groups.size == 2) { groups.toString() }
        check(groups.map { it.key.season }.toSet() == setOf(1, 2))
    }

    run {
        val groups = resolver.resolve(
            listOf(
                chapter("a", 1, "Prólogo"),
                chapter("b", 2, "Chapter 0", 0.0),
            ),
        )
        check(groups.size == 2) { groups.toString() }
        check(groups.any { it.key.kind == ChapterKind.PROLOGUE })
        check(groups.any { it.key.kind == ChapterKind.REGULAR })
    }

    run {
        val reference = (1..30).map(Int::toDouble)
        val zeroBased = (0..29).map(Int::toDouble)
        val offset = ChapterNumberAlignment.detectOffset(reference, zeroBased)
        check(offset != null) { "offset not detected" }
        check(offset.offset == 1.0) { offset.toString() }
        check(offset.overlapRatio >= 0.95)
    }

    run {
        val a = (1..20).map(Int::toDouble)
        val unrelated = (100..119).map(Int::toDouble)
        check(ChapterNumberAlignment.detectOffset(a, unrelated) == null)
    }

    run {
        val groups = resolver.resolve(
            listOf(
                chapter("a", 1, "Chapter 1", 1.0),
                chapter("b", 2, "Episode 0", 0.0, "en"),
            ),
            offsetBySourceVariant = mapOf("b" to 1.0),
        )
        check(groups.size == 1) { groups.toString() }
    }

    run {
        val groups = resolver.resolve(
            listOf(
                chapter("a", 1, "Extra - Valentine's Day"),
                chapter("b", 2, "Extra - Summer Vacation"),
            ),
        )
        check(groups.size == 2) { groups.toString() }
    }

    println("SPIKE004_CANONICAL_CHAPTER_TESTS_PASS")
}
