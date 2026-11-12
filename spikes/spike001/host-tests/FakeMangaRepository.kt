package tachiyomi.domain.manga.repository

import tachiyomi.domain.manga.model.Manga

interface MangaRepository {
  suspend fun getMangaById(id: Long): Manga
  suspend fun getMangaByUrlAndSourceId(url: String, source: Long): Manga?
  suspend fun insertNetworkManga(mangas: List<Manga>): List<Manga>
}
