package tachiyomi.domain.manga.interactor

import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository

class InsertMergedReference(
    private val repository: MangaMergeRepository,
) {
    suspend fun await(reference: MergedMangaReference): Long? = repository.insert(reference)
    suspend fun awaitAll(references: List<MergedMangaReference>) = repository.insertAll(references)
}
