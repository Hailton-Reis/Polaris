package polaris.domain.semantic

import polaris.domain.matching.WorkCandidate

object SemanticWorkMatchPrompt {
    fun systemPrompt(): String = """
        You compare comic/novel work metadata to decide whether two source entries represent the same underlying work.

        Return a compact JSON object only with keys:
        sameWork, confidence, canonicalTitle, aliases, reasonCode.

        Rules:
        - Titles may be translations, transliterations, abbreviations, or alternate titles.
        - Use author, artist, chapter structure, descriptions, genres, and external IDs as supporting evidence.
        - Never invent an external ID.
        - Similar genres or chapter counts alone are not enough.
        - Prefer false over an unsafe merge when evidence is weak.
        - Keep aliases limited to names supported by supplied metadata or clearly equivalent translations.
        - Do not add prose outside JSON.
    """.trimIndent()

    fun userPrompt(request: SemanticWorkMatchRequest): String = buildString {
        appendLine("LEFT")
        appendCandidate(request.left)
        appendLine()
        appendLine("RIGHT")
        appendCandidate(request.right)
        appendLine()
        appendLine("LOCAL_EVIDENCE")
        appendLine("score=" + request.localEvidence.evidence.score)
        appendLine("titleSimilarity=" + request.localEvidence.evidence.titleSimilarity)
        appendLine("authorMatch=" + request.localEvidence.evidence.authorMatch)
        appendLine("artistMatch=" + request.localEvidence.evidence.artistMatch)
        appendLine("chapterSimilarity=" + request.localEvidence.evidence.chapterSimilarity)
        appendLine("sharedExternalIds=" + request.localEvidence.evidence.sharedExternalIds)
        appendLine("conflictingExternalNamespaces=" + request.localEvidence.evidence.conflictingExternalNamespaces)
    }

    private fun StringBuilder.appendCandidate(candidate: WorkCandidate) {
        appendLine("language=" + candidate.language)
        appendLine("title=" + candidate.title)
        appendLine("aliases=" + candidate.aliases.sorted())
        appendLine("author=" + candidate.author.orEmpty())
        appendLine("artist=" + candidate.artist.orEmpty())
        appendLine("externalIds=" + candidate.externalIds)
        appendLine("genres=" + candidate.genres.sorted())
        appendLine("chapterCount=" + candidate.chapterNumbers.size)
        appendLine("chapterMin=" + (candidate.chapterNumbers.minOrNull() ?: ""))
        appendLine("chapterMax=" + (candidate.chapterNumbers.maxOrNull() ?: ""))
        candidate.description?.takeIf(String::isNotBlank)?.let {
            appendLine("description=" + it.take(MAX_DESCRIPTION_CHARS))
        }
    }

    private const val MAX_DESCRIPTION_CHARS = 1200
}
