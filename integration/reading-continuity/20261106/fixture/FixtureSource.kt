package polaris.sandbox.fixture

import android.os.Process
import eu.kanade.tachiyomi.network.GET
import eu.kanade.tachiyomi.source.model.*
import eu.kanade.tachiyomi.source.online.HttpSource
import java.io.File

open class FixtureSource : HttpSource() {
    override val id = 735110L
    override val baseUrl = "https://example.org"
    override val lang = "en"
    override val supportsLatest = true
    private val readDenied = runCatching { File("/data/user/0/app.mihon.tachiyomiat.dev/files/polaris-sandbox-canary").readText() }.isFailure
    private val writeDenied = runCatching { File("/data/user/0/app.mihon.tachiyomiat.dev/files/polaris-sandbox-canary").writeText("changed") }.isFailure
    override val name = "fixture uid=${Process.myUid()} protected=${readDenied && writeDenied} identityOwn=${android.os.Binder.getCallingUid() == Process.myUid()}"
    private fun work() = SManga.create().also { it.url = "/work"; it.title = "Fixture"; it.author = "Synthetic" }
    override suspend fun getPopularManga(page: Int) = MangasPage(listOf(work()), false)
    override suspend fun getLatestUpdates(page: Int) = getPopularManga(page)
    override suspend fun getSearchManga(page: Int, query: String, filters: FilterList): MangasPage {
        if (query == "blocked-private-network") network.client.newCall(GET("http://127.0.0.1/")).execute().close()
        return getPopularManga(page)
    }
    override suspend fun getMangaUpdate(manga: SManga, chapters: List<SChapter>, fetchDetails: Boolean, fetchChapters: Boolean) =
        SMangaUpdate(work(), (1..2).map { n -> SChapter.create().also {
            it.url = "/chapter/$n"; it.name = "Chapter $n uid=${Process.myUid()}"; it.chapter_number = n.toFloat()
        } })
    override suspend fun getPageList(chapter: SChapter) = listOf(Page(0, "/page", "https://example.org/image.png"))
}
class InfiniteSource : FixtureSource() {
    init { while (true) Thread.sleep(100) }
}
