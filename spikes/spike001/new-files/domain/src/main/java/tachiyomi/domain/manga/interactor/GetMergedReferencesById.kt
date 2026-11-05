package tachiyomi.domain.manga.interactor

import kotlinx.coroutines.flow.Flow
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository

class GetMergedReferencesById(
    private val repository: MangaMergeRepository,
) {
    suspend fun await(id: Long): List<MergedMangaReference> = repository.getReferencesById(id)
    fun subscribe(id: Long): Flow<List<MergedMangaReference>> = repository.subscribeReferencesById(id)
}
