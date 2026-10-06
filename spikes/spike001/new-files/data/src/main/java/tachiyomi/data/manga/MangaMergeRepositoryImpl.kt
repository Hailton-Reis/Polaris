package tachiyomi.data.manga

import app.cash.sqldelight.async.coroutines.awaitAsList
import app.cash.sqldelight.async.coroutines.awaitAsOneOrNull
import kotlinx.coroutines.flow.Flow
import logcat.LogPriority
import tachiyomi.core.common.util.system.logcat
import tachiyomi.data.Database
import tachiyomi.data.subscribeToList
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MergeMangaSettingsUpdate
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaMergeRepository

class MangaMergeRepositoryImpl(
    private val database: Database,
) : MangaMergeRepository {

    override suspend fun getMergedMangaById(id: Long): List<Manga> =
        database.mergedQueries
            .selectMergedMangasById(id, MangaMapper::mapManga)
            .awaitAsList()

    override fun subscribeMergedMangaById(id: Long): Flow<List<Manga>> =
        database.mergedQueries
            .selectMergedMangasById(id, MangaMapper::mapManga)
            .subscribeToList()

    override suspend fun getReferencesById(id: Long): List<MergedMangaReference> =
        database.mergedQueries
            .selectByMergeId(id, MergedMangaMapper::map)
            .awaitAsList()

    override fun subscribeReferencesById(id: Long): Flow<List<MergedMangaReference>> =
        database.mergedQueries
            .selectByMergeId(id, MergedMangaMapper::map)
            .subscribeToList()

    override suspend fun updateSettings(update: MergeMangaSettingsUpdate): Boolean = try {
        partialUpdate(update)
        true
    } catch (e: Exception) {
        logcat(LogPriority.ERROR, e)
        false
    }

    override suspend fun updateAllSettings(values: List<MergeMangaSettingsUpdate>): Boolean = try {
        partialUpdate(*values.toTypedArray())
        true
    } catch (e: Exception) {
        logcat(LogPriority.ERROR, e)
        false
    }

    private suspend fun partialUpdate(vararg values: MergeMangaSettingsUpdate) {
        database.transaction {
            values.forEach { value ->
                database.mergedQueries.updateSettingsById(
                    id = value.id,
                    getChapterUpdates = value.getChapterUpdates,
                    downloadChapters = value.downloadChapters,
                    infoManga = value.isInfoManga,
                    chapterPriority = value.chapterPriority?.toLong(),
                    chapterSortMode = value.chapterSortMode?.toLong(),
                )
            }
        }
    }

    override suspend fun insert(reference: MergedMangaReference): Long? =
        database.mergedQueries
            .insertReturningId(
                infoManga = reference.isInfoManga,
                getChapterUpdates = reference.getChapterUpdates,
                chapterSortMode = reference.chapterSortMode.toLong(),
                chapterPriority = reference.chapterPriority.toLong(),
                downloadChapters = reference.downloadChapters,
                mergeId = requireNotNull(reference.mergeId),
                mergeUrl = reference.mergeUrl,
                mangaId = reference.mangaId,
                mangaUrl = reference.mangaUrl,
                mangaSource = reference.mangaSourceId,
            )
            .awaitAsOneOrNull()

    override suspend fun insertAll(references: List<MergedMangaReference>) {
        database.transaction {
            references.forEach { reference ->
                database.mergedQueries.insert(
                    infoManga = reference.isInfoManga,
                    getChapterUpdates = reference.getChapterUpdates,
                    chapterSortMode = reference.chapterSortMode.toLong(),
                    chapterPriority = reference.chapterPriority.toLong(),
                    downloadChapters = reference.downloadChapters,
                    mergeId = requireNotNull(reference.mergeId),
                    mergeUrl = reference.mergeUrl,
                    mangaId = reference.mangaId,
                    mangaUrl = reference.mangaUrl,
                    mangaSource = reference.mangaSourceId,
                )
            }
        }
    }

    override suspend fun deleteById(id: Long) {
        database.mergedQueries.deleteById(id)
    }

    override suspend fun deleteByMergeId(mergeId: Long) {
        database.mergedQueries.deleteByMergeId(mergeId)
    }
}
