package polaris.domain.e2e

import polaris.domain.canonical.*
import polaris.domain.health.*
import polaris.domain.language.*
import polaris.domain.open.*
import polaris.domain.progress.*
import polaris.domain.translation.*

private const val NOW = 2_000_000_000_000L

private fun source(
    id: String,
    lang: String,
    count: Int,
    high: Double,
    health: SourceHealthSnapshot,
) = SourceVariant(
    id = id,
    sourceId = id.hashCode().toLong(),
    language = lang,
    title = id,
    totalChapters = count,
    highestChapterNumber = high,
    lastUpdatedEpochMs = NOW,
    health = health,
)

private fun chapter(
    id: String,
    source: SourceVariant,
    number: Double,
    chapterId: Long,
) = ChapterVariant(
    id = id,
    sourceVariant = source,
    chapterId = chapterId,
    chapterNumber = number,
    title = "Chapter $number",
)

fun main() {
    val tracker = SourceHealthTracker()
    val healthy = tracker.apply(tracker.initial(), SourceAccessEvent.Success(250), NOW).snapshot
    val challenged = tracker.apply(
        tracker.initial(),
        SourceAccessEvent.Failure(FailureKind.CHALLENGE),
        NOW,
    ).snapshot

    val pt80 = source("pt80", "pt-BR", 80, 80.0, healthy)
    val pt83Blocked = source("pt83", "pt-BR", 83, 83.0, challenged)
    val en85 = source("en85", "en", 85, 85.0, healthy)

    val route = LanguageRoutePlanner.plan(
        LanguageRouteRequest(targetLanguage = "pt-BR", originalLanguage = "en"),
    )
    check(route == listOf("pt-br", "pt", "en"))

    val planner = ChapterOpenPlanner()

    val chapter79 = planner.plan(
        ChapterOpenRequest(
            canonicalWorkId = "123e4567-e89b-12d3-a456-426614174000",
            canonicalTitle = "The Beginning After the End",
            variants = listOf(
                chapter("pt80-c79", pt80, 79.0, 1079),
                chapter("pt83-c79", pt83Blocked, 79.0, 2079),
                chapter("en85-c79", en85, 79.0, 3079),
            ),
            preferredLanguages = route,
            targetLanguage = "pt-BR",
            nowEpochMs = NOW,
        ),
    ) ?: error("no plan for chapter 79")

    check(chapter79.rankedVariant.variant.sourceVariant.id == "pt80")
    check(chapter79.translation.mode == TranslationOpenMode.READ_ORIGINAL)

    val chapter84 = planner.plan(
        ChapterOpenRequest(
            canonicalWorkId = "123e4567-e89b-12d3-a456-426614174000",
            canonicalTitle = "The Beginning After the End",
            variants = listOf(chapter("en85-c84", en85, 84.0, 3084)),
            preferredLanguages = route,
            targetLanguage = "pt-BR",
            nowEpochMs = NOW,
            translationEnabled = true,
            translatorAvailable = true,
        ),
    ) ?: error("no plan for chapter 84")

    check(chapter84.rankedVariant.variant.sourceVariant.id == "en85")
    check(chapter84.translation.mode == TranslationOpenMode.QUEUE_TRANSLATION)

    val cached84 = planner.plan(
        ChapterOpenRequest(
            canonicalWorkId = "123e4567-e89b-12d3-a456-426614174000",
            canonicalTitle = "The Beginning After the End",
            variants = listOf(chapter("en85-c84", en85, 84.0, 3084)),
            preferredLanguages = route,
            targetLanguage = "pt-BR",
            nowEpochMs = NOW,
            cachedTranslationVariantIds = setOf("en85-c84"),
        ),
    ) ?: error("no cached plan")

    check(cached84.translation.mode == TranslationOpenMode.READ_TRANSLATED_CACHE)

    var progress = CanonicalChapterProgress()
    progress = CanonicalProgressPolicy.observeChild(
        progress,
        ChildChapterProgress(3084, read = true, bookmarked = false, lastPageRead = 30),
        NOW,
    )
    check(progress.read)

    val newPtVariant = ChildChapterProgress(4084, read = false, bookmarked = false, lastPageRead = 12)
    val resume = CanonicalProgressPolicy.resume(progress, newPtVariant)
    check(resume.pageIndex == 0)
    check(progress.read)

    val recovered = tracker.apply(
        SourceHealthRecord(challenged),
        SourceAccessEvent.Success(200),
        NOW + 1000,
    ).snapshot
    check(recovered.state == SourceHealthState.DEGRADED || recovered.state == SourceHealthState.HEALTHY)
    check(recovered.isUsable(NOW + 1000))

    println("SPIKE021_R001_SCENARIO_SIMULATION_PASS")
}
