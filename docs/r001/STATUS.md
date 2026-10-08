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
- On 2026-10-08, hardened `compare_android_unit_tests.py` to require baseline/patched app+domain JUnit coverage and distinguish unit-test failures from Gradle infrastructure/build failures; added `capture_issue002_device_evidence.py` for read-only B01/B02/B03 ADB snapshots. The two Python test files passed 22 local tests (16 comparator + 6 capture), but the Android CI job has not successfully executed this updated gate.
- Added a debug-only read-only `inspect` operation to list saved child IDs, source IDs and chapter counts via ADB for B01/B02 preparation; hardened it to require an explicit operation and split diagnostic logs per row. See `ISSUE002_DEVICE_RUNBOOK.md`. The modified APK has not yet been rebuilt/installed for this addition.
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

## Follow-up safeguards (post-checkpoint)

- Protected the exported debug-only hook with Android's `android.permission.DUMP`; authorized ADB shell launch must be tested in runtime.
- 26 offline Python tests PASS locally: comparator 16, ADB evidence tool 6, debug hook installer 4.
- The latest code and security change still need the full pinned Yomotsu Android build and B01/B02/B03 runtime evidence. Issue #2 remains open and migration 15 is not applied.


## Actual staged Kotlin host runtime test (2026-10-08)

- 8/8 additional host-only Kotlin tests PASS using `scripts/r001/test_spike001_host.sh` (JDK21/kotlinc1.9/coroutines), compiling the staged real Spike-001 aggregation interactor and reference/virtual-ID models, not rewritten domain logic.
- Demonstrates source-specific child `mangaId` preservation, chapter list aggregation, priority selection, live Flow update on reference removal, and orphan-reference tolerance. Does not demonstrate Yomotsu Android ReaderActivity, pages, extensions or device acceptance.


## Extended domain proof and CI hook

- 12/12 host Kotlin scenarios PASS locally, using real staged Spike-001 Kotlin interactor/models with fake repository boundaries.
- Host Gradle lab added under `spikes/spike001/host-lab` and connected to `domain-spikes.yml`. Runner execution unverified: GitHub Actions jobs examined still fail at runner allocation with no steps.
- Android build latest revision and B01/B02/B03 still unverified. No migration 15.

## Virtual-work refresh integration (2026-10-08)

- Added real-source refresh delegation to Yomotsu's patched `MangaViewModel` for virtual merged works; previously its refresh incorrectly targeted the virtual no-network MergedSource. New resolver `MergedRefreshTargets` prevents orphan/cross-merge/root IDs.
- Full existing Yomotsu refresh remains for ordinary manga. Source-specific chapters and fetches retain the real child manga IDs.
- Kotlin host invariant tests 16/16 PASS; offline Python tests 33/33 PASS, **49 local validations**, not Android acceptance.
- Pre/post applicator VM compatibility checks added to the issue #2 build gate. Anchors verified against exact pinned Yomotsu source in read-only mode. Full patched Android build and real B04 verification still pending.


## Additional refresh isolation verification — 2026-10-08

- Real staged `MergedRefreshCoordinator` added, replacing the one-off error-handling loop in the Yomotsu ViewModel patch. It preserves per-child source identity, tolerates a single failed source, propagates cancellation and fails when every source fails.
- 22 Kotlin/JVM domain scenarios PASS locally (including 6 new coordinator cases). 36 Python offline integration/tooling cases PASS locally (including 3 coordinator patch-check tests). Total 58 offline cases.
- Pinned Yomotsu `MangaViewModel` anchor compatibility checked for four replacements. The new Android Kotlin code/Gradle build and B01/B02/B03/B04 on-device runtime acceptance remain **NOT VERIFIED**.


## October 8 verification expansion — lifecycle tested on host

- Full local Kotlin host suite **26/26 PASS**: includes 4 new actual staged `CreateMergedManga`/`DeleteMergedManga` lifecycle scenarios, preserving parent/child source IDs and post-removal chapters. Production source Git SHA verified. These tests use fake repository contracts, not Android storage/network.
- Python offline-tool suite **36/36 PASS**, verified again. Total **62** successful local test cases.
- `scripts/r001/test_spike001_host.sh` and the isolated Gradle host project now include actual staged create/delete interactors. CI has not run the extended Gradle lab because no runner was assigned to recent Actions jobs.
- Runner diagnosis documented at `ACTIONS_RUNNER_TRIAGE_2026_10_08.md` with exact GitHub job metadata. Account-level cause cannot be inferred.
- Android B01/B02/B03/B04 and latest compiled APK remain **NOT VERIFIED**. Issue #2 open; PR #1 draft; migration 15 unapplied.
