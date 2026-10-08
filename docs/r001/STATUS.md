# R001 Status

Updated: 2026-10-08

## Repository

- Repository: Hailton-Reis/Polaris
- Branch: r001/multisource-foundation
- Draft PR: #1
- Practical Android work is tracked in issues #2–#7.

## PASS — architecture / framework-independent engineering

- Product architecture consolidated.
- Yomotsu selected as Android base candidate.
- Pinned Yomotsu/TachiyomiSY baselines recorded.
- TachiyomiSY Merged Manga mapped.
- Yomotsu global-search and translation integration points mapped.
- Runtime acceptance matrix written.
- Work/Codex integration checklist written.

### Spike-001 — multi-source staging
- static port prepared;
- applicator mechanically validated;
- domain/source Kotlin slice compiled;
- priority / most-chapters / highest-chapter / no-dedupe semantics tested.

### Spike-002 — SourceRanker
Validated:
- language tiers;
- PT-BR redundancy;
- coverage/freshness/latency/health scoring;
- auth/challenge/rate-limit eligibility;
- hysteresis against source flapping.

### Spike-003 — AutomaticWorkMatcher
Validated:
- shared external IDs;
- aliases;
- punctuation normalization;
- external-ID conflicts;
- translated titles with structural evidence escalate to semantic review.

### Spike-004 — CanonicalChapterResolver
Validated:
- decimal comma/dot;
- seasons;
- prologue separation;
- conservative extras;
- trusted number-offset detection.

### Spike-005 — SourceHealthTracker
Validated:
- success recovery;
- latency smoothing;
- timeout/network degradation;
- unreachable threshold;
- auth/challenge states;
- rate-limit cooldown;
- parser failure -> broken.

### Spike-006 — TranslationDecisionPolicy
Validated:
- target-language direct read;
- translated-cache hit;
- foreign chapter queues translation;
- provider-unavailable diagnostic;
- canonical translation context identity.

### Spike-007 — ChapterOpenPlanner
Validated:
- source selection + translation decision composition;
- PT-BR direct;
- challenged PT -> EN translate;
- cached EN translation;
- no usable source -> no plan.

### Spike-008 — SearchResultClusterer
Validated:
- AUTO_MATCH clusters;
- REVIEW remains separate and emits semantic-review pair;
- conflicts never silently merge.

### Spike-009 — AliasSearchPlanner
Validated:
- PT/EN language-specific second-pass queries;
- health filtering;
- canonical-title fallback.

### Spike-010 — canonical SQLDelight persistence
- schema designed;
- migration 15 staged;
- canonical progress semantics documented;
- NOT to be applied before Spike-001 Android runtime PASS.

### Spike-011 — SemanticWorkMatcher contract
- provider interface;
- structured prompt boundary;
- confidence policy;
- hard external-ID conflict cannot be overridden by LLM.

### Spike-012 — SourceAccessClassifier
- cancellation ignored;
- challenge/auth/rate-limit/5xx/parser/source-removed classification;
- ordinary content 404 does not poison whole-source health.

### Spike-013 — LanguageRoutePlanner
- target -> base language -> EN bridge -> original -> extras;
- normalized/deduplicated language route.

### Spike-014 — stable canonical translation scope
- separates friendly display title from stable TranslationMemory/Cache/Glossary identity;
- preserves old Yomotsu behavior by default;
- defines migration-compatible memoryScopeKey semantics.

### Spike-015 — content-addressed translation artifact key
Validated locally:
- same page bytes/configuration -> same reusable key independent of source URL;
- target language aliases normalize consistently;
- glossary/model/page changes invalidate the key.

### Spike-016 — canonical progress policy
Validated locally:
- chapter completion survives source switch;
- same child variant resumes page index;
- switching child source never copies page index blindly;
- canonical read/bookmark can mirror to linked child rows.

### Spike-017 — selection diagnostics
Validated:
- explain selected source, score/reasons and rejected alternatives;
- translation marker;
- explicit no-usable-source summary.

### Spike-018 — backup contract
Validated:
- portable canonical UUID/aliases/external IDs/source identities;
- local DB IDs excluded from portable identity;
- manual FORCE_SAME/FORCE_DIFFERENT overrides preserved.

### Spike-019 — canonical identity policy
Validated:
- immutable internal UUID;
- title/external-ID changes never rotate canonical identity;
- stable translation scope.

### Spike-020 — manual work-link overrides
Validated:
- symmetric pair identity;
- explicit user same/different decisions precede automatic/semantic matching;
- latest explicit override wins.

### Spike-021 — integrated R001 domain simulation
Validated:
- PT health/ranking -> EN fallback -> translation/cache -> canonical progress -> source recovery;
- result: SPIKE021_R001_SCENARIO_SIMULATION_PASS.

### Spike-022 — variant refresh planner
Validated:
- work-open/background/manual TTL behavior;
- selected-variant priority;
- challenge/auth/rate-limit/unreachable guards;
- bounded refresh concurrency.

### Spike-023 — canonical metadata resolver
Validated locally:
- PT-BR display metadata preferred when usable;
- stable current title avoids UI churn;
- user metadata overrides win;
- blocked preferred-language variant falls back cleanly;
- field provenance retained.

### Spike-024 — canonical work lifecycle
Validated locally:
- source loss never deletes canonical work identity/progress;
- zero usable variants -> DEGRADED;
- zero linked variants -> ORPHANED;
- aliases can trigger rediscovery and in-library orphan can request user attention.

## Integration design

Written and staged:
- docs/r001/INTEGRATION_BLUEPRINT.md
- docs/r001/INTEGRATION_MAP_YOMOTSU.md
- docs/r001/PERSISTENCE_SCHEMA_V1.md
- docs/r001/ACCEPTANCE_SCENARIOS.md
- docs/r001/RUNTIME_ACCEPTANCE_TESTS.md
- docs/r001/WORK_CODEX_CHECKLIST.md

Key integration choices already fixed:
- reuse Yomotsu SearchViewModel networking;
- do not redesign source-api;
- open selected real child manga/chapter in existing reader;
- keep translation storage source-specific while making memory/glossary context canonical;
- no personal server requirement;
- user handles login/challenge interactively;
- source health records actual access outcomes rather than aggressive background probing.

## CI

A JVM domain-lab and GitHub Actions workflow are staged using the Yomotsu toolchain family:
- Kotlin 2.4.10
- Gradle 9.6.1
- Java 21

The workflow/domain-lab now targets Spikes 002–009 and 011–024.

GitHub Actions jobs currently fail before any step is exposed (empty job step list). Treat this as repository/account runner infrastructure until a runner actually starts; it is not evidence of a Kotlin/domain failure.

Framework-independent modules were additionally compiled/tested locally where possible, including the integrated scenario and Spikes 023/024.

## Android issue #2 checkpoint — evidence from 2026-10-07 and improvements on 2026-10-08

- PASS: pinned Yomotsu original and patched Spike-001 Android APK builds, with real SQLDelight generation and migration 14 verification. Migration 15 remains unapplied.
- PASS: software Android 12/API31 x86_64 original Yomotsu onboarding launched. Patched ARM64 APK installed and MainActivity splash rendered; this is not a reader pass.
- The patched build reproduced the same 34 app unit failures seen in the unmodified baseline with the agent-preloaded setup; 58/58 domain unit tests passed. The full unit suite was not green.
- On 2026-10-08, added `compare_android_unit_tests.py` and eight offline comparison tests, then changed the CI build script to compare fresh baseline and patched JUnit outcomes. The Android CI job has not successfully executed this updated gate.
- Added a debug-only read-only `inspect` operation to list saved child IDs, source IDs and chapter counts via ADB for B01/B02 preparation. See `ISSUE002_DEVICE_RUNBOOK.md`. The modified APK has not yet been rebuilt/installed for this addition.
- GitHub Actions workflows currently report failures **before job steps start** (zero steps in inspected jobs); these failures do not verify Android/Kotlin defects. Do not infer the platform cause without evidence.
- BLOCKED: B01 merged list, B02 chapters opening from both real sources, and B03 preservation after removing one source. The last emulation attempt ended with execution transport disconnected; no runtime gate completion is claimed.

## PENDING — real Android runtime and higher-level integration

- Rebuild and install the latest debug hook including read-only `inspect`.
- Trust two real extensions, load and refresh two source-specific manga of the same work, and capture real IDs.
- Real merged/canonical work and B01/B02/B03 evidence through the reader.

- Reader routing across two real child sources.
- Apply/adapt migration 15.
- Implement repositories/mappers for Polaris canonical tables.
- Integrate search clustering and semantic LLM provider.
- Integrate SourceHealth instrumentation/persistence.
- Integrate ChapterOpenPlanner before reader launch.
- Bridge stable canonical translation scope into Yomotsu TranslationManager/ChapterTranslator/TranslationMemory/Cache.
- Execute full runtime acceptance matrix.

## Gate

Do not merge Draft PR #1 and do not mark R001 PASS until:
- issue #2 runtime multi-source proof passes;
- mandatory scenarios in docs/r001/RUNTIME_ACCEPTANCE_TESTS.md pass.

The framework-independent design should not be redesigned in Work/Codex unless a real Android/API incompatibility is demonstrated.
