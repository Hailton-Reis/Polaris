#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

BASELINE = "0fb80c439ef816eeb50674f1b90af39918b176d8"
BUNDLE = Path(__file__).resolve().parent

def replace_once(path: Path, old: str, new: str):
    text = path.read_text()
    if old not in text:
        raise SystemExit(f"Baseline mismatch: expected block not found in {path}")
    if text.count(old) != 1:
        raise SystemExit(f"Unsafe patch: expected exactly one match in {path}, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1))

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_spike001.py /path/to/yomotsu")
    repo = Path(sys.argv[1]).resolve()
    if not (repo / "settings.gradle.kts").exists():
        raise SystemExit(f"Not a Yomotsu/Mihon repository: {repo}")

    src = BUNDLE / "new-files"
    for f in src.rglob("*"):
        if f.is_file():
            dest = repo / f.relative_to(src)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise SystemExit(f"Refusing to overwrite existing new-file target: {dest}")
            shutil.copy2(f, dest)

    target = repo / "domain/src/main/java/tachiyomi/domain/manga/interactor/GetMangaWithChapters.kt"
    shutil.copy2(BUNDLE / "REPLACEMENT_GetMangaWithChapters.kt", target)

    dm = repo / "app/src/main/java/eu/kanade/domain/DomainModule.kt"
    replace_once(dm, "import tachiyomi.data.manga.MangaRepositoryImpl\n",
        "import tachiyomi.data.manga.MangaRepositoryImpl\nimport tachiyomi.data.manga.MangaMergeRepositoryImpl\n")
    replace_once(dm, "import tachiyomi.domain.chapter.interactor.GetChapterByUrlAndMangaId\n",
        "import tachiyomi.domain.chapter.interactor.GetChapterByUrlAndMangaId\nimport tachiyomi.domain.chapter.interactor.GetMergedChaptersByMangaId\n")
    replace_once(dm, "import tachiyomi.domain.manga.interactor.FetchInterval\n",
        "import tachiyomi.domain.manga.interactor.CreateMergedManga\nimport tachiyomi.domain.manga.interactor.DeleteMergedManga\nimport tachiyomi.domain.manga.interactor.FetchInterval\n")
    replace_once(dm, "import tachiyomi.domain.manga.interactor.GetMangaWithChapters\n",
        "import tachiyomi.domain.manga.interactor.GetMangaWithChapters\nimport tachiyomi.domain.manga.interactor.GetMergedMangaById\nimport tachiyomi.domain.manga.interactor.GetMergedReferencesById\nimport tachiyomi.domain.manga.interactor.InsertMergedReference\n")
    replace_once(dm, "import tachiyomi.domain.manga.interactor.UpdateMangaNotes\n",
        "import tachiyomi.domain.manga.interactor.UpdateMangaNotes\nimport tachiyomi.domain.manga.interactor.UpdateMergedSettings\n")
    replace_once(dm, "import tachiyomi.domain.manga.repository.MangaRepository\n",
        "import tachiyomi.domain.manga.repository.MangaMergeRepository\nimport tachiyomi.domain.manga.repository.MangaRepository\n")

    replace_once(dm, "        addSingletonFactory<MangaRepository> { MangaRepositoryImpl(get()) }\n",
        "        addSingletonFactory<MangaRepository> { MangaRepositoryImpl(get()) }\n"
        "        addSingletonFactory<MangaMergeRepository> { MangaMergeRepositoryImpl(get()) }\n"
        "        addFactory { GetMergedReferencesById(get()) }\n"
        "        addFactory { GetMergedMangaById(get()) }\n"
        "        addFactory { InsertMergedReference(get()) }\n"
        "        addFactory { UpdateMergedSettings(get()) }\n"
        "        addFactory { DeleteMergedManga(get()) }\n"
        "        addFactory { GetMergedChaptersByMangaId(get(), get()) }\n"
        "        addFactory { CreateMergedManga(get(), get()) }\n")
    replace_once(dm, "        addFactory { GetMangaWithChapters(get(), get()) }\n",
        "        addFactory { GetMangaWithChapters(get(), get(), get()) }\n")

    sm = repo / "app/src/main/java/eu/kanade/tachiyomi/source/AndroidSourceManager.kt"
    replace_once(sm, "import tachiyomi.domain.source.model.StubSource\n",
        "import tachiyomi.domain.source.model.MERGED_SOURCE_ID\nimport tachiyomi.domain.source.model.StubSource\n")
    replace_once(sm,
        "                        eu.kanade.tachiyomi.source.TelegramSource.ID to eu.kanade.tachiyomi.source.TelegramSource(context),\n",
        "                        eu.kanade.tachiyomi.source.TelegramSource.ID to eu.kanade.tachiyomi.source.TelegramSource(context),\n"
        "                        MERGED_SOURCE_ID to MergedSource(),\n")

    ms = repo / "app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaScreen.kt"
    replace_once(ms, "import eu.kanade.tachiyomi.source.Source\n",
        "import eu.kanade.tachiyomi.source.MergedSource\nimport eu.kanade.tachiyomi.source.Source\n")
    replace_once(ms,
        "            onDownloadChapter = viewModel::runChapterDownloadActions.takeIf { !successState.source.isLocalOrStub() },\n",
        "            onDownloadChapter = viewModel::runChapterDownloadActions\n"
        "                .takeIf { !successState.source.isLocalOrStub() && successState.source !is MergedSource },\n")
    replace_once(ms,
        "            onTranslationChapter = viewModel::runChapterTranslationActions.takeIf { !isNovel },\n",
        "            onTranslationChapter = viewModel::runChapterTranslationActions\n"
        "                .takeIf { !isNovel && successState.source !is MergedSource },\n")
    replace_once(ms,
        "            onDownloadActionClicked = viewModel::runDownloadAction.takeIf { !successState.source.isLocalOrStub() },\n",
        "            onDownloadActionClicked = viewModel::runDownloadAction\n"
        "                .takeIf { !successState.source.isLocalOrStub() && successState.source !is MergedSource },\n")
    replace_once(ms,
        "                .takeIf { !isNovel && successState.hasDownloadedChaptersToTranslate },\n",
        "                .takeIf { !isNovel && successState.source !is MergedSource && successState.hasDownloadedChaptersToTranslate },\n")

    # Preserve each real child manga source when dispatching merged chapters,
    # including novel vs image readers. Ordinary manga keep existing behavior.
    replace_once(ms, "import eu.kanade.tachiyomi.source.Source\n", "import eu.kanade.tachiyomi.source.INovelSource\nimport eu.kanade.tachiyomi.source.Source\n")
    replace_once(ms, "import tachiyomi.domain.manga.model.Manga\n", "import tachiyomi.domain.manga.model.Manga\nimport tachiyomi.domain.manga.repository.MangaRepository\nimport tachiyomi.domain.source.service.SourceManager\nimport uy.kohesive.injekt.Injekt\nimport uy.kohesive.injekt.api.get\n")
    replace_once(ms, "            onChapterClicked = { openChapter(context, it, successState.source) },", "            onChapterClicked = { chapter -> scope.launch { openChapter(context, chapter, successState.source) } },")
    replace_once(ms, "            onContinueReading = { continueReading(context, viewModel.getNextUnreadChapter(), successState.source) },", "            onContinueReading = { scope.launch { continueReading(context, viewModel.getNextUnreadChapter(), successState.source) } },")
    replace_once(ms, "    private fun continueReading(context: Context, unreadChapter: Chapter?, source: Source?) {\n        if (unreadChapter != null) openChapter(context, unreadChapter, source)\n    }\n\n    private fun openChapter(context: Context, chapter: Chapter, source: Source?) {\n        if (source is eu.kanade.tachiyomi.source.INovelSource) {\n            context.startActivity(eu.kanade.tachiyomi.ui.reader.NovelReaderActivity.newIntent(context, chapter.mangaId, chapter.id))\n        } else {\n            context.startActivity(ReaderActivity.newIntent(context, chapter.mangaId, chapter.id))\n        }\n    }", "    private suspend fun continueReading(context: Context, unreadChapter: Chapter?, source: Source?) {\n        if (unreadChapter != null) openChapter(context, unreadChapter, source)\n    }\n\n    private suspend fun openChapter(context: Context, chapter: Chapter, source: Source?) {\n        // The chapter belongs to a REAL child manga. For a virtual parent,\n        // resolve the actual child source before choosing image vs novel reader.\n        val readerSource = if (source is MergedSource) {\n            try {\n                val realChild = withIOContext { Injekt.get<MangaRepository>().getMangaById(chapter.mangaId) }\n                Injekt.get<SourceManager>().get(realChild.source) ?: error("Source extension unavailable for real mangaId=${chapter.mangaId}")\n            } catch (error: kotlinx.coroutines.CancellationException) {\n                throw error\n            } catch (error: Exception) {\n                logcat(LogPriority.ERROR, error) { \"Cannot resolve merged chapter childId=${chapter.mangaId}\" }\n                context.toast(error.message ?: \"Chapter source unavailable\")\n                return\n            }\n        } else {\n            source\n        }\n        if (readerSource is INovelSource) {\n            context.startActivity(eu.kanade.tachiyomi.ui.reader.NovelReaderActivity.newIntent(context, chapter.mangaId, chapter.id))\n        } else {\n            context.startActivity(ReaderActivity.newIntent(context, chapter.mangaId, chapter.id))\n        }\n    }")

    vm = repo / "app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaViewModel.kt"
    replace_once(vm, "import eu.kanade.tachiyomi.source.Source\n", "import eu.kanade.tachiyomi.source.MergedSource\nimport eu.kanade.tachiyomi.source.Source\n")
    replace_once(vm, "import tachiyomi.domain.manga.interactor.GetMangaWithChapters\n", "import tachiyomi.domain.manga.interactor.GetMangaWithChapters\nimport tachiyomi.domain.manga.interactor.GetMergedReferencesById\n")
    replace_once(vm, "import tachiyomi.domain.manga.repository.MangaRepository\n", "import tachiyomi.domain.manga.refresh.MergedRefreshCoordinator\nimport tachiyomi.domain.manga.repository.MangaRepository\nimport tachiyomi.domain.source.model.MERGED_SOURCE_ID\n")
    replace_once(vm, "                val update = updateMangaFromRemote(\n                    source = state.source,\n                    manga = state.manga,\n                    fetchDetails = fetchDetails,\n                    fetchChapters = fetchChapters,\n                    manualFetch = manualFetch,\n                )\n                    .getOrThrow()\n\n                if (manualFetch) {\n                    downloadNewChapters(update.newChapters)\n                }", "                if (state.source is MergedSource) {\n                    // The virtual source is never refreshed over the network. Refresh\n                    // linked REAL child manga via Yomotsu's existing updater.\n                    val references = Injekt.get<GetMergedReferencesById>().await(state.manga.id)\n                    MergedRefreshCoordinator.refresh(\n                        mergedMangaId = state.manga.id,\n                        references = references,\n                        refreshChild = { childId ->\n                            val child = mangaRepository.getMangaById(childId)\n                            check(child.source != MERGED_SOURCE_ID) { \"Nested virtual source is not refreshable\" }\n                            updateMangaFromRemote(\n                                manga = child,\n                                fetchDetails = fetchDetails,\n                                fetchChapters = fetchChapters,\n                                manualFetch = manualFetch,\n                            ).getOrThrow()\n                        },\n                        onFailure = { childId, error ->\n                            logcat(LogPriority.ERROR, error) { \"Merged refresh failed for real mangaId=$childId\" }\n                        },\n                    )\n                    // Keep virtual library identity separate from real child download identity:\n                    // no automatic downloads are scheduled from this virtual screen.\n                } else {\n                    val update = updateMangaFromRemote(\n                        source = state.source,\n                        manga = state.manga,\n                        fetchDetails = fetchDetails,\n                        fetchChapters = fetchChapters,\n                        manualFetch = manualFetch,\n                    )\n                        .getOrThrow()\n    \n                    if (manualFetch) {\n                        downloadNewChapters(update.newChapters)\n                    }\n                }")

    print("Spike-001 applied successfully.")
    print(f"Expected upstream baseline: {BASELINE}")

if __name__ == "__main__":
    main()
