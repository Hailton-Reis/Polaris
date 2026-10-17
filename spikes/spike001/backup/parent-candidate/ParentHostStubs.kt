package eu.kanade.tachiyomi.data.backup.models
class BackupManga(
    val source: Long, val url: String, val title: String="", val notes: String="",
    val categories: List<Long> = emptyList(), val chapters: List<String> = emptyList(),
    val history: List<String> = emptyList(), val tracking: List<String> = emptyList(),
    val memo: ByteArray = byteArrayOf(),
)
