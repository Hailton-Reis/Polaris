package eu.kanade.tachiyomi.polaris

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import tachiyomi.domain.chapter.interactor.GetMergedChaptersByMangaId
import tachiyomi.domain.chapter.repository.ChapterRepository
import tachiyomi.domain.manga.interactor.CreateMergedManga
import tachiyomi.domain.manga.interactor.DeleteMergedManga
import tachiyomi.domain.manga.interactor.GetMergedReferencesById
import tachiyomi.domain.manga.interactor.UpdateMergedSettings
import tachiyomi.domain.manga.model.MergeMangaSettingsUpdate
import tachiyomi.domain.manga.model.MergedMangaReference
import tachiyomi.domain.manga.repository.MangaRepository
import tachiyomi.domain.source.model.MERGED_SOURCE_ID
import uy.kohesive.injekt.Injekt
import uy.kohesive.injekt.api.get

/** Issue #2 test hook. Included and exported only in the debug build. */
class Spike001DebugActivity : Activity() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val status = TextView(this).apply { text = "Running Spike-001 debug operation…" }
        setContentView(status)
        // Do not replay a mutating operation on a configuration/process recreation.
        if (savedInstanceState != null) {
            status.text = "Operation was already started. Inspect PolarisSpike001 logcat."
            return
        }
        scope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    val operation = requireNotNull(intent.getStringExtra("operation")) {
                        "Explicit operation extra required: inspect, create or remove"
                    }
                    when (operation) {
                        "inspect" -> inspect()
                        "create" -> create()
                        "remove" -> remove()
                        else -> error("Expected operation=inspect, create or remove")
                    }
                }
                val lines = result.lines()
                Log.i("PolarisSpike001", "BEGIN operation=${intent.getStringExtra("operation")} lines=${lines.size}")
                lines.forEachIndexed { index, line ->
                    // ADB logcat entries are size-limited; keep one row per entry.
                    Log.i("PolarisSpike001", "line=${index + 1}/${lines.size} $line")
                }
                Log.i("PolarisSpike001", "END operation=${intent.getStringExtra("operation")}")
                status.text = result + "\n\nDiagnostic result only. Actual reader behavior requires B01/B02/B03 evidence."
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                Log.e("PolarisSpike001", "Debug operation failed", error)
                status.text = "FAILED: ${error.message}"
            }
        }
    }

    /** Read-only convenience for collecting actual child IDs from real extensions.
     *  No URLs/titles are logged by default; optional title_filter limits results.
     */
    private suspend fun inspect(): String {
        val filter = intent.getStringExtra("title_filter")?.trim()?.takeIf { it.isNotEmpty() }
        val limit = intent.getIntExtra("limit", 50).coerceIn(1, 200)
        val candidates = Injekt.get<MangaRepository>().getFavorites()
            .asSequence()
            .filter { it.source != MERGED_SOURCE_ID }
            .filter { filter == null || it.title.contains(filter, ignoreCase = true) }
            .take(limit)
            .toList()
        val chapterRepo = Injekt.get<ChapterRepository>()
        val rows = mutableListOf<String>()
        for (manga in candidates) {
            val count = chapterRepo.getChapterByMangaId(manga.id).size
            rows += "childId=${manga.id} sourceId=${manga.source} chapters=$count"
        }
        return "INSPECT candidates=${rows.size} titleFilterUsed=${filter != null}\n" +
            rows.joinToString("\n")
    }

    private suspend fun create(): String {
        val ids = listOf(intent.getLongExtra("child_a", -1), intent.getLongExtra("child_b", -1))
        require(ids.all { it > 0 } && ids.distinct().size == 2) { "Supply two distinct positive child IDs" }
        val mangas = ids.map { Injekt.get<MangaRepository>().getMangaById(it) }
        require(mangas.all { it.source != MERGED_SOURCE_ID } && mangas.map { it.source }.distinct().size == 2) {
            "Children must belong to two different real sources"
        }
        val counts = ids.map { Injekt.get<ChapterRepository>().getChapterByMangaId(it).size }
        require(counts.all { it > 0 }) { "Populate chapters for both children before running this hook" }
        val merged = Injekt.get<CreateMergedManga>()(ids)
        val root = Injekt.get<GetMergedReferencesById>().await(merged.id).single { it.mangaSourceId == MERGED_SOURCE_ID }
        // Show both overlapping lists for routing proof without changing the domain default.
        check(Injekt.get<UpdateMergedSettings>().await(MergeMangaSettingsUpdate(root.id, chapterSortMode = MergedMangaReference.CHAPTER_SORT_NO_DEDUPE)))
        val chapters = Injekt.get<GetMergedChaptersByMangaId>().await(merged.id)
        check(ids.all { id -> chapters.any { it.mangaId == id } }) { "Merged list is missing a child" }
        return "CREATED mergeId=${merged.id} children=$ids sources=${mangas.map { it.source }} chapterCounts=$counts mergedCount=${chapters.size}"
    }

    private suspend fun remove(): String {
        val mergeId = intent.getLongExtra("merge_id", -1)
        val childId = intent.getLongExtra("child_id", -1)
        require(mergeId > 0 && childId > 0 && mergeId != childId)
        val refs = Injekt.get<GetMergedReferencesById>().await(mergeId)
        val children = refs.filter { it.mangaSourceId != MERGED_SOURCE_ID && it.mangaId != null }
        require(children.size >= 2) { "This gate removes one reference while preserving another" }
        val reference = children.single { it.mangaId == childId }
        Injekt.get<DeleteMergedManga>().deleteReference(reference.id)
        val parent = Injekt.get<MangaRepository>().getMangaById(mergeId)
        check(parent.source == MERGED_SOURCE_ID)
        val chapters = Injekt.get<GetMergedChaptersByMangaId>().await(mergeId)
        check(chapters.isNotEmpty() && chapters.none { it.mangaId == childId })
        return "REMOVED referenceId=${reference.id} childId=$childId mergeId=$mergeId remainingChildren=${chapters.map { it.mangaId }.distinct()}"
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}
