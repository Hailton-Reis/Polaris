package polaris.domain.matching

class AutomaticWorkMatcher(
    private val autoMatchThreshold: Double = 0.82,
    private val reviewThreshold: Double = 0.48,
) {
    fun compare(a: WorkCandidate, b: WorkCandidate): WorkMatchResult {
        val sharedIds = a.externalIds.mapNotNull { (namespace, id) ->
            b.externalIds[namespace]
                ?.takeIf { it == id }
                ?.let { namespace to id }
        }.toMap()

        val conflictingNamespaces = a.externalIds.keys
            .intersect(b.externalIds.keys)
            .filterTo(mutableSetOf()) { namespace ->
                a.externalIds[namespace] != b.externalIds[namespace]
            }

        val aTitles = (a.aliases + a.title).map(TitleNormalizer::normalize).filter(String::isNotBlank).toSet()
        val bTitles = (b.aliases + b.title).map(TitleNormalizer::normalize).filter(String::isNotBlank).toSet()
        val aliasExact = aTitles.any { it in bTitles }

        val titleSimilarity = (a.aliases + a.title).maxOfOrNull { left ->
            (b.aliases + b.title).maxOfOrNull { right ->
                TitleNormalizer.similarity(left, right)
            } ?: 0.0
        } ?: 0.0

        val authorMatch = normalizedEqual(a.author, b.author)
        val artistMatch = normalizedEqual(a.artist, b.artist)
        val genreSimilarity = TitleNormalizer.jaccard(
            a.genres.map(TitleNormalizer::normalize).filter(String::isNotBlank).toSet(),
            b.genres.map(TitleNormalizer::normalize).filter(String::isNotBlank).toSet(),
        )
        val descriptionSimilarity = TitleNormalizer.jaccard(
            a.description?.let(TitleNormalizer::tokens).orEmpty(),
            b.description?.let(TitleNormalizer::tokens).orEmpty(),
        )
        val chapterSimilarity = chapterOverlap(a.chapterNumbers, b.chapterNumbers)

        val reasons = mutableListOf<String>()
        var score = 0.0

        if (sharedIds.isNotEmpty()) {
            score += 0.92
            reasons += "shared_external_id"
        }
        if (aliasExact) {
            score += 0.82
            reasons += "exact_title_or_alias"
        } else {
            val titleContribution = titleSimilarity * 0.52
            score += titleContribution
            if (titleContribution > 0.0) reasons += "title_similarity"
        }

        if (authorMatch) {
            score += 0.13
            reasons += "author_match"
        }
        if (artistMatch) {
            score += 0.08
            reasons += "artist_match"
        }
        score += genreSimilarity * 0.07
        score += descriptionSimilarity * 0.10
        score += chapterSimilarity * 0.12

        if (conflictingNamespaces.isNotEmpty()) {
            score -= 0.75
            reasons += "external_id_conflict"
        }

        score = score.coerceIn(0.0, 1.0)

        val strongConflict = conflictingNamespaces.isNotEmpty() && sharedIds.isEmpty()
        val crossLanguage = TitleNormalizer.normalize(a.language) != TitleNormalizer.normalize(b.language)
        val structuralCrossLanguageCandidate =
            crossLanguage &&
                (authorMatch || artistMatch) &&
                chapterSimilarity >= 0.65

        if (structuralCrossLanguageCandidate) {
            reasons += "cross_language_structural_candidate"
        }

        val decision = when {
            strongConflict -> WorkMatchDecision.DIFFERENT
            sharedIds.isNotEmpty() -> WorkMatchDecision.AUTO_MATCH
            score >= autoMatchThreshold && (aliasExact || titleSimilarity >= 0.80) -> WorkMatchDecision.AUTO_MATCH
            score >= reviewThreshold || structuralCrossLanguageCandidate -> WorkMatchDecision.REVIEW
            else -> WorkMatchDecision.DIFFERENT
        }

        val metadataSupport =
            authorMatch ||
                artistMatch ||
                chapterSimilarity >= 0.45 ||
                genreSimilarity >= 0.45

        val shouldAskSemanticProvider =
            decision == WorkMatchDecision.REVIEW &&
                sharedIds.isEmpty() &&
                !strongConflict &&
                (crossLanguage || titleSimilarity < 0.72) &&
                metadataSupport

        return WorkMatchResult(
            decision = decision,
            evidence = WorkMatchEvidence(
                score = score,
                titleSimilarity = titleSimilarity,
                aliasExactMatch = aliasExact,
                sharedExternalIds = sharedIds,
                conflictingExternalNamespaces = conflictingNamespaces,
                authorMatch = authorMatch,
                artistMatch = artistMatch,
                genreSimilarity = genreSimilarity,
                descriptionSimilarity = descriptionSimilarity,
                chapterSimilarity = chapterSimilarity,
                reasons = reasons,
            ),
            shouldAskSemanticProvider = shouldAskSemanticProvider,
        )
    }

    private fun normalizedEqual(left: String?, right: String?): Boolean {
        if (left.isNullOrBlank() || right.isNullOrBlank()) return false
        return TitleNormalizer.normalize(left) == TitleNormalizer.normalize(right)
    }

    private fun chapterOverlap(left: Set<Double>, right: Set<Double>): Double {
        if (left.isEmpty() || right.isEmpty()) return 0.0
        val intersection = left.intersect(right).size
        val smaller = minOf(left.size, right.size)
        return if (smaller == 0) 0.0 else intersection.toDouble() / smaller
    }
}
