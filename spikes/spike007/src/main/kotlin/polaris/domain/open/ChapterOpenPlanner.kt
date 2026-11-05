package polaris.domain.open

import polaris.domain.canonical.ChapterVariant
import polaris.domain.canonical.RankedChapterVariant
import polaris.domain.canonical.SourceRanker
import polaris.domain.canonical.SourceRankingContext
import polaris.domain.translation.TranslationDecisionInput
import polaris.domain.translation.TranslationDecisionPolicy
import polaris.domain.translation.TranslationOpenDecision

data class ChapterOpenRequest(
    val canonicalWorkId: String,
    val canonicalTitle: String,
    val variants: List<ChapterVariant>,
    val preferredLanguages: List<String>,
    val targetLanguage: String,
    val nowEpochMs: Long,
    val currentSourceVariantId: String? = null,
    val cachedTranslationVariantIds: Set<String> = emptySet(),
    val translationEnabled: Boolean = true,
    val translatorAvailable: Boolean = true,
)

data class ChapterOpenPlan(
    val rankedVariant: RankedChapterVariant,
    val translation: TranslationOpenDecision,
)

class ChapterOpenPlanner(
    private val sourceRanker: SourceRanker = SourceRanker(),
) {
    fun plan(request: ChapterOpenRequest): ChapterOpenPlan? {
        val ranked = sourceRanker.select(
            variants = request.variants,
            context = SourceRankingContext(
                preferredLanguages = request.preferredLanguages,
                nowEpochMs = request.nowEpochMs,
                currentSourceVariantId = request.currentSourceVariantId,
            ),
        ) ?: return null

        val selected = ranked.variant
        val translation = TranslationDecisionPolicy.decide(
            TranslationDecisionInput(
                canonicalWorkId = request.canonicalWorkId,
                canonicalTitle = request.canonicalTitle,
                sourceLanguage = selected.sourceVariant.language,
                targetLanguage = request.targetLanguage,
                cachedTranslationAvailable = selected.id in request.cachedTranslationVariantIds,
                translationEnabled = request.translationEnabled,
                translatorAvailable = request.translatorAvailable,
            ),
        )

        return ChapterOpenPlan(
            rankedVariant = ranked,
            translation = translation,
        )
    }
}
