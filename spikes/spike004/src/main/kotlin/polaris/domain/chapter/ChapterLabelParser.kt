package polaris.domain.chapter

import java.text.Normalizer
import java.util.Locale

object ChapterLabelParser {
    private val seasonRegex = Regex("""(?:season|temporada|s)[\s._-]*(\d+)""", RegexOption.IGNORE_CASE)
    private val numberRegex = Regex(
        """(?:chapter|chap|ch|capitulo|capítulo|cap|episode|episodio|episódio|ep)[\s._:#-]*(\d+(?:[.,]\d+)?)""",
        RegexOption.IGNORE_CASE,
    )
    private val bareNumberRegex = Regex("""(?<!\d)(\d+(?:[.,]\d+)?)(?!\d)""")
    private val partRegex = Regex("""(?:part|parte)[\s._:#-]*(\d+)""", RegexOption.IGNORE_CASE)

    fun parse(chapter: SourceChapterCandidate): ParsedChapterIdentity {
        val normalized = normalize(chapter.name)
        val kind = when {
            containsWord(normalized, "prologue") || containsWord(normalized, "prologo") -> ChapterKind.PROLOGUE
            containsWord(normalized, "epilogue") || containsWord(normalized, "epilogo") -> ChapterKind.EPILOGUE
            containsWord(normalized, "extra") || containsWord(normalized, "omake") -> ChapterKind.EXTRA
            containsWord(normalized, "special") || containsWord(normalized, "especial") -> ChapterKind.SPECIAL
            else -> ChapterKind.REGULAR
        }

        val season = seasonRegex.find(normalized)?.groupValues?.getOrNull(1)?.toIntOrNull()
        val part = partRegex.find(normalized)?.groupValues?.getOrNull(1)?.toIntOrNull()
        val parsedNumber = numberRegex.find(normalized)
            ?.groupValues?.getOrNull(1)
            ?.replace(',', '.')
            ?.toDoubleOrNull()
            ?: bareNumberRegex.find(normalized)
                ?.groupValues?.getOrNull(1)
                ?.replace(',', '.')
                ?.toDoubleOrNull()

        val number = chapter.reportedNumber
            ?.takeIf { it.isFinite() && it >= 0.0 }
            ?: parsedNumber

        return ParsedChapterIdentity(
            season = season,
            number = number,
            part = part,
            kind = kind,
            normalizedTitle = normalized,
        )
    }

    fun normalize(value: String): String = Normalizer.normalize(value, Normalizer.Form.NFKD)
        .lowercase(Locale.ROOT)
        .replace(Regex("""\p{M}+"""), "")
        .replace(Regex("""[^\p{L}\p{N}.,]+"""), " ")
        .trim()
        .replace(Regex("""\s+"""), " ")

    private fun containsWord(text: String, word: String): Boolean =
        Regex("""(?:^|\s)${Regex.escape(word)}(?:\s|$)""").containsMatchIn(text)
}
