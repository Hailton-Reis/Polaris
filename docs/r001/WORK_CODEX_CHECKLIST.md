# Polaris — Work/Codex practical checklist

This document intentionally contains the remaining heavy/practical work only.

## Checkout

- Clone `Hailton-Reis/Polaris`.
- Checkout `r001/multisource-foundation`.
- Read `docs/r001/START_HERE.md`.
- Obtain pinned Yomotsu commit:
  `0fb80c439ef816eeb50674f1b90af39918b176d8`.

Recommended working branch:
`r001/android-integration`

## Phase 1 — Build gate

- Build unmodified pinned Yomotsu first.
- Apply `spikes/spike001/apply_spike001.py`.
- Review diff against staged files.
- Generate SQLDelight.
- Run format/static/unit tests.
- Build debug APK.
- Resolve only real API/integration differences; do not redesign spike semantics.

## Phase 2 — Runtime merge proof

- Install at least two compatible source extensions.
- Add the same test work from two sources.
- Populate chapters.
- Invoke `CreateMergedManga`.
- Open merged work.
- Open child chapter from each source.
- Remove one child reference and re-open.
- Record build commands, logs and screenshots in PR #1 / issue #2.

Hard gate: do not integrate migration 15 until this passes.

## Phase 3 — Canonical persistence

- Apply/adapt Spike-010 migration 15.
- Implement SQLDelight repository/mappers.
- Generate immutable canonical UUID according to Spike-019.
- Map virtual work -> `polaris_works`.
- Map child mangas -> `polaris_source_variants`.
- Persist aliases/external IDs.
- Persist canonical chapter mappings.
- Apply Spike-016 progress semantics.
- Do not use tracker ID/title as stable work key.

## Phase 4 — Runtime orchestration

Port/adapt:
- spike002 SourceRanker;
- spike004 CanonicalChapterResolver;
- spike005 SourceHealthTracker;
- spike007 ChapterOpenPlanner;
- spike012 SourceAccessClassifier;
- spike013 LanguageRoutePlanner;
- spike017 SelectionDiagnostics.

Requirements:
- keep these framework-light;
- do not penalize cancelled prefetch;
- log selection traces in debug builds;
- real child mangaId/chapterId must reach existing reader.

## Phase 5 — Discovery

Reuse Yomotsu global-search networking.

Integrate:
- spike003 AutomaticWorkMatcher;
- spike008 SearchResultClusterer;
- spike009 AliasSearchPlanner;
- spike011 SemanticWorkMatcher.

Rules:
- conflicting trusted external IDs cannot be overridden by LLM;
- REVIEW never silently merges;
- persist learned/confirmed aliases.

## Phase 6 — Translation bridge

Do not create a new OCR/translation pipeline.

- add Polaris automatic origin to TranslationLaunchPolicy;
- implement Spike-014 `memoryScopeKey` compatibility;
- preserve real child Manga/Source for translation files/downloads;
- use canonical UUID scope for TranslationMemory/Cache/Glossary;
- prompt may show current preferred canonical title;
- connect ChapterOpenPlanner QUEUE_TRANSLATION to Yomotsu.
- Spike-015 content-addressed reuse is optional for R001; do not let it block runtime proof.

## Phase 7 — Backup compatibility

Spike-018 defines the contract.

For R001:
- normal Yomotsu backup must not crash with Polaris tables.

Full Polaris backup/restore may move to R002 if necessary.

Never serialize local DB IDs as portable Polaris identity.

## Phase 8 — Acceptance

Run `docs/r001/RUNTIME_ACCEPTANCE_TESTS.md`.

Mandatory evidence:
- two real sources;
- PT-BR redundancy;
- unhealthy-source fallback;
- EN fallback + Yomotsu translation;
- canonical progress after source switch;
- auth revalidation;
- matching conflicts;
- regression of ordinary Yomotsu manga/search/download/translation.

Do not merge Draft PR #1 until mandatory R001 PASS scenarios are green.

## Explicitly deferred

See `docs/R002_DEFERRED_BACKLOG.md`:
- cross-source page-hash cache integration;
- full Polaris backup/restore UX;
- page correspondence across source variants;
- optional personal accelerator server;
- advanced diagnostics UI;
- richer novels integration/optimization.
