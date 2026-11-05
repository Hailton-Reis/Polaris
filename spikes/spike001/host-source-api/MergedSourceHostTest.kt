package polaris.spike001.source.host

import eu.kanade.tachiyomi.source.MergedSource
import eu.kanade.tachiyomi.source.model.*
import kotlinx.coroutines.runBlocking
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

fun main() = runBlocking {
    var passed = 0
    suspend fun test(name: String, body: suspend () -> Unit) {
        body()
        passed++
        println("PASS virtual source: $name")
    }
    val source = MergedSource()
    test("pinned Source API implementation compiles and identity is canonical") {
        check(source.id == MERGED_SOURCE_ID)
        check(source.name == "Merged" && source.lang == "all" && !source.supportsLatest)
    }
    test("filter list defaults to independent values") {
        val first = source.getFilterList()
        check(first !== source.getFilterList())
    }
    val manga = SManga()
    val chapters = listOf(SChapter(), SChapter())
    test("getMangaUpdate returns existing identity when all flags false") {
        val update = source.getMangaUpdate(manga, chapters, false, false)
        check(update.manga === manga && update.chapters === chapters)
    }
    test("getMangaUpdate never queries network when flags true") {
        val update = source.getMangaUpdate(manga, chapters, true, true)
        check(update.manga === manga && update.chapters === chapters)
    }
    suspend fun unsupported(block: suspend () -> Unit): Boolean = try {
        block()
        false
    } catch (e: UnsupportedOperationException) {
        e.message == "MergedSource is a virtual identity source"
    }
    test("popular search cannot be used as a real extension") {
        check(unsupported { source.getPopularManga(1) })
    }
    test("latest updates cannot be used as a real extension") {
        check(unsupported { source.getLatestUpdates(1) })
    }
    test("search cannot be used as a real extension") {
        check(unsupported { source.getSearchManga(1, "x", FilterList()) })
    }
    test("page fetching cannot be used as a real extension") {
        check(unsupported { source.getPageList(SChapter()) })
    }
    println("MERGED_SOURCE_PINNED_SOURCE_API_PASS ($passed scenarios); NOT_ANDROID_RUNTIME")
}
