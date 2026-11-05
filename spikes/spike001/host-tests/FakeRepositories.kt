package tachiyomi.domain.chapter.repository

import kotlinx.coroutines.flow.Flow
import tachiyomi.domain.chapter.model.Chapter

interface ChapterRepository {
  suspend fun getChapterByMangaId(id: Long, applyScanlatorFilter: Boolean = false): List<Chapter>
  suspend fun getChapterByMangaIdAsFlow(id: Long, applyScanlatorFilter: Boolean = false): Flow<List<Chapter>>
}
