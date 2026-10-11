package tachiyomi.domain.chapter.interactor

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import tachiyomi.domain.chapter.model.Chapter
import tachiyomi.domain.chapter.repository.ChapterRepository
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

class GetMergedChaptersByMangaId(
    private val chapterRepository: ChapterRepository,
    private val mergeRepository: MangaMergeRepository,
) {
    suspend fun await(
        mangaId: Long,
        dedupe: Boolean = true,
        applyScanlatorFilter: Boolean = false,
    ): List<Chapter> {
        val references = validReferences(mangaId, mergeRepository.getReferencesById(mangaId))
        val chapters = childReferences(references)
            .flatMap { ref -> chapterRepository.getChapterByMangaId(requireNotNull(ref.mangaId), applyScanlatorFilter) }
        return transform(references, chapters, dedupe)
    }

    @OptIn(ExperimentalCoroutinesApi::class)
    fun subscribe(
        mangaId: Long,
        dedupe: Boolean = true,
        applyScanlatorFilter: Boolean = false,
    ): Flow<List<Chapter>> = mergeRepository.subscribeReferencesById(mangaId)
        .flatMapLatest { rawReferences ->
            val references = validReferences(mangaId, rawReferences)
            val refs = childReferences(references)
            if (refs.isEmpty()) {
                flowOf(emptyList())
            } else {
                val flows = refs.map { ref ->
                    chapterRepository.getChapterByMangaIdAsFlow(requireNotNull(ref.mangaId), applyScanlatorFilter)
                }
                combine(flows) { lists ->
                    transform(references, lists.flatMap { it }, dedupe)
                }
            }
        }

    /** Ignore duplicate, stale and cross-work edges without changing stored data. */
    private fun validReferences(mangaId: Long, references: List<MergedMangaReference>): List<MergedMangaReference> {
        val children = references.asSequence()
            .filter {
                it.mergeId == mangaId && it.mangaId != null &&
                    it.mangaId != mangaId && it.mangaSourceId != MERGED_SOURCE_ID
            }
            // A corrupt/retried link must not yield duplicate reader chapters.
            .distinctBy { it.mangaId }
            .toList()
        val root = references.firstOrNull {
            it.mergeId == mangaId && it.mangaId == mangaId && it.mangaSourceId == MERGED_SOURCE_ID
        }
        return children + listOfNotNull(root)
    }

    private fun childReferences(references: List<MergedMangaReference>) =
        references.filter { it.mangaSourceId != MERGED_SOURCE_ID }

    private fun transform(
        references: List<MergedMangaReference>,
        chapters: List<Chapter>,
        dedupe: Boolean,
    ): List<Chapter> {
        if (!dedupe) return chapters
        return when (rootSettings(references)?.chapterSortMode) {
            MergedMangaReference.CHAPTER_SORT_NO_DEDUPE,
            MergedMangaReference.CHAPTER_SORT_NONE,
            null,
            -> chapters

            MergedMangaReference.CHAPTER_SORT_PRIORITY -> dedupeByPriority(references, chapters)
            MergedMangaReference.CHAPTER_SORT_MOST_CHAPTERS -> {
                val mangaId = chapters.groupBy { it.mangaId }.maxByOrNull { it.value.size }?.key
                mangaId?.let { id -> chapters.filter { it.mangaId == id } } ?: chapters
            }
            MergedMangaReference.CHAPTER_SORT_HIGHEST_CHAPTER_NUMBER -> {
                val mangaId = chapters.maxByOrNull { it.chapterNumber }?.mangaId
                mangaId?.let { id -> chapters.filter { it.mangaId == id } } ?: chapters
            }
            else -> chapters
        }
    }

    private fun rootSettings(references: List<MergedMangaReference>) =
        references.firstOrNull { it.mangaSourceId == MERGED_SOURCE_ID }

    private fun dedupeByPriority(
        references: List<MergedMangaReference>,
        chapters: List<Chapter>,
    ): List<Chapter> {
        val out = mutableListOf<Chapter>()
        val priority = references.associate { it.mangaId to it.chapterPriority }
        // Track the winning original manga for each chapter number in O(n).
        // Duplicate numbers within the same source remain visible, as before.
        val numberOwner = mutableMapOf<Double, Long>()

        chapters.groupBy { it.mangaId }
            .entries
            .sortedBy { (mangaId) -> priority[mangaId] ?: Int.MAX_VALUE }
            .forEach { (_, sourceChapters) ->
                sourceChapters.forEach { chapter ->
                    if (!chapter.isRecognizedNumber) {
                        out += chapter
                    } else {
                        // Normalize signed zero: -0.0 == +0.0 in the old
                        // equality check, while boxed Double map keys differ.
                        val number = if (chapter.chapterNumber == 0.0) 0.0 else chapter.chapterNumber
                        val owner = numberOwner[number]
                        if (owner == null || owner == chapter.mangaId) {
                            out += chapter
                            numberOwner.putIfAbsent(number, chapter.mangaId)
                        }
                    }
                }
            }

        return out.mapIndexed { index, chapter -> chapter.copy(sourceOrder = index.toLong()) }
    }
}
