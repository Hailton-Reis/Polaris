# R001 Integration Blueprint — Yomotsu -> Polaris

Pinned Yomotsu baseline: `0fb80c439ef816eeb50674f1b90af39918b176d8`.

## Goal

Keep Yomotsu/Mihon behavior intact for normal source-specific manga while inserting Polaris only at four boundaries:

1. discovery/search;
2. canonical identity/persistence;
3. chapter-open selection;
4. translation context.

No source-api redesign is required.

## 1. Multi-source runtime

First integrate Spike-001 exactly as staged.

Primary Yomotsu touchpoints:
- `app/src/main/java/eu/kanade/domain/DomainModule.kt`
- `app/src/main/java/eu/kanade/tachiyomi/source/AndroidSourceManager.kt`
- `domain/src/main/java/tachiyomi/domain/manga/interactor/GetMangaWithChapters.kt`
- `app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaScreen.kt`

Important finding:
`MangaScreen.openChapter()` launches ReaderActivity with `chapter.mangaId`. A child chapter therefore opens through its real child manga/source. Do not port TachiyomiSY's invasive ReaderViewModel merged logic until a real runtime test proves it is needed.

## 2. Search/discovery

Reuse Yomotsu `SearchViewModel`.

Current behavior already provides:
- enabled source filtering;
- up to five source requests concurrently;
- `Source.getSearchManga()`;
- source-specific result maps.

Do not replace this search engine.

Add a Polaris coordinator after results arrive:
`SearchItemResult.Success -> WorkCandidate -> SearchResultClusterer`.

Pipeline:
1. user query runs through existing global search;
2. flatten source results into WorkCandidate records;
3. cluster confident aliases with Spike-003;
4. emit REVIEW pairs to semantic/LLM resolver;
5. persist confirmed work/source relationships;
6. Spike-009 schedules second-pass alias queries only for usable sources.

The existing source extension API remains unchanged.

## 3. Health

Instrument source access outcomes, do not continuously probe every source.

Useful event sites:
- global search request completion/error;
- chapter refresh/update;
- page-list/image loading failures;
- manual login/revalidation success;
- HTTP 429/retry-after.

Feed events to Spike-005 SourceHealthTracker and persist the record per SourceVariant.

A challenge/auth state is not a broken source. It is temporarily ineligible until user interaction + successful revalidation.

## 4. Chapter identity

After a merged/canonical work receives child chapter lists:
1. convert source chapters to SourceChapterCandidate;
2. run Spike-004 parser/resolver;
3. detect only high-confidence small source-number offsets;
4. persist canonical chapter + child chapter variants;
5. use SourceRanker inside each canonical chapter.

Never silently collapse ambiguous specials/prologues/season resets.

## 5. Open planning

Immediately before open:
`canonical chapter -> ChapterOpenPlanner -> selected real ChapterVariant`.

The selected child chapter retains its real `mangaId`.
Launch the existing Yomotsu reader with that child manga/chapter.

This preserves:
- source-specific page retrieval;
- cookies/session behavior;
- downloads;
- reader settings;
- extension compatibility.

## 6. Translation

Yomotsu translation should stay responsible for OCR, LLM/API translation, inpainting, typesetting, queue and cache files.

Polaris only controls WHEN and under WHICH CANONICAL CONTEXT it runs.

### Translation launch origin

Extend `TranslationRequestOrigin` with:
`POLARIS_AUTO_OPEN`.

Policy:
- USER_ACTION: always allowed;
- DOWNLOAD_COMPLETION: existing per-manga preference;
- POLARIS_AUTO_OPEN: allowed when the open plan requested translation and a provider is configured.

Do not make Polaris depend on a personal server.

### Canonical translation context

Today ChapterTranslator uses:
`ComicTranslationContext(translation.manga.title, translation.chapter.name)`.

Polaris needs:
`ComicTranslationContext(canonicalTitle, canonicalChapterLabel)`.

Storage path should remain source-specific:
`provider.getMangaDir(realManga.title, realSource)`.

This separation is intentional:
- translation files belong to the real source chapter;
- glossary/memory/context belong to the canonical work.

Recommended minimal implementation:
- add optional `contextTitle` and `contextChapterName` to queued Translation;
- `queueChapter(..., contextOverride = null)`;
- use override only when building ComicTranslationContext;
- continue using real manga/source for file lookup/storage.

Later, page-image content hashes can allow translation reuse across sources with identical bytes.

## 7. Glossary UI

For a canonical work, open TranslationGlossaryScreen with canonical title, not child-source title.

A source-specific manga that is not linked to Polaris keeps existing behavior unchanged.

## 8. App-first invariant

All of the above runs in-app.

External providers such as Gemini/OpenRouter/DeepL can be called directly by Yomotsu as they are today.

A personal backend remains an optional accelerator only.

## Integration order

1. Spike-001 full build/runtime.
2. Polaris persistence schema.
3. SourceHealth event recording.
4. Canonical chapter persistence.
5. ChapterOpenPlanner wiring.
6. Translation canonical-context override.
7. SearchResultClusterer.
8. AliasSearchPlanner.
9. LLM semantic resolver for REVIEW pairs.
10. UX simplification.

Do not invert this order: search intelligence is not useful until the open path is stable.
