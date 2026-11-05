package polaris.domain.progress

data class CanonicalChapterProgress(
    val read: Boolean = false,
    val bookmarked: Boolean = false,
    val lastVariantChapterId: Long? = null,
    val completedAtEpochMs: Long? = null,
)

data class ChildChapterProgress(
    val chapterId: Long,
    val read: Boolean,
    val bookmarked: Boolean,
    val lastPageRead: Int,
)

data class ResumeDecision(
    val chapterId: Long,
    val pageIndex: Int,
    val reason: String,
)

object CanonicalProgressPolicy {
    fun observeChild(
        current: CanonicalChapterProgress,
        child: ChildChapterProgress,
        nowEpochMs: Long,
    ): CanonicalChapterProgress {
        val becameRead = child.read && !current.read
        return current.copy(
            read = current.read || child.read,
            bookmarked = current.bookmarked || child.bookmarked,
            lastVariantChapterId = child.chapterId,
            completedAtEpochMs = when {
                becameRead -> nowEpochMs
                else -> current.completedAtEpochMs
            },
        )
    }

    fun resume(
        canonical: CanonicalChapterProgress,
        targetChild: ChildChapterProgress,
    ): ResumeDecision {
        return if (canonical.lastVariantChapterId == targetChild.chapterId) {
            ResumeDecision(
                chapterId = targetChild.chapterId,
                pageIndex = targetChild.lastPageRead.coerceAtLeast(0),
                reason = "same_variant_resume",
            )
        } else {
            ResumeDecision(
                chapterId = targetChild.chapterId,
                pageIndex = 0,
                reason = "variant_changed_do_not_copy_page_index",
            )
        }
    }

    fun childReadUpdates(read: Boolean, childChapterIds: Collection<Long>): Map<Long, Boolean> =
        childChapterIds.distinct().associateWith { read }

    fun childBookmarkUpdates(bookmarked: Boolean, childChapterIds: Collection<Long>): Map<Long, Boolean> =
        childChapterIds.distinct().associateWith { bookmarked }
}
