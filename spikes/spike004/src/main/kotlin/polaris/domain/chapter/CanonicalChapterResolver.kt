package polaris.domain.chapter

class CanonicalChapterResolver {

    fun resolve(
        chapters: List<SourceChapterCandidate>,
        offsetBySourceVariant: Map<String, Double> = emptyMap(),
    ): List<CanonicalChapterGroup> {
        return chapters
            .groupBy { chapter -> canonicalKey(chapter, offsetBySourceVariant[chapter.sourceVariantId] ?: 0.0) }
            .map { (key, variants) ->
                CanonicalChapterGroup(
                    key = key,
                    variants = variants.sortedWith(compareBy({ it.language }, { it.sourceVariantId }, { it.chapterId })),
                )
            }
            .sortedWith(
                compareBy<CanonicalChapterGroup> { it.key.season ?: 0 }
                    .thenBy { kindOrder(it.key.kind) }
                    .thenBy { it.key.number ?: Double.NEGATIVE_INFINITY }
                    .thenBy { it.key.part ?: 0 }
                    .thenBy { it.key.specialTitleKey.orEmpty() },
            )
    }

    fun canonicalKey(chapter: SourceChapterCandidate, sourceOffset: Double = 0.0): CanonicalChapterKey {
        val parsed = ChapterLabelParser.parse(chapter)
        val alignedNumber = parsed.number?.let { normalizeNumber(it + sourceOffset) }

        val specialTitleKey = when (parsed.kind) {
            ChapterKind.REGULAR -> null
            else -> specialSemanticKey(parsed.normalizedTitle, alignedNumber)
        }

        return CanonicalChapterKey(
            season = parsed.season,
            number = alignedNumber,
            part = parsed.part,
            kind = parsed.kind,
            specialTitleKey = specialTitleKey,
        )
    }

    private fun specialSemanticKey(normalizedTitle: String, number: Double?): String {
        var value = normalizedTitle
            .replace(Regex("""\b(?:chapter|chap|ch|capitulo|cap|episode|episodio|ep)\b"""), " ")
            .replace(Regex("""\b\d+(?:[.,]\d+)?\b"""), " ")
            .replace(Regex("""\s+"""), " ")
            .trim()
        if (value.isBlank()) value = "special"
        return if (number == null) value else "$value#$number"
    }

    private fun normalizeNumber(value: Double): Double =
        kotlin.math.round(value * 1000.0) / 1000.0

    private fun kindOrder(kind: ChapterKind): Int = when (kind) {
        ChapterKind.PROLOGUE -> 0
        ChapterKind.REGULAR -> 1
        ChapterKind.EXTRA -> 2
        ChapterKind.SPECIAL -> 3
        ChapterKind.EPILOGUE -> 4
        ChapterKind.UNKNOWN -> 5
    }
}
