package tachiyomi.domain.manga.interactor

import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository
import tachiyomi.domain.manga.repository.MangaRepository
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

class CreateMergedManga(
    private val mangaRepository: MangaRepository,
    private val mergeRepository: MangaMergeRepository,
) {
    suspend operator fun invoke(
        childMangaIds: List<Long>,
        infoMangaId: Long = childMangaIds.first(),
    ): Manga {
        val ids = childMangaIds.distinct()
        require(ids.size >= 2) { "A merged manga requires at least two source variants" }
        require(infoMangaId in ids) { "infoMangaId must be one of the merged variants" }

        val children = ids.map { mangaRepository.getMangaById(it) }
        require(children.none { it.source == MERGED_SOURCE_ID }) { "Nested merged works are not supported" }
        require(children.map { it.source }.distinct().size >= 2) { "Merge requires variants from two real sources" }
        val info = children.first { it.id == infoMangaId }
        val mergeUrl = "merged://${ids.sorted().joinToString("-")}"

        val existing = mangaRepository.getMangaByUrlAndSourceId(mergeUrl, MERGED_SOURCE_ID)
        // A previous attempt may have inserted the virtual parent but failed
        // before insertAll persisted its references. Recover only that empty
        // state. A nonempty reference set can represent intentional removal
        // of one source; never silently restore those deleted references.
        if (existing != null && mergeRepository.getReferencesById(existing.id).isNotEmpty()) return existing

        val merged = existing ?: mangaRepository.insertNetworkManga(
            listOf(
                info.copy(
                    id = -1L,
                    source = MERGED_SOURCE_ID,
                    url = mergeUrl,
                    favorite = true,
                    initialized = true,
                ),
            ),
        ).single()

        val childReferences = children.mapIndexed { index, child ->
            MergedMangaReference(
                id = -1L,
                isInfoManga = child.id == infoMangaId,
                getChapterUpdates = true,
                chapterSortMode = MergedMangaReference.CHAPTER_SORT_PRIORITY,
                chapterPriority = index,
                downloadChapters = false,
                mergeId = merged.id,
                mergeUrl = merged.url,
                mangaId = child.id,
                mangaUrl = child.url,
                mangaSourceId = child.source,
            )
        }

        val rootReference = MergedMangaReference(
            id = -1L,
            isInfoManga = false,
            getChapterUpdates = false,
            chapterSortMode = MergedMangaReference.CHAPTER_SORT_PRIORITY,
            chapterPriority = Int.MAX_VALUE,
            downloadChapters = false,
            mergeId = merged.id,
            mergeUrl = merged.url,
            mangaId = merged.id,
            mangaUrl = merged.url,
            mangaSourceId = MERGED_SOURCE_ID,
        )

        mergeRepository.insertAll(childReferences + rootReference)
        return merged
    }
}
