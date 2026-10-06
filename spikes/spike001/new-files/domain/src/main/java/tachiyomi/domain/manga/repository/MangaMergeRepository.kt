package tachiyomi.domain.manga.repository

import kotlinx.coroutines.flow.Flow
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MergeMangaSettingsUpdate
import tachiyomi.domain.manga.model.MergedMangaReference

interface MangaMergeRepository {
    suspend fun getMergedMangaById(id: Long): List<Manga>
    fun subscribeMergedMangaById(id: Long): Flow<List<Manga>>

    suspend fun getReferencesById(id: Long): List<MergedMangaReference>
    fun subscribeReferencesById(id: Long): Flow<List<MergedMangaReference>>

    suspend fun updateSettings(update: MergeMangaSettingsUpdate): Boolean
    suspend fun updateAllSettings(values: List<MergeMangaSettingsUpdate>): Boolean

    suspend fun insert(reference: MergedMangaReference): Long?
    suspend fun insertAll(references: List<MergedMangaReference>)

    suspend fun deleteById(id: Long)
    suspend fun deleteByMergeId(mergeId: Long)
}
