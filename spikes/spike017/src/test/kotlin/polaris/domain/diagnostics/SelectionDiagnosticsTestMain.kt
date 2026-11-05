package polaris.domain.diagnostics

fun main() {
    val trace = ChapterSelectionTrace(
        canonicalWorkId = "tbate",
        canonicalChapterKey = "84",
        selectedSourceVariantId = "en-a",
        translationRequired = true,
        candidates = listOf(
            CandidateDecisionTrace("pt-a", "PT A", "pt-BR", 84.0, CandidateEligibility.CHALLENGED),
            CandidateDecisionTrace("en-a", "EN A", "en", 84.0, CandidateEligibility.ELIGIBLE, 2, 1210.0, selected = true),
            CandidateDecisionTrace("en-b", "EN B", "en", 84.0, CandidateEligibility.ELIGIBLE, 2, 1180.0),
        ),
    )
    val summary = trace.humanSummary()
    check("EN A" in summary)
    check("tradução necessária" in summary)
    check("1 alternativa" in summary)
    check("1 candidata" in summary)

    val none = ChapterSelectionTrace("x", "10", null, false, emptyList())
    check(none.humanSummary().startsWith("Nenhuma fonte"))

    println("SPIKE017_SELECTION_DIAGNOSTICS_TESTS_PASS")
}
