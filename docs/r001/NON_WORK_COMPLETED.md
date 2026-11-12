# R001 — Framework-independent work completed

This file is a scope lock for Work/Codex.

Do not redesign these behaviors unless full Yomotsu/Android integration proves an incompatibility.

## Multi-source foundation
- Spike-001: staged Merged Manga port.
- Reader-routing finding: real child chapter mangaId naturally routes to its real source.

## Canonical source selection
- Spike-002: SourceRanker.
- Spike-005: SourceHealthTracker.
- Spike-007: ChapterOpenPlanner.
- Spike-012: SourceAccessClassifier.
- Spike-013: LanguageRoutePlanner.
- Spike-017: SelectionDiagnostics.
- Spike-022: VariantRefreshPlanner.
- Spike-024: CanonicalWorkLifecyclePolicy.

## Work identity/discovery
- Spike-003: AutomaticWorkMatcher.
- Spike-008: SearchResultClusterer.
- Spike-009: AliasSearchPlanner.
- Spike-011: SemanticWorkMatcher contract.
- Spike-019: immutable canonical UUID.
- Spike-020: manual FORCE_SAME/FORCE_DIFFERENT overrides.
- Spike-023: CanonicalMetadataResolver.

## Chapters/progress
- Spike-004: CanonicalChapterResolver and number alignment.
- Spike-016: canonical progress policy.

## Translation
- Spike-006: TranslationDecisionPolicy.
- Spike-014: stable canonical translation memory/cache/glossary scope.
- Spike-015: content-addressed reusable translation artifact identity.

## Persistence/portability
- Spike-010: canonical SQLDelight schema + staged migration 15.
- Spike-018: portable backup/restore contract.

## Integrated proof
- Spike-021: cross-spike R001 domain scenario simulation PASS.

## Heavy work left

Only the following categories require Work/Codex:
- full pinned Yomotsu checkout;
- Android/Gradle/SQLDelight generation;
- adapting staged code to real APIs;
- repositories/mappers wired into app DI;
- UI/navigation integration;
- actual extensions/network access;
- emulator/device/APK;
- runtime logs and acceptance evidence.

If a heavy integration conflict appears, adapt the boundary first. Change domain semantics only with a documented reason and regression test.
