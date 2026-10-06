# Polaris — R001 Handoff

Date: 2026-10-06

## Start here

Repository:
`Hailton-Reis/Polaris`

Engineering branch:
`r001/multisource-foundation`

Draft PR:
`#1 — R001: multi-source foundation spikes`

Heavy Android work is decomposed into issues:
- #2 real Yomotsu/Spike-001 runtime build;
- #3 canonical persistence/chapter mapping;
- #4 discovery + aliases + semantic matching;
- #5 source health/ranking/open planner;
- #6 canonical translation bridge;
- #7 full runtime acceptance/regression.

## Product direction frozen for R001

- Work-first, not source-first.
- A canonical work owns multiple source variants.
- Source selection happens per canonical chapter.
- PT-BR is preferred when usable.
- Same-language variants are ranked by health, coverage, freshness, success history and latency.
- Default language route: target PT-BR -> PT -> EN -> original language -> optional extras.
- If a foreign variant wins, Yomotsu translation is reused.
- LLM/API calls may be frequent when useful.
- A personal server is optional acceleration only.
- Authentication/challenge resolution is user-interactive and valid sessions are reused.

## Pinned baselines

Yomotsu:
- repo: kiritsuguxs/yomotsu
- branch: main
- commit: 0fb80c439ef816eeb50674f1b90af39918b176d8

TachiyomiSY reference:
- repo: jobobby04/TachiyomiSY
- branch: master
- commit: 14648c7cf0aa84e5a35d48de9dbf1386df6cca42

## Critical findings already established

### Reader routing
Yomotsu opens ReaderActivity with `chapter.mangaId`.
A canonical/virtual list can therefore display real child chapters and the existing reader naturally uses the child's real source.

Do not clone child chapters into the virtual parent.

### Search
Yomotsu Global Search already searches enabled sources concurrently with a fixed pool of 5.

Do not create another source-search engine.
Polaris adds:
- result clustering;
- automatic/semantic work matching;
- alias second pass.

### Translation
Yomotsu already provides:
- OCR;
- inpainting/typesetting;
- Gemini/OpenRouter/DeepL/Google/ML Kit;
- provider fallback;
- translation cache;
- translation memory;
- glossary;
- contextual sequential-chapter prompt.

Do not create another translator.

Polaris must only decide WHEN translation is needed and ensure translation memory/glossary/cache use a canonical-work context rather than a source-specific title.

## Framework-independent spikes

- Spike-001: staged Merged Manga/multi-source port.
- Spike-002: CanonicalWork/SourceVariant/SourceHealth + SourceRanker.
- Spike-003: AutomaticWorkMatcher.
- Spike-004: CanonicalChapterResolver + number alignment.
- Spike-005: SourceHealthTracker.
- Spike-006: TranslationDecisionPolicy.
- Spike-007: ChapterOpenPlanner.
- Spike-008: SearchResultClusterer.
- Spike-009: AliasSearchPlanner.
- Spike-010: canonical SQLDelight schema/migration 15.
- Spike-011: SemanticWorkMatcher provider contract/prompt.
- Spike-012: SourceAccessClassifier.
- Spike-013: LanguageRoutePlanner.

See `docs/r001/STATUS.md` for validation status.

## Exact Work/Codex order

1. Issue #2: full pinned Yomotsu build + Spike-001 runtime proof.
2. Issue #3: canonical persistence/schema and chapter mapping.
3. Issue #5: source health/ranking/open planner.
4. Issue #4: search clustering + semantic matcher + aliases.
5. Issue #6: canonical translation context bridge.
6. Issue #7: run acceptance/regression matrix.

The order of #4/#5 may be swapped after #3, but do not integrate canonical schema before issue #2 passes.

## Practical references

- `docs/r001/INTEGRATION_MAP_YOMOTSU.md`
- `docs/r001/RUNTIME_ACCEPTANCE_TESTS.md`
- `docs/r001/WORK_CODEX_CHECKLIST.md`
- `spikes/spike001/VALIDATION.md`
- `spikes/spike010/PROGRESS_SEMANTICS.md`

## Scope protection

Do not spend Work/Codex time redesigning domain behavior that is already captured by spikes unless the real Yomotsu/Android APIs prove it incompatible.

The heavy environment should focus on:
- checkout;
- Gradle/SQLDelight;
- adapters;
- repositories;
- Android UI integration;
- APK/runtime;
- real sources;
- device/emulator testing.
