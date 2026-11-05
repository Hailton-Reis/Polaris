package tachiyomi.domain.manga.model

data class Manga(val id: Long, val source: Long, val url: String, val title: String, val favorite: Boolean = false, val initialized: Boolean = false)
