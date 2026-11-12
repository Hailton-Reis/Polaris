package polaris.domain.canonical

private const val NOW = 2_000_000_000_000L
private const val DAY = 86_400_000L

private fun source(
    id: String,
    lang: String,
    chapters: Int,
    high: Double,
    state: SourceHealthState = SourceHealthState.HEALTHY,
    success: Double = 1.0,
    latency: Long = 300,
    failures: Int = 0,
    updatedDaysAgo: Long = 0,
    cooldownUntil: Long? = null,
) = SourceVariant(
    id = id,
    sourceId = id.hashCode().toLong(),
    language = lang,
    title = id,
    totalChapters = chapters,
    highestChapterNumber = high,
    lastUpdatedEpochMs = NOW - updatedDaysAgo * DAY,
    health = SourceHealthSnapshot(
        state = state,
        successRate = success,
        averageLatencyMs = latency,
        consecutiveFailures = failures,
        cooldownUntilEpochMs = cooldownUntil,
    ),
)

private fun chapter(id: String, source: SourceVariant, number: Double) = ChapterVariant(
    id = id,
    sourceVariant = source,
    chapterId = id.hashCode().toLong(),
    chapterNumber = number,
    title = "Chapter $number",
)

private val ranker = SourceRanker()
private val prefs = listOf("pt-BR", "pt", "en", "ja", "ko", "zh")

private fun context(current: String? = null, hysteresis: Double = 60.0) = SourceRankingContext(
    preferredLanguages = prefs,
    nowEpochMs = NOW,
    currentSourceVariantId = current,
    hysteresisMargin = hysteresis,
)

fun main() {
    run {
        val a80 = source("pt80", "pt-BR", 80, 80.0, updatedDaysAgo = 3)
        val b83 = source("pt83", "pt-BR", 83, 83.0, updatedDaysAgo = 0)
        val selected = ranker.select(listOf(chapter("a", a80, 79.0), chapter("b", b83, 79.0)), context())
        check(selected?.variant?.sourceVariant?.id == "pt83") { selected.toString() }
    }

    run {
        val challenged83 = source("pt83", "pt-BR", 83, 83.0, state = SourceHealthState.CHALLENGED)
        val healthy80 = source("pt80", "pt-BR", 80, 80.0)
        val selected = ranker.select(listOf(chapter("a", challenged83, 79.0), chapter("b", healthy80, 79.0)), context())
        check(selected?.variant?.sourceVariant?.id == "pt80") { selected.toString() }
    }

    run {
        val pt = source("pt", "pt-BR", 80, 80.0, state = SourceHealthState.DEGRADED, success = 0.90, failures = 1)
        val en = source("en", "en", 120, 120.0)
        val selected = ranker.select(listOf(chapter("pt", pt, 79.0), chapter("en", en, 79.0)), context())
        check(selected?.variant?.sourceVariant?.id == "pt") { selected.toString() }
    }

    run {
        val en = source("en", "en", 120, 120.0)
        val selected = ranker.select(listOf(chapter("en84", en, 84.0)), context())
        check(selected?.variant?.sourceVariant?.id == "en") { selected.toString() }
    }

    run {
        val authPt = source("auth-pt", "pt-BR", 100, 100.0, state = SourceHealthState.AUTH_REQUIRED)
        val en = source("en", "en", 120, 120.0)
        val selected = ranker.select(listOf(chapter("pt", authPt, 50.0), chapter("en", en, 50.0)), context())
        check(selected?.variant?.sourceVariant?.id == "en") { selected.toString() }
    }

    run {
        val current = source("current", "pt-BR", 82, 82.0, updatedDaysAgo = 1)
        val slightlyBetter = source("better", "pt-BR", 83, 83.0, updatedDaysAgo = 0)
        val selected = ranker.select(
            listOf(chapter("cur", current, 70.0), chapter("better", slightlyBetter, 70.0)),
            context(current = "current", hysteresis = 60.0),
        )
        check(selected?.variant?.sourceVariant?.id == "current") { selected.toString() }
        check(selected != null && "kept_by_hysteresis" in selected.reasons)
    }

    run {
        val current = source("current", "pt-BR", 82, 82.0, state = SourceHealthState.DEGRADED, success = 0.60, latency = 3000, failures = 3)
        val better = source("better", "pt-BR", 83, 83.0)
        val selected = ranker.select(
            listOf(chapter("cur", current, 70.0), chapter("better", better, 70.0)),
            context(current = "current", hysteresis = 60.0),
        )
        check(selected?.variant?.sourceVariant?.id == "better") { selected.toString() }
    }

    run {
        val limited = source("limited", "pt-BR", 90, 90.0, state = SourceHealthState.RATE_LIMITED, cooldownUntil = NOW + 10_000)
        val en = source("en", "en", 120, 120.0)
        val blocked = ranker.select(listOf(chapter("pt", limited, 50.0), chapter("en", en, 50.0)), context())
        check(blocked?.variant?.sourceVariant?.id == "en") { blocked.toString() }

        val recovered = limited.copy(health = limited.health.copy(cooldownUntilEpochMs = NOW - 1))
        val usable = ranker.select(listOf(chapter("pt", recovered, 50.0), chapter("en", en, 50.0)), context())
        check(usable?.variant?.sourceVariant?.id == "limited") { usable.toString() }
    }

    println("SPIKE002_SOURCE_RANKER_TESTS_PASS")
}
