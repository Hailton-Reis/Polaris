package tachiyomi.domain.manga.interactor

import tachiyomi.domain.manga.model.MergeMangaSettingsUpdate
import tachiyomi.domain.manga.repository.MangaMergeRepository

class UpdateMergedSettings(
    private val repository: MangaMergeRepository,
) {
    suspend fun await(update: MergeMangaSettingsUpdate): Boolean = repository.updateSettings(update)
    suspend fun awaitAll(values: List<MergeMangaSettingsUpdate>): Boolean = repository.updateAllSettings(values)
}
