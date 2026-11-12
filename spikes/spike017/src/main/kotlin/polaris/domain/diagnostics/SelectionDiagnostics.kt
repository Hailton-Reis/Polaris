package polaris.domain.diagnostics

enum class CandidateEligibility {
    ELIGIBLE,
    WRONG_CHAPTER,
    AUTH_REQUIRED,
    AUTH_EXPIRED,
    CHALLENGED,
    RATE_LIMITED,
    BROKEN,
    UNREACHABLE,
    LANGUAGE_NOT_PREFERRED,
}

data class CandidateDecisionTrace(
    val sourceVariantId: String,
    val sourceName: String? = null,
    val language: String,
    val chapterNumber: Double?,
    val eligibility: CandidateEligibility,
    val languageTier: Int? = null,
    val score: Double? = null,
    val scoreReasons: List<String> = emptyList(),
    val selected: Boolean = false,
)

data class ChapterSelectionTrace(
    val canonicalWorkId: String,
    val canonicalChapterKey: String,
    val selectedSourceVariantId: String?,
    val translationRequired: Boolean,
    val candidates: List<CandidateDecisionTrace>,
) {
    fun humanSummary(): String {
        val selected = candidates.firstOrNull { it.selected }
            ?: return "Nenhuma fonte utilizável para $canonicalChapterKey."
        val excluded = candidates.count { !it.selected && it.eligibility != CandidateEligibility.ELIGIBLE }
        val alternatives = candidates.count { !it.selected && it.eligibility == CandidateEligibility.ELIGIBLE }
        return buildString {
            append("Selecionada ")
            append(selected.sourceName ?: selected.sourceVariantId)
            append(" [${selected.language}]")
            selected.score?.let { append(" score=${"%.1f".format(java.util.Locale.US, it)}") }
            if (translationRequired) append("; tradução necessária")
            if (alternatives > 0) append("; $alternatives alternativa(s) utilizável(is)")
            if (excluded > 0) append("; $excluded candidata(s) indisponível(is)")
            append('.')
        }
    }
}
