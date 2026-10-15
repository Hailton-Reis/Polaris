package tachiyomi.domain.manga.model
import kotlinx.serialization.json.JsonObject
data class Manga(val id: Long, val source: Long, val memo: JsonObject = JsonObject())
data class MangaUpdate(val id: Long, val memo: JsonObject? = null)
