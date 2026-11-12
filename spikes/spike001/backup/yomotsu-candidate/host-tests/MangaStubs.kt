package tachiyomi.domain.manga.model
import kotlinx.serialization.json.JsonObject
data class Manga(val id: Long, val source: Long, val url: String, val title: String, val favorite: Boolean, val memo: JsonObject = JsonObject())
data class MangaUpdate(val id: Long, val memo: JsonObject? = null)
data class MergedMangaReference(val mergeId: Long?, val mergeUrl: String, val mangaId: Long?, val mangaUrl: String, val mangaSourceId: Long, val isInfoManga: Boolean = false, val getChapterUpdates: Boolean = true, val chapterSortMode: Int = 2, val chapterPriority: Int = 0, val downloadChapters: Boolean = false)
