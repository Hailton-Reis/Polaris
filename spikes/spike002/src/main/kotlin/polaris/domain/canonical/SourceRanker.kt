package polaris.domain.canonical

import kotlin.math.min

data class SourceRankingContext(
    val preferredLanguages: List<String>,
    val nowEpochMs: Long,
    val currentSourceVariantId: String? = null,
    val hysteresisMargin: Double = 60.0,
)

data class RankedChapterVariant(
    val variant: ChapterVariant,
    val languageTier: Int,
    val score: Double,
    val reasons: List<String>,
)

class SourceRanker {

    fun select(
        variants: List<ChapterVariant>,
        context: SourceRankingContext,
    ): RankedChapterVariant? {
        val ranked = rank(variants, context)
        if (ranked.isEmpty()) return null

        val best = ranked.first()
        val current = context.currentSourceVariantId?.let { currentId ->
            ranked.firstOrNull {
                it.variant.sourceVariant.id == currentId && it.languageTier == best.languageTier
            }
        }

        return if (current != null && best.score - current.score <= context.hysteresisMargin) {
            current.copy(reasons = current.reasons + "kept_by_hysteresis")
        } else {
            best
        }
    }

    fun rank(
        variants: List<ChapterVariant>,
        context: SourceRankingContext,
    ): List<RankedChapterVariant> {
        val normalizedPreferences = context.preferredLanguages.map(::normalizeLanguage)
        val usable = variants.mapNotNull { chapterVariant ->
            val source = chapterVariant.sourceVariant
            if (!source.health.isUsable(context.nowEpochMs)) return@mapNotNull null

            val normalizedLanguage = normalizeLanguage(source.language)
            val languageTier = normalizedPreferences.indexOf(normalizedLanguage)
                .takeIf { it >= 0 }
                ?: UNKNOWN_LANGUAGE_TIER

            val (score, reasons) = score(source, context.nowEpochMs)
            RankedChapterVariant(
                variant = chapterVariant,
                languageTier = languageTier,
                score = score,
                reasons = reasons,
            )
        }

        if (usable.isEmpty()) return emptyList()
        val bestTier = usable.minOf { it.languageTier }
        return usable
            .filter { it.languageTier == bestTier }
            .sortedWith(
                compareByDescending<RankedChapterVariant> { it.score }
                    .thenByDescending { it.variant.sourceVariant.totalChapters }
                    .thenByDescending { it.variant.sourceVariant.highestChapterNumber ?: Double.NEGATIVE_INFINITY }
                    .thenBy { it.variant.sourceVariant.id },
            )
    }

    private fun score(source: SourceVariant, nowEpochMs: Long): Pair<Double, List<String>> {
        val reasons = mutableListOf<String>()
        var score = when (source.health.state) {
            SourceHealthState.HEALTHY -> 1000.0.also { reasons += "health:healthy" }
            SourceHealthState.DEGRADED -> 700.0.also { reasons += "health:degraded" }
            SourceHealthState.RATE_LIMITED -> 550.0.also { reasons += "health:rate_limit_cooldown_expired" }
            else -> Double.NEGATIVE_INFINITY
        }

        val successBonus = source.health.successRate * 250.0
        score += successBonus
        reasons += "success_rate:+${successBonus.toInt()}"

        val coverageBonus = min(source.totalChapters.coerceAtLeast(0), 500) * 0.40
        score += coverageBonus
        reasons += "coverage:+${coverageBonus.toInt()}"

        val highChapterBonus = min((source.highestChapterNumber ?: 0.0).coerceAtLeast(0.0), 500.0) * 0.20
        score += highChapterBonus
        reasons += "highest_chapter:+${highChapterBonus.toInt()}"

        val freshnessBonus = freshnessBonus(source.lastUpdatedEpochMs, nowEpochMs)
        score += freshnessBonus
        reasons += "freshness:+${freshnessBonus.toInt()}"

        val latencyPenalty = min(source.health.averageLatencyMs / 20.0, 150.0)
        score -= latencyPenalty
        reasons += "latency:-${latencyPenalty.toInt()}"

        val failurePenalty = source.health.consecutiveFailures * 50.0
        score -= failurePenalty
        reasons += "failures:-${failurePenalty.toInt()}"

        return score to reasons
    }

    private fun freshnessBonus(lastUpdatedEpochMs: Long?, nowEpochMs: Long): Double {
        if (lastUpdatedEpochMs == null) return 0.0
        val ageMs = (nowEpochMs - lastUpdatedEpochMs).coerceAtLeast(0L)
        val ageDays = ageMs / DAY_MS
        return when {
            ageDays == 0L -> 100.0
            ageDays <= 1L -> 90.0
            ageDays <= 7L -> 60.0
            ageDays <= 30L -> 30.0
            else -> 0.0
        }
    }

    private fun normalizeLanguage(language: String): String = when (language.trim().lowercase()) {
        "pt-br", "pt_br", "ptbr", "br" -> "pt-br"
        "pt", "pt-pt", "pt_pt" -> "pt"
        "en", "en-us", "en_us", "en-gb", "en_gb" -> "en"
        "ja", "jp", "jpn" -> "ja"
        "ko", "kr", "kor" -> "ko"
        "zh", "zh-cn", "zh_cn", "zh-tw", "zh_tw", "cn" -> "zh"
        else -> language.trim().lowercase()
    }

    companion object {
        private const val UNKNOWN_LANGUAGE_TIER = 10_000
        private const val DAY_MS = 86_400_000L
    }
}
