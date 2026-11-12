package polaris.domain.progress

fun main() {
    val start = CanonicalChapterProgress()
    val childA = ChildChapterProgress(101, read = false, bookmarked = false, lastPageRead = 17)
    val opened = CanonicalProgressPolicy.observeChild(start, childA, nowEpochMs = 1000)
    check(opened.lastVariantChapterId == 101L)
    check(!opened.read)

    val same = CanonicalProgressPolicy.resume(opened, childA)
    check(same.pageIndex == 17 && same.reason == "same_variant_resume")

    val childB = ChildChapterProgress(202, read = false, bookmarked = false, lastPageRead = 9)
    val switched = CanonicalProgressPolicy.resume(opened, childB)
    check(switched.pageIndex == 0)
    check(switched.reason == "variant_changed_do_not_copy_page_index")

    val completedA = childA.copy(read = true, lastPageRead = 30)
    val completed = CanonicalProgressPolicy.observeChild(opened, completedA, nowEpochMs = 2000)
    check(completed.read)
    check(completed.completedAtEpochMs == 2000L)

    val observedB = CanonicalProgressPolicy.observeChild(completed, childB, nowEpochMs = 3000)
    check(observedB.read)
    check(observedB.lastVariantChapterId == 202L)

    val readUpdates = CanonicalProgressPolicy.childReadUpdates(true, listOf(101, 202, 202))
    check(readUpdates == mapOf(101L to true, 202L to true))

    val bookmarkUpdates = CanonicalProgressPolicy.childBookmarkUpdates(true, listOf(101, 202))
    check(bookmarkUpdates.values.all { it })

    println("SPIKE016_CANONICAL_PROGRESS_TESTS_PASS")
}
