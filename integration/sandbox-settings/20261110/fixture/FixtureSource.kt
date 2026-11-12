package polaris.sandbox.fixture

import android.os.Process
import uy.kohesive.injekt.api.get
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


class FixtureSelect : Filter.Select<String>("Order", arrayOf("First", "Last"))
class FixtureGenres : Filter.Group<Filter<*>>("Genres", listOf(object : Filter.TriState("Action") {}, object : Filter.CheckBox("Color") {}))
class FilteredSource : FixtureSource() {
    override val id = 735112L
    override fun getFilterList() = FilterList(Filter.Header("Filters"), object : Filter.Text("Author") {}, FixtureSelect(), FixtureGenres(), object : Filter.Sort("Sort", arrayOf("Name", "Date")) {})
    override suspend fun getSearchManga(page: Int, query: String, filters: FilterList): MangasPage {
        val author = (filters[1] as Filter.Text).state
        val order = (filters[2] as FixtureSelect).state
        val genres = (filters[3] as FixtureGenres).state
        val tri = (genres[0] as Filter.TriState).state
        val color = (genres[1] as Filter.CheckBox).state
        val sort = (filters[4] as Filter.Sort).state
        return MangasPage(listOf(SManga.create().also { it.url = "/filtered"; it.title = "$author|$order|$tri|$color|${sort?.index}|${sort?.ascending}" }), false)
    }
}

class ConfiguredSource : FixtureSource(), eu.kanade.tachiyomi.source.ConfigurableSource {
    override val id = 735111L
    private val prefs get() = getSourcePreferences()
    override val name = "Configured source"
    override fun getFilterList(): FilterList {
        val expanded = prefs.getString("mode", "normal") == "expanded"
        return FilterList(object : Filter.Select<String>("Mode", if (expanded) arrayOf("Any", "One", "Two") else arrayOf("Any", "One")) {})
    }
    override suspend fun getPopularManga(page: Int) = MangasPage(listOf(SManga.create().also {
        it.url = "/configured"
        val app = uy.kohesive.injekt.Injekt.get<android.app.Application>()
        val blocked = runCatching { app.getSharedPreferences("polaris-host-settings", 0).all }.isFailure
        it.title = "${prefs.getString("token", "unset")}|${prefs.getBoolean("enabled", true)}|${prefs.getInt("counter", 0)}|$blocked"
    }), false)
    override fun setupPreferenceScreen(screen: androidx.preference.PreferenceScreen) {
        val ctx = screen.context
        val category = androidx.preference.PreferenceCategory(ctx).apply { key = "category"; title = "Fixture settings" }
        screen.addPreference(category)
        category.addPreference(androidx.preference.SwitchPreferenceCompat(ctx).apply {
            key = "enabled"; title = "Enabled"; setDefaultValue(true)
            setOnPreferenceChangeListener { _, _ -> prefs.edit().putLong("callback_uid", Process.myUid().toLong()).commit(); true }
        })
        category.addPreference(androidx.preference.EditTextPreference(ctx).apply {
            key = "token"; title = "Token"; setDefaultValue("unset")
            setOnPreferenceChangeListener { _, value -> if (value == "reject") false else { prefs.edit().putLong("callback_uid", Process.myUid().toLong()).commit(); true } }
        })
        category.findPreference<androidx.preference.EditTextPreference>("token")!!.dependency = "enabled"
        category.addPreference(androidx.preference.EditTextPreference(ctx).apply {
            key = "counter"; title = "Custom integer"; isPersistent = false; text = prefs.getInt("counter", 0).toString()
            setOnPreferenceChangeListener { _, value ->
                val number = value.toString().toIntOrNull()
                if (number != null) prefs.edit().putInt("counter", number).putLong("callback_uid", Process.myUid().toLong()).commit()
                false
            }
        })
        category.addPreference(androidx.preference.ListPreference(ctx).apply {
            key = "mode"; title = "Mode"; entries = arrayOf("Normal", "Expanded"); entryValues = arrayOf("normal", "expanded"); setDefaultValue("normal")
        })
        category.addPreference(androidx.preference.MultiSelectListPreference(ctx).apply {
            key = "tags"; title = "Tags"; entries = arrayOf("A", "B"); entryValues = arrayOf("a", "b"); setDefaultValue(setOf("a"))
        })
        category.addPreference(androidx.preference.Preference(ctx).apply {
            key = "login"; title = "Custom login action"; setOnPreferenceClickListener { error("Source action must not execute in host") }
        })
    }
}
