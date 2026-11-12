package polaris.domain.open

import polaris.domain.canonical.ChapterVariant
import polaris.domain.canonical.SourceHealthSnapshot
import polaris.domain.canonical.SourceHealthState
import polaris.domain.canonical.SourceVariant
import polaris.domain.translation.TranslationOpenMode

private const val NOW = 2_000_000_000_000L

private fun source(
    id: String,
    lang: String,
    chapters: Int,
    state: SourceHealthState = SourceHealthState.HEALTHY,
) = SourceVariant(
    id = id,
    sourceId = id.hashCode().toLong(),
    language = lang,
    title = id,
    totalChapters = chapters,
    highestChapterNumber = chapters.toDouble(),
    lastUpdatedEpochMs = NOW,
    health = SourceHealthSnapshot(state = state),
)

private fun chapter(id: String, source: SourceVariant, number: Double) = ChapterVariant(
    id = id,
    sourceVariant = source,
    chapterId = id.hashCode().toLong(),
    chapterNumber = number,
    title = "Chapter $number",
)

private fun request(
    variants: List<ChapterVariant>,
    cached: Set<String> = emptySet(),
) = ChapterOpenRequest(
    canonicalWorkId = "tbate",
    canonicalTitle = "The Beginning After the End",
    variants = variants,
    preferredLanguages = listOf("pt-BR", "pt", "en", "ko"),
    targetLanguage = "pt-BR",
    nowEpochMs = NOW,
    cachedTranslationVariantIds = cached,
)

fun main() {
    val planner = ChapterOpenPlanner()

    run {
        val pt80 = source("pt80", "pt-BR", 80)
        val pt83 = source("pt83", "pt-BR", 83)
        val en85 = source("en85", "en", 85)
        val plan = planner.plan(
            request(
                listOf(
                    chapter("pt80-82", pt80, 82.0),
                    chapter("pt83-82", pt83, 82.0),
                    chapter("en85-82", en85, 82.0),
                ),
            ),
        )
        check(plan != null)
        check(plan.rankedVariant.variant.sourceVariant.id == "pt83") { plan.toString() }
        check(plan.translation.mode == TranslationOpenMode.READ_ORIGINAL)
    }

    run {
        val challengedPt = source("pt83", "pt-BR", 83, SourceHealthState.CHALLENGED)
        val en85 = source("en85", "en", 85)
        val plan = planner.plan(
            request(
                listOf(
                    chapter("pt-84", challengedPt, 84.0),
                    chapter("en-84", en85, 84.0),
                ),
            ),
        )
        check(plan != null)
        check(plan.rankedVariant.variant.sourceVariant.id == "en85")
        check(plan.translation.mode == TranslationOpenMode.QUEUE_TRANSLATION)
    }

    run {
        val en85 = source("en85", "en", 85)
        val variant = chapter("en-84", en85, 84.0)
        val plan = planner.plan(request(listOf(variant), cached = setOf(variant.id)))
        check(plan != null)
        check(plan.translation.mode == TranslationOpenMode.READ_TRANSLATED_CACHE)
    }

    run {
        val brokenPt = source("pt", "pt-BR", 83, SourceHealthState.BROKEN)
        val challengedEn = source("en", "en", 85, SourceHealthState.CHALLENGED)
        check(planner.plan(request(listOf(chapter("pt", brokenPt, 84.0), chapter("en", challengedEn, 84.0)))) == null)
    }

    println("SPIKE007_CHAPTER_OPEN_PLANNER_TESTS_PASS")
}
