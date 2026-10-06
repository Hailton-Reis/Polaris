package tachiyomi.domain.manga.interactor

import tachiyomi.domain.manga.repository.MangaMergeRepository

class DeleteMergedManga(
    private val repository: MangaMergeRepository,
) {
    suspend fun deleteReference(id: Long) = repository.deleteById(id)
    suspend fun deleteMerge(mergeId: Long) = repository.deleteByMergeId(mergeId)
}
