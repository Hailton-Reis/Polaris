package tachiyomi.domain.manga.repository
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MangaUpdate
interface MangaRepository {
    suspend fun getMangaById(id: Long): Manga
    suspend fun update(update: MangaUpdate): Boolean
}
