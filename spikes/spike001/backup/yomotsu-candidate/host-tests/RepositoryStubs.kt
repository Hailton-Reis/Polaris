package tachiyomi.domain.manga.repository
import tachiyomi.domain.manga.model.Manga
import tachiyomi.domain.manga.model.MangaUpdate
import tachiyomi.domain.manga.model.MergedMangaReference
interface MangaRepository { suspend fun getMangaById(id: Long): Manga; suspend fun update(update: MangaUpdate): Boolean }
interface MangaMergeRepository { suspend fun getReferencesById(id: Long): List<MergedMangaReference> }
