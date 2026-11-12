package tachiyomi.domain.chapter.model

data class Chapter(val id: Long, val mangaId: Long, val chapterNumber: Double, val sourceOrder: Long = 0) {
  val isRecognizedNumber: Boolean get() = chapterNumber >= 0.0
}
