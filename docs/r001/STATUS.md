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

## Reader kind / virtual child routing

- Patched Yomotsu `MangaScreen` to dispatch virtual chapters using their actual child source, preserving novel-reader vs image-reader selection and original chapter ID pair; both chapter click and Continue Reading use a suspend-aware coroutine.
- Debug-only `route` operation verifies the chapter links to the merged parent and identifies installed source kind via ADB. It is a source classification diagnostic, **not** actual B02 acceptance.
- 10/10 pinned-upstream MangaScreen patch anchors verified exactly once. Eight new Python patch-check scenarios added; **new Android compilation and their full CI invocation remain pending**. Prior 26 Kotlin + 36 Python locally executed cases remain valid historical evidence, not Android PASS.
- Supplemental novel case B05 and commands in `ISSUE002_DEVICE_RUNBOOK.md`. No migration 15.


## Orphan virtual work repair (host-proven focused case, 2026-10-08)

- Failed initial write can leave a virtual parent without any `merged` reference rows; an ordinary retry previously returned that orphan. Reproduced failure with original `CreateMergedManga.kt` and an injected repository exception.
- Patched production interactor to recover **only fully empty** reference sets on retry; intentionally removed source references are never silently restored. One parent remains, two child references plus root are recreated.
- Verified production file Git blob matches locally compiled replacement `253f8ada08c55730b7138258745ce323d38f222d`; 3 focused JVM checks PASS. Extended host-test code to 28 scenarios, **full 28 not rerun yet**; last full run 26 Kotlin and 36 Python.
- SQLDelight/Android runtime (including B01–B05) remains pending, migration 15 unapplied and PR draft.


## New 2026-10-08 validation — SQLite contract and safe merge creation

- **10/10 actual migration-14/merged.sq SQLite tests PASS** with Git blob equality proven. New runnable test `spikes/spike001/host-sqlite/test_merged_sqlite_contract.py`; wired to domain-spikes CI and issue-002 Android build preflight.
- Production `CreateMergedManga.kt` now prohibits nested virtual child works and two variants from the same real source before side effects. **5/5 focused local Kotlin tests PASS** on byte-identical production source; existing orphan-repair semantics preserved.
- Main host Kotlin suite contains **30 committed test definitions** (previously 28); the entire 30-case suite has **not** run in this checkpoint. Previous complete recorded tests: 26/26 Kotlin + 36/36 Python. Do not conflate separate runs.
- Pinned Yomotsu uses **BundledSQLiteDriver**, so Android *framework* API31's older SQLite is not evidence of a `RETURNING` incompatibility. Driver configuration static preflight committed; Android runtime still needed.
- Separate whole-work deletion/virtual-parent leak tracked as [issue #8](https://github.com/Hailton-Reis/Polaris/issues/8), not silently fixed or waived. No migration 15.
- PR remains draft; issue #2 B01–B05 and current APK build not passed.

## Offline three-suite host gate (2026-10-08)

- Added `scripts/r001/run_host_gate.py` and `docs/r001/HOST_GATE_RUNBOOK.md`: strict host-only gate with minimum **54 Python / 10 SQLite / 30 Kotlin** results, three logs and JSON evidence; missing tests fail closed.
- Added 7 self-tests for the gate; **7/7 locally PASS**, tested files matched the GitHub blobs exactly. Verified that an intentionally partial local checkout yields SQLite **10/10 PASS** but overall `FAIL_OR_INCONCLUSIVE` with exit code 1 because full Python/Kotlin sources are absent.
- Rechecked production focused Kotlin **5/5** and SQL migration fixtures **10/10** in the current environment. The complete 30-case Kotlin and 54-case Python suites remain not executed here; do not call them PASS.
- Domain-spikes workflow now invokes the Python tooling tests in addition to existing host SQLite and Gradle checks. An authorized one-job rerun of GitHub Actions run 37838795183, attempt 2, still received no runner (`steps=[]`, `runner_id=0`).
- Android B01–B05 remain unverified and migration 15 blocked. Issue #2 open, PR #1 draft.

## 2026-10-09 — complete R001 host gate verified (SUPERSEDES previous host pending status)

- First full Kotlin host suite executed with exact staged files: **30/30 PASS**, compiled with JDK21/kotlinc1.9.
- First full Python tooling suite executed: the initial run exposed an actual Python SyntaxError in the applicator's MangaScreen patch. Fixed in commit 4d699352; reran **54/54 PASS**.
- SQLite migration 14 contracts **10/10 PASS**. Unified scripts/r001/run_host_gate.py executed all three together and reported **94/94 PASS**, exit 0, scope HOST_ONLY_NOT_ANDROID_RUNTIME.
- Verified **34 exact GitHub blobs** against the local test files. This was a reconstructed source subset, not a full cloned repo; report's repo_commit=null correctly signals that. See docs/r001/RESUME_2026_10_09.md and the Drive evidence ZIP.
- Android APK and B01–B05 device gates are **NOT VERIFIED**. GitHub Actions runner allocation remains unresolved; issue #2 open, PR #1 draft, migration 15 not applied. Issue #8 remains separate.


## 2026-10-09 addendum — expanded offline gate and worker safety

- Exact pinned Yomotsu `Source.kt` compiled against real staged `MergedSource.kt`: **8/8 host Kotlin API cases PASS** (with unrelated models and deprecated Rx stand-ins).
- Found and narrowly prevented direct background updates of virtual parent in `LibraryUpdateJob` and `MetadataUpdateJob`. Both pinned upstream file anchor checks PASS in original and patched states. Only real source manga continue through Yomotsu's normal automatic updater; virtual-only automatic child refresh awaits the planner of issue #5.
- Eight new Python regression tests for worker patch checking are included; unified offline host gate now **62 Python + 10 SQLite + 30 Kotlin = 102/102 PASS** (retested with committed source bytes). API's 8 cases are separate, not double-counted.
- Build script now fails closed on broken worker patch anchors in baseline and patched trees. No migration-15 changes or automatic Cloudflare handling.
- [Expanded verification ZIP in Polaris Drive](https://drive.google.com/file/d/1yDAoe_bGnd1pIu4iGo4YfEZ0L2U1xASL/view). No Android SDK/ADB/Gradle was available in this container; Android B01–B05 and APK remain unverified.

## 2026-10-11 — full Spike-001 patch application + 112-test host gate

- Applied the **actual** Spike-001 applicator end-to-end to seven hash-verified original pinned Yomotsu files: all **28 literal edits**, **18 added source/migration files** and the replaced GetMangaWithChapters implementation passed exact whole-file checks. Both existing pre/post patch guards passed.
- New `scripts/r001/check_spike001_full_apply.py` is fail-closed and runs inside `build_issue002.sh` **before** Gradle. Ten new negative/positive Python regression cases PASS.
- Re-executed unified offline gate: **72 Python + 10 SQLite + 30 Kotlin = 112/112 PASS**, exit 0, scope HOST_ONLY_NOT_ANDROID_RUNTIME. New files and altered gate files matched GitHub blob hashes; source subset is not a full Git clone.
- Evidence: https://drive.google.com/file/d/1pEwZyiiJeuh4vGXfAAyyEYLdBR5venmr/view ; SHA256 `cb73fca51f8c45cf77616304bc68500e5f7951ecda4691a0931da7016bb12702`.
- GitHub Actions issue-002 run 38144387274 and domain run 38144387272 still failed before runner assignment (zero steps, runner_id 0); no Android build/device proof. See docs/r001/RESUME_2026_10_11.md. Issue #2 open, PR #1 draft, migration 15 unchanged.

## 11/10/2026 — Auditoria técnica integrada e priorização de lacunas

- Novo relatório: `docs/r001/AUDIT_GAPS_2026_10_11.md`, com riscos confirmados vs hipóteses, prioridades P0/P1/P2 e sequência para uso real.
- **Issue #9 (contadores)**: SQLite/Yomotsu `libraryView` exibe 0 capítulos/lidos/marcados no parent virtual apesar de 4 capítulos nos filhos reais. **Reproduzido**.
- **Issue #10 (unicidade)**: migration14 aceita duas referências idênticas ao mesmo filho, provocando risco de capítulos duplicados/concorrência. **Reproduzido**.
- **Issue #11 (backup)**: Yomotsu backup/restore serializa mangás e seus capítulos mas não as referências da nova tabela `merged`; risco de perda de vínculos ao restaurar. Comprovado por auditoria de código; round-trip em dispositivo não testado.
- **Issue #8** (exclusão total) permanece; #3–#7 ainda abrangem persistência canônica, matching, saúde/ranking, tradução e aceitação integral.
- Corrigidos defensivamente a entrada vazia/IDs inválidos em `CreateMergedManga` e desempenho quadrático de `dedupeByPriority`, preservando semântica com novos testes: **34/34 Kotlin**, gate **116/116 offline** (72 Python + 10 SQLite + 34 Kotlin). Sem migração 15 nem alteração em SQL de produção.
- Script `spikes/spike001/audit/reproduce_known_gaps.py` (NÃO contar no gate) preserva diagnóstico reproduzível usando `libraryView.sq` pinned byte-idêntica ao Yomotsu.
- CI Android segue sem runner; a conclusão do APK e B01–B05 continuam bloqueadas. PR #1 draft, issue #2 aberta.

## 2026-10-11 — defensive chapter-link normalization (host red/green verified)

- Found, reproduced (original host test FAILED) and fixed a reader integration bug: duplicate `merged` rows gave duplicate chapters in non-deduped reading mode, while incorrect cross-work rows could override chapter-source priority. Reader now filters linked records for the selected parent, suppresses repeated child IDs, excludes parent-as-child and retains only the correct root settings in both `await` and `subscribe`.
- Four new Kotlin host scenarios PASS; 38/38 Kotlin, combined gate **120/120 PASS** (72 Python + 10 SQLite + 38 Kotlin). Code on GitHub matched tested Git blob hashes exactly.
- Proof ZIP saved in Polaris Drive: https://drive.google.com/file/d/1x4NA1OAadA23NaWQpYfVDy08zsLt_El9/view (SHA256 `2232a35ba0acdc32514bd8dedd465dd3938a8d6ae4b5da48c4fe40e047afd9c2`). Red test and green logs included.
- This guards reads only: migration 14 **still allows duplicate records**. #10 remains OPEN, along with #8, #9, #11. Android B01–B05 still required, issue #2 open, PR #1 draft and migration15 blocked.


## 2026-10-11 — idempotent source association writes (partial #10)

- Replayed original `merged.sq` inserts; new red tests exposed four violations of idempotency. Patched both `insert` and `insertReturningId` to atomically skip already-linked child IDs (or same source+URL for null/orphan rows) via SQLite `INSERT ... SELECT ... WHERE NOT EXISTS`. Existing settings, explicit unlinking and real child identity remain preserved.
- New ten-case SQLite test file includes four separate SQLite connections racing to insert the same child. Staged SQLite total **20/20 PASS**. Full gate **72 Python + 20 SQLite + 38 Kotlin = 130/130 PASS**, exit 0, offline only. Full patched Yomotsu subset application guard passed.
- Evidence ZIP: https://drive.google.com/file/d/1Ii4t2QUChADw6KjTIVG82dDbe1XMkIS3/view (SHA-256 `191258fdd1f1ab859ccfe754e4f8d0ea6a92688323c92c5f19b860b692b194be`). Three source Git blobs match local executed bytes exactly.
- **Issue #10 remains OPEN**: SQL table still lacks a UNIQUE constraint, existing duplicate rows aren't deleted; SQLDelight code generation/Android execution are unverified. No schema/migration changes or Android B01–B05 evidence.


## 2026-10-11 — source-variant query deduplication and ordering

- Demonstrated actual SQL returned duplicate `Manga` objects for repeated `merged` rows. Improved `selectMergedMangasById` to return each distinct manga ID once and stable order by reference priority, and `selectByMergeId` to order references explicitly.
- Seven new SQL tests: **4 failures before** the fix, **7 PASS after**. SQLite **27/27 PASS**, separately Python **72/72 PASS** and Kotlin/JVM **38/38 PASS**. **Combined gate timed out during Kotlin and has no PASS report** in this checkpoint; these are three independent completed suites, totaling 137 passing checks.
- Source hashes for updated `merged.sq`, new SQL tests and gate minimum matched GitHub. Evidence: https://drive.google.com/file/d/1rpLs10hlX343u0HlSTldyp6O27NBjRRA/view , SHA256 `a9f9a6d3cd7a876d0f83c7f246aef60c3a5dc79af79eb9c0ff22c0dff6afcb79`.
- #10 remains open for schema constraints, preexisting duplicates, concurrency; Android codegen/runtime still untested, issue #2 open, PR #1 draft, migration15 blocked.


## 2026-10-11 — whole virtual work deletion protected by real-source guard

- `deleteByMergeId` was proven to leave a virtual parent orphan. Patched it to delete **only the virtual `mangas` row** (`_id=:mergeId AND source=:mergedSourceId`) with `MERGED_SOURCE_ID` passed from `MangaMergeRepositoryImpl`. Existing migration14 FK cascade removes links; child mangas untouched. Single-reference unlink unchanged; no migration/DDL edits.
- New 9-case SQLite regression file demonstrated original bug (6/8 failures before fix), now **36/36 SQLite PASS**. Full Python **72/72 PASS** and Kotlin **38/38 PASS** completed independently (146 successful checks). The combined gate did NOT finish due timeout during Kotlin: do not claim a unified 146/146 PASS.
- Source hashes of all five edited/new files match committed GitHub blobs. Fix commit `fbebe210`. Evidence archive `Polaris_R001_Virtual_Deletion_Evidence_2026-10-11.zip` in the ChatGPT conversation.
- **#8 remains open** pending actual bundled driver cascade, delete UI/caches, Android runtime. #9/#10/#11 remain open; PR #1 draft, migration15 blocked.

## 11/10/2026 — issue #9: projeção testada dos contadores da biblioteca (candidata)

- Protótipo de `libraryView` para obras multifonte implementado, respeitando os 5 modos de ordenação/deduplicação, lidos, bookmarks, scanlator, datas, favoritos e identidades reais.
- **25/25 testes SQLite do candidato PASS**: 18 de projeção + 7 de reconstrução de view/upgrade simulado. A definição original Yomotsu `libraryView.sq` e a migração14 usada nos testes foram conferidas contra os blobs exatos fixados.
- Os arquivos ficam em `spikes/spike001/audit/`: `libraryView_candidate.sql`, `migration14_view_candidate.sql`, `test_virtual_library_projection.py` e `test_library_upgrade_candidate.py`. **Não são aplicados pelo Spike-001 atual** nem integram a contagem das suítes de produção; a issue #9 continua aberta.
- Antes de integrar: SQLDelight/mapper e dependências reativas, benchmark em dispositivo, e estratégia de upgrade para bancos que já receberam a migração14. **Migração15 continua bloqueada**.
- Ver `docs/r001/ISSUE009_LIBRARY_COUNTER_PROPOSAL_2026_10_11.md`.
