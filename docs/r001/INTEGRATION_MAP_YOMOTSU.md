# Polaris R001 — Integration Map for Yomotsu

Pinned Yomotsu baseline:
`0fb80c439ef816eeb50674f1b90af39918b176d8`

This document is the practical map for Work/Codex. Pure domain behavior is already staged/tested in the Polaris spikes. The remaining work is to wire those decisions into the real Android app.

## 1. Multi-source persistence — first gate

Apply Spike-001 to the full Yomotsu checkout.

Primary files:
- `app/src/main/java/eu/kanade/domain/DomainModule.kt`
- `domain/src/main/java/tachiyomi/domain/manga/interactor/GetMangaWithChapters.kt`
- `app/src/main/java/eu/kanade/tachiyomi/source/AndroidSourceManager.kt`
- `app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaScreen.kt`
- new SQLDelight/domain/data files staged under `spikes/spike001/new-files/`

Do not proceed to canonical persistence until:
- SQLDelight generates;
- Gradle compiles;
- a virtual work aggregates two real manga rows;
- tapping a child chapter opens its real source.

## 2. Reader routing

Important baseline behavior already verified in Yomotsu:

`MangaScreen.openChapter(context, chapter, source)` launches:
`ReaderActivity.newIntent(context, chapter.mangaId, chapter.id)`.

Therefore Polaris should keep each selected chapter as the REAL child `Chapter` row.

Do not clone chapter rows into the virtual parent.
Do not rewrite child `manga_id`.

The canonical layer groups references; the Reader continues to receive a real child manga/chapter pair.

## 3. Global discovery

Reuse:
`app/src/main/java/eu/kanade/tachiyomi/ui/browse/source/globalsearch/SearchViewModel.kt`

Yomotsu already:
- enumerates enabled non-novel sources;
- honors enabled languages/disabled sources;
- calls sources concurrently with a 5-thread dispatcher;
- stores `SearchItemResult` by Source.

Polaris addition:
1. convert successful source results to `WorkCandidate`;
2. pass them to Spike-008 `SearchResultClusterer`;
3. render clusters as one canonical work candidate;
4. retain source-specific members behind an advanced “variants” view;
5. pass REVIEW pairs to semantic matcher;
6. after aliases are learned, use Spike-009 `AliasSearchPlanner` for a second targeted discovery pass.

Do NOT create a second networking/search engine.

## 4. Work matching

Local matching:
- Spike-003 `AutomaticWorkMatcher`.

Escalation:
- shared tracker/external IDs -> auto;
- exact alias/title -> auto;
- translated title with structural metadata support -> semantic review;
- conflicting same-namespace external IDs -> never auto-merge.

Persist confirmed aliases/external IDs in Spike-010 schema.

## 5. Chapter canonicalization

Replace Spike-001’s temporary numeric dedupe over time with:
- Spike-004 `ChapterLabelParser`;
- `ChapterNumberAlignment`;
- `CanonicalChapterResolver`.

Integration flow:
1. load child chapters from all source variants;
2. detect trusted source-number offsets;
3. convert each real chapter to canonical key;
4. persist `polaris_canonical_chapters` + `polaris_chapter_variants`;
5. never create fake reader chapters;
6. display one canonical chapter row;
7. choose one real child ChapterVariant at open time.

Specials/prologues/seasons stay conservative. Ambiguous entries remain separate.

## 6. Source health

Use Spike-005 `SourceHealthTracker`.

Good observation points:

### Global search
Around:
`source.getSearchManga(1, query, source.getFilterList())`

Record:
- success + elapsed latency;
- network/timeout/HTTP failures;
- auth/challenge/rate-limit when detectable.

### Manga/chapter refresh
At calls into:
`Source.getMangaUpdate(...)`

Record:
- success latency;
- parse/contract failures;
- source removed/unreachable status.

### Reader/page loading
Do NOT count every cancelled prefetch as a failure.
Only record genuine request failures that indicate source health.

Persist source-level health in `polaris_source_health`.

Source health is source-wide by default. If evidence later shows one title-specific failure, add variant health as a separate layer rather than poisoning the whole source.

## 7. Chapter opening

Before opening a canonical chapter:
1. load all mapped real child ChapterVariants;
2. join SourceHealth;
3. build Spike-002 `SourceVariant`/ChapterVariant inputs;
4. call Spike-007 `ChapterOpenPlanner`;
5. obtain one real child chapter;
6. update `last_variant_chapter_id`;
7. launch the existing ReaderActivity with that child `mangaId/chapterId`.

If no usable variant:
- show a diagnostic state;
- surface AUTH_REQUIRED / AUTH_EXPIRED / CHALLENGED action if applicable;
- offer manual “view variants” rather than silently failing.

## 8. Authentication / challenge state

No automated bypass.

When health says:
- AUTH_REQUIRED
- AUTH_EXPIRED
- CHALLENGED

UI action:
“Entrar / Desbloquear fonte”

Open the existing extension/webview authentication route when available.

After user interaction:
- re-run a light source request;
- on success, SourceHealthTracker restores usability;
- rerun ChapterOpenPlanner.

## 9. Translation integration

Reuse Yomotsu:
- `TranslationManager`
- `ChapterTranslator`
- `TranslationCache`
- `TranslationMemory`
- `TranslationGlossary`
- OCR engines
- LLM providers/fallbacks
- inpainting/typesetting.

Do not build another translator.

Use Spike-006 `TranslationDecisionPolicy`.

Required Yomotsu adaptation:

### 9.1 New request origin
Extend `TranslationRequestOrigin` with something like:
`POLARIS_READER`

It should be allowed to start when automatic canonical translation is enabled.

### 9.2 Canonical translation context
Current Yomotsu scopes glossary/cache/memory by manga title.

Polaris MUST pass a stable canonical title/key for:
`ComicTranslationContext`

Otherwise:
- “The Beginning After the End”
- “O Começo Depois do Fim”
- another source alias

would create separate memory/glossary scopes.

Recommended API change:
`TranslationManager.translateChapter(..., translationContextTitle: String? = null)`

Then:
`ChapterTranslator.queueChapter(..., translationContextTitle)`

The real child `Manga` is still retained for files/source/download access, but `ComicTranslationContext.mangaTitle` receives canonical title when supplied.

Long term, prefer a stable canonical key in storage rather than display title, but title-based compatibility can be preserved initially.

### 9.3 Open behavior
Planner result:
- READ_ORIGINAL -> launch child chapter directly.
- READ_TRANSLATED_CACHE -> launch and render existing translated pages.
- QUEUE_TRANSLATION -> queue Yomotsu translation for the real child chapter with canonical context, then open/refresh according to existing translation UX.
- READ_FOREIGN_UNTRANSLATED -> open original with a visible diagnostic/action.

## 10. Canonical progress

Use Spike-010 semantics.

Canonical:
- read/unread;
- bookmark;
- last chapter;
- selected variant.

Real child chapter:
- page-level last_page_read.

Do not map page index across different sources.

If a partially-read source becomes unavailable:
- pick a new source;
- safest fallback is page 0 for that chapter until image/page matching exists.

## 11. Existing Yomotsu features to preserve

Do not regress:
- source extensions;
- downloads;
- trackers;
- backup;
- translation UI;
- novel reader;
- global search;
- migration;
- reader pager/webtoon;
- local source.

Polaris should add orchestration above these systems, not replace them.

## 12. Recommended implementation sequence in Work/Codex

1. Apply Spike-001 and make Android build green.
2. Runtime proof: virtual work + two real sources.
3. Add Spike-010 SQLDelight schema/migration 15.
4. Add repositories/mappers for Polaris schema.
5. Integrate chapter canonicalizer.
6. Integrate SourceHealthTracker.
7. Integrate ChapterOpenPlanner.
8. Integrate search clustering.
9. Add semantic matcher provider.
10. Add canonical translation context.
11. Run full R001 acceptance matrix.
12. Only after PASS, redesign search/library UI around canonical works.
