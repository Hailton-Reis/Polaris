package tachiyomi.domain.manga.interactor

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import tachiyomi.domain.chapter.interactor.GetMergedChaptersByMangaId
import tachiyomi.domain.chapter.model.Chapter
import tachiyomi.domain.chapter.repository.ChapterRepository
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.repository.MangaRepository
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

class GetMangaWithChapters(
    private val mangaRepository: MangaRepository,
    private val chapterRepository: ChapterRepository,
    private val getMergedChaptersByMangaId: GetMergedChaptersByMangaId,
) {
    suspend fun subscribe(id: Long, applyScanlatorFilter: Boolean = false): Flow<Pair<Manga, List<Chapter>>> {
        return mangaRepository.getMangaByIdAsFlow(id).flatMapLatest { manga ->
            val chapters = if (manga.source == MERGED_SOURCE_ID) {
                getMergedChaptersByMangaId.subscribe(id, applyScanlatorFilter = applyScanlatorFilter)
            } else {
                chapterRepository.getChapterByMangaIdAsFlow(id, applyScanlatorFilter)
            }
            chapters.map { manga to it }
        }
    }

    suspend fun awaitManga(id: Long): Manga = mangaRepository.getMangaById(id)

    suspend fun awaitChapters(id: Long, applyScanlatorFilter: Boolean = false): List<Chapter> {
        val manga = mangaRepository.getMangaById(id)
        return if (manga.source == MERGED_SOURCE_ID) {
            getMergedChaptersByMangaId.await(id, applyScanlatorFilter = applyScanlatorFilter)
        } else {
            chapterRepository.getChapterByMangaId(id, applyScanlatorFilter)
        }
    }
}
