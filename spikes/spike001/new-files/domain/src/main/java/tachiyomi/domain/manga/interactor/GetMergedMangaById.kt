package tachiyomi.domain.manga.interactor

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.repository.MangaMergeRepository
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

class GetMergedMangaById(
    private val repository: MangaMergeRepository,
) {
    suspend fun await(id: Long): List<Manga> =
        repository.getMergedMangaById(id).filterNot { it.source == MERGED_SOURCE_ID }

    fun subscribe(id: Long): Flow<List<Manga>> =
        repository.subscribeMergedMangaById(id).map { list ->
            list.filterNot { it.source == MERGED_SOURCE_ID }
        }
}
