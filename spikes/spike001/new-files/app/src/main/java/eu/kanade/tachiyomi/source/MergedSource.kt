package eu.kanade.tachiyomi.source

import eu.kanade.tachiyomi.source.model.FilterList
import eu.kanade.tachiyomi.source.model.MangasPage
import eu.kanade.tachiyomi.source.model.Page
import eu.kanade.tachiyomi.source.model.SChapter
import eu.kanade.tachiyomi.source.model.SManga
import eu.kanade.tachiyomi.source.model.SMangaUpdate
import tachiyomi.domain.source.model.MERGED_SOURCE_ID

/**
 * Virtual source used only as the identity of a merged work.
 * Real chapters retain their original mangaId/source and are opened by those real sources.
 */
class MergedSource : Source {
    override val id = MERGED_SOURCE_ID
    override val name = "Merged"
    override val lang = "all"
    override val supportsLatest = false

    override suspend fun getPopularManga(page: Int): MangasPage = unsupported()
    override suspend fun getLatestUpdates(page: Int): MangasPage = unsupported()
    override suspend fun getSearchManga(page: Int, query: String, filters: FilterList): MangasPage = unsupported()

    override suspend fun getMangaUpdate(
        manga: SManga,
        chapters: List<SChapter>,
        fetchDetails: Boolean,
        fetchChapters: Boolean,
    ): SMangaUpdate = SMangaUpdate(manga, chapters)

    override suspend fun getPageList(chapter: SChapter): List<Page> = unsupported()

    private fun <T> unsupported(): T =
        throw UnsupportedOperationException("MergedSource is a virtual identity source")
}
