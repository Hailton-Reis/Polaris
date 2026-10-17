package eu.kanade.tachiyomi.data.backup.models

data class BackupCategory(val order: Long = 0L)
data class BackupChapter(val url: String, val read: Boolean = false, val bookmark: Boolean = false, val lastPageRead: Long = 0)
data class BackupManga(val source: Long, val url: String, val chapters: List<BackupChapter> = emptyList())
