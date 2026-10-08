package tachiyomi.domain.manga.repository

import kotlinx.coroutines.flow.Flow
import tachiyomi.domain.manga.model.MergedMangaReference

interface MangaMergeRepository {
  suspend fun getReferencesById(id: Long): List<MergedMangaReference>
  fun subscribeReferencesById(id: Long): Flow<List<MergedMangaReference>>
}
