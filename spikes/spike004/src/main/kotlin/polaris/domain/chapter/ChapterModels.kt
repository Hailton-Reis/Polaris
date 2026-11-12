package polaris.domain.chapter

enum class ChapterKind {
    REGULAR,
    PROLOGUE,
    EPILOGUE,
    EXTRA,
    SPECIAL,
    UNKNOWN,
}

data class SourceChapterCandidate(
    val sourceVariantId: String,
    val chapterId: Long,
    val language: String,
    val name: String,
    val reportedNumber: Double? = null,
    val volume: Double? = null,
)

data class ParsedChapterIdentity(
    val season: Int?,
    val number: Double?,
    val part: Int?,
    val kind: ChapterKind,
    val normalizedTitle: String,
)

data class CanonicalChapterKey(
    val season: Int?,
    val number: Double?,
    val part: Int?,
    val kind: ChapterKind,
    val specialTitleKey: String?,
)

data class CanonicalChapterGroup(
    val key: CanonicalChapterKey,
    val variants: List<SourceChapterCandidate>,
)
