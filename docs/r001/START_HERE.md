# Polaris — R001 Handoff

Date: 2026-10-06

## Latest execution checkpoint

**First read `docs/r001/RESUME_2026_10_08.md`.** This documents the pinned baseline and patched APK build results, the partial emulator run, current B01/B02/B03 device blocker, and the test/debug-harness improvements made after the original 2026-10-06 handoff. The R000 Drive notes and older `STATUS.md` descriptions must not override newer verified evidence.

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
- CanonicalWork gets an immutable internal UUID; tracker IDs/titles never become its primary identity.
- Source selection happens per canonical chapter.
- PT-BR is preferred when usable.
- Same-language variants are ranked by health, coverage, freshness, success history and latency.
- Default route: target PT-BR -> PT -> EN -> original language -> optional extras.
- If a foreign variant wins, reuse Yomotsu translation.
- LLM/API calls may be frequent when useful.
- A personal server is optional acceleration only.
- Authentication/challenge resolution is user-interactive and valid sessions are reused.
- Canonical read/bookmark survives source switches; page index does not cross source variants blindly.

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
Polaris adds clustering, automatic/semantic work matching and alias second-pass discovery.

### Translation
Yomotsu already provides OCR, inpainting/typesetting, Gemini/OpenRouter/DeepL/Google/ML Kit, provider fallback, translation cache, memory, glossary and contextual chapter prompts.

Do not create another translator.

Polaris decides WHEN translation is needed. Real child manga/source remains translation-file/download identity; canonical work UUID becomes stable memory/glossary/cache intelligence scope.

### Progress
Canonical:
- read/unread;
- bookmark;
- canonical chapter identity.

Real child:
- page index and source-specific files.

Switching source variant never copies page index unless future page correspondence proves equivalence.

## Framework-independent spikes

- 001: staged Merged Manga/multi-source port.
- 002: CanonicalWork/SourceVariant/SourceHealth + SourceRanker.
- 003: AutomaticWorkMatcher.
- 004: CanonicalChapterResolver + number alignment.
- 005: SourceHealthTracker.
- 006: TranslationDecisionPolicy.
- 007: ChapterOpenPlanner.
- 008: SearchResultClusterer.
- 009: AliasSearchPlanner.
- 010: canonical SQLDelight schema/migration 15.
- 011: SemanticWorkMatcher LLM contract.
- 012: SourceAccessClassifier.
- 013: LanguageRoutePlanner.
- 014: stable canonical TranslationMemory/Cache/Glossary scope.
- 015: content-addressed translation artifact identity.
- 016: canonical progress policy.
- 017: explainable source-selection diagnostics.
- 018: provider-neutral backup/restore contract.
- 019: immutable canonical UUID identity policy.
- 020: manual work-link overrides.
- 021: integrated R001 domain scenario simulation.
- 022: source-variant refresh planner.
- 023: canonical metadata resolver with provenance.
- 024: canonical-work lifecycle/orphan preservation policy.

Spikes 002–024 are framework-independent/staged; executable pure-Kotlin coverage exists for the decision modules. See `docs/r001/STATUS.md`.

## Exact Work/Codex order

1. Issue #2: full pinned Yomotsu build + Spike-001 runtime proof.
2. Issue #3: canonical persistence/schema, UUID, chapter mapping, metadata and lifecycle.
3. Issue #5: source health/ranking/open planner + refresh/lifecycle/diagnostic traces.
4. Issue #4: search clustering + semantic matcher + aliases + manual link overrides.
5. Issue #6: stable canonical translation context bridge.
6. Issue #7: acceptance/regression matrix.

Do not apply canonical migration 15 before issue #2 passes.

## Practical references

- `docs/r001/INTEGRATION_BLUEPRINT.md`
- `docs/r001/INTEGRATION_MAP_YOMOTSU.md`
- `docs/r001/PERSISTENCE_SCHEMA_V1.md`
- `docs/r001/RUNTIME_ACCEPTANCE_TESTS.md`
- `docs/r001/WORK_CODEX_CHECKLIST.md`
- `docs/R002_DEFERRED_BACKLOG.md`
- `spikes/spike001/VALIDATION.md`
- `spikes/spike010/PROGRESS_SEMANTICS.md`

## Scope protection

Do not spend Work/Codex time redesigning already-tested domain behavior unless real Yomotsu/Android APIs demonstrate incompatibility.

The heavy environment should focus on:
- checkout and full upstream tree;
- Gradle/SQLDelight;
- adapters/repositories;
- Android UI integration;
- APK/runtime;
- real extensions/sources;
- device/emulator testing;
- logs and acceptance evidence.
