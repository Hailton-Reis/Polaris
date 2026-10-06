# Polaris — Work/Codex practical checklist

This is intentionally the remaining heavy/practical work.

## Checkout

- Clone `Hailton-Reis/Polaris`.
- Checkout `r001/multisource-foundation`.
- Obtain pinned Yomotsu commit:
  `0fb80c439ef816eeb50674f1b90af39918b176d8`.

Recommended working branch:
`r001/android-integration`

## Phase 1 — Build gate

- Create full Yomotsu working tree.
- Apply `spikes/spike001/apply_spike001.py`.
- Review diff against staged files.
- Generate SQLDelight.
- Run formatting/static checks.
- Run unit tests.
- Build debug APK.
- Fix only integration/API differences, preserving spike semantics.

## Phase 2 — Runtime merge proof

- Install at least two compatible source extensions.
- Add the same test work from two sources.
- Ensure chapters are populated.
- Invoke `CreateMergedManga`.
- Open merged work.
- Open child chapter from each source.
- Record logs/screenshots/results in PR.

## Phase 3 — Canonical persistence

Only after merge proof:
- apply/adapt Spike-010 migration 15;
- implement SQLDelight repository/mappers;
- map virtual merged work to `polaris_works`;
- map child manga rows to `polaris_source_variants`.

## Phase 4 — Runtime orchestration

Port pure domain code from:
- spike002 SourceRanker;
- spike003 AutomaticWorkMatcher;
- spike004 CanonicalChapterResolver;
- spike005 SourceHealthTracker;
- spike006 TranslationDecisionPolicy;
- spike007 ChapterOpenPlanner;
- spike008 SearchResultClusterer;
- spike009 AliasSearchPlanner.

Keep these classes framework-light where possible.

## Phase 5 — Translation bridge

- add Polaris automatic origin to Yomotsu TranslationLaunchPolicy;
- add canonical translation context parameter;
- preserve real child Manga for source/download access;
- use canonical work identity for TranslationMemory/Cache/Glossary context.

## Phase 6 — Acceptance

Run `docs/r001/RUNTIME_ACCEPTANCE_TESTS.md`.

Do not merge Draft PR #1 until the mandatory R001 PASS set is green.
