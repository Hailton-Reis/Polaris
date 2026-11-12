# Polaris — Final handoff before Work mode

Date: 2026-10-06

## Repository state

Repository:
`Hailton-Reis/Polaris`

Primary engineering branch:
`r001/multisource-foundation`

Draft PR:
`#1 — R001: multi-source foundation spikes`

Practical Android issues:
- #2 — build pinned Yomotsu + validate Spike-001 runtime;
- #3 — canonical persistence/chapter mapping/metadata/lifecycle;
- #4 — discovery, aliases, semantic matching, manual overrides;
- #5 — source health, ranking, refresh and chapter-open orchestration;
- #6 — bridge Polaris routing to Yomotsu translation;
- #7 — full runtime acceptance/regression.

## Product decisions frozen

### Product identity
Official project/app name: Polaris.

### Core UX
The user chooses a work, not a source.

A canonical work can contain multiple source/language variants.

The app:
1. prefers usable PT-BR;
2. prefers the best same-language source by health/coverage/freshness;
3. falls back to PT;
4. falls back to EN;
5. falls back to the original language/other configured languages;
6. translates foreign content automatically when needed.

The user should not manually migrate sources just because one source fails or becomes outdated.

### Canonical identity
CanonicalWork owns:
- immutable internal UUID;
- preferred title;
- aliases;
- external tracker/metadata IDs;
- source variants;
- canonical chapters;
- canonical read/bookmark state.

Source-specific manga/chapter rows remain real Yomotsu/Mihon entities.

Tracker IDs and titles are correlation evidence, never the primary Polaris identity.

### Work matching
Priority of evidence:
- explicit manual FORCE_SAME / FORCE_DIFFERENT;
- shared trusted external IDs;
- normalized title/aliases;
- author/artist;
- chapter structure;
- description/genres;
- semantic/LLM adjudication for REVIEW candidates.

Conflicting IDs in the same trusted namespace are a hard conflict.

Ambiguous works are never silently merged.

### Source selection
Selection is per canonical chapter.

Source health states include:
- HEALTHY
- DEGRADED
- AUTH_REQUIRED
- AUTH_EXPIRED
- CHALLENGED
- RATE_LIMITED
- BROKEN
- UNREACHABLE

Health beats a tiny chapter-count advantage.
Language preference is a dominant routing tier.
Hysteresis prevents source flapping.

### Authentication / Cloudflare
No automatic anti-bot bypass is required.

When a source requires login/challenge:
- user interacts manually;
- app keeps/reuses valid cookies/session/tokens where possible;
- successful revalidation returns source to normal ranking.

### Translation
Reuse Yomotsu translation infrastructure.

Do not build another OCR/translation stack.

Polaris decides when translation is required.

Yomotsu remains responsible for:
- OCR;
- inpainting;
- typesetting;
- Gemini/OpenRouter/DeepL/Google/ML Kit providers;
- provider fallback;
- translation cache;
- translation memory;
- glossary.

Polaris adds one stable canonical translation scope:
`polaris:<canonical-uuid>`

Friendly display title may change without losing glossary/memory.

### LLM policy
LLMs may be used frequently if they improve quality/speed.

Allowed uses include:
- translation;
- semantic work matching;
- ambiguity resolution;
- metadata assistance.

The design does NOT try to minimize LLM usage by principle.

### Server policy
App-first / server-optional.

A personal server is not required.

The app may call external providers directly.

A future server can be attached only as an accelerator for:
- larger local models;
- heavy OCR/inpainting;
- batch/background work;
- prefetch;
- Ollama/local LLM.

The app must continue working when that server is offline.

### Progress
Canonical:
- read/unread;
- bookmark;
- canonical chapter completion.

Real child chapter:
- page index;
- source-specific files/downloads.

Never copy page index blindly across source variants.

### Source loss
A canonical work survives source loss.

States:
- ACTIVE — one or more usable variants;
- DEGRADED — linked variants exist but none are usable;
- ORPHANED — no linked variants remain.

Progress/history/identity must not be deleted because a site disappeared.

## Technical base

Android base candidate:
Yomotsu pinned at:
`0fb80c439ef816eeb50674f1b90af39918b176d8`

Multi-source reference:
TachiyomiSY pinned at:
`14648c7cf0aa84e5a35d48de9dbf1386df6cca42`

Key architectural discovery:
Yomotsu opens the reader using the selected real `chapter.mangaId`.

Therefore a canonical/virtual work can list chapters belonging to different real child manga/source rows without rewriting the reader core.

## Framework-independent work completed

Spikes:

001 — staged Merged Manga/Yomotsu multi-source port.
002 — SourceRanker / CanonicalWork / SourceVariant / SourceHealth model.
003 — AutomaticWorkMatcher.
004 — CanonicalChapterResolver + number alignment.
005 — SourceHealthTracker.
006 — TranslationDecisionPolicy.
007 — ChapterOpenPlanner.
008 — SearchResultClusterer.
009 — AliasSearchPlanner.
010 — canonical SQLDelight schema / staged migration 15.
011 — SemanticWorkMatcher LLM contract.
012 — SourceAccessClassifier.
013 — LanguageRoutePlanner.
014 — stable canonical translation memory/cache/glossary scope.
015 — content-addressed translation artifact identity.
016 — CanonicalProgressPolicy.
017 — SelectionDiagnostics.
018 — provider-neutral backup/restore contract.
019 — immutable canonical UUID identity.
020 — manual work-link overrides.
021 — integrated R001 domain scenario simulation.
022 — VariantRefreshPlanner.
023 — CanonicalMetadataResolver.
024 — CanonicalWorkLifecyclePolicy.

The R001 integrated domain simulation already passes.

## Important reusable Yomotsu findings

### Search
Reuse Yomotsu global search.
Do not create another source-search engine.

Polaris layers on:
- clustering;
- aliases;
- automatic matcher;
- semantic review;
- second-pass alias searches.

### Reader
Keep real child manga/chapter IDs.

Do not clone real child chapters into a virtual parent.

### Translation
Keep real child source identity for page/files/download operations.

Use canonical UUID for translation intelligence scope.

## Work/Codex must focus on heavy integration

Read, in order:
1. `docs/r001/START_HERE.md`
2. `docs/r001/NON_WORK_COMPLETED.md`
3. `docs/r001/WORK_HANDOFF_PROMPT.md`
4. `docs/r001/WORK_CODEX_CHECKLIST.md`
5. `docs/r001/RUNTIME_ACCEPTANCE_TESTS.md`

Then begin with issue #2.

Exact first gate:
1. checkout pinned Yomotsu;
2. build it unmodified;
3. apply/reconcile Spike-001;
4. generate SQLDelight;
5. build debug APK;
6. install two real compatible sources/extensions;
7. create one virtual work with two child mangas;
8. open one chapter from Source A;
9. open one chapter from Source B;
10. verify removing one source reference does not corrupt the work.

Do not apply migration 15 until this gate passes.

## After issue #2 passes

Issue #3:
- canonical DB repositories/mappers;
- UUID identity;
- source variants;
- aliases/external IDs;
- canonical chapters;
- canonical progress;
- metadata resolver;
- lifecycle/orphan preservation.

Issue #5:
- SourceHealth instrumentation;
- ranking;
- refresh planner;
- language routing;
- open planner;
- diagnostics.

Issue #4:
- global search adapters;
- clustering;
- alias pass;
- semantic LLM provider;
- manual overrides.

Issue #6:
- canonical translation context bridge into Yomotsu.

Issue #7:
- full acceptance/regression matrix.

## Scope protection

Do NOT spend Work/Codex time redesigning framework-independent behavior unless the real Android/Yomotsu integration demonstrates a concrete incompatibility.

Prefer adapter changes over domain-policy redesign.

Any semantic change should include:
- reason;
- failing real integration case;
- regression test.

## Runtime acceptance minimum

R001 cannot be marked complete until real Android tests prove:
- one work across at least two real sources;
- correct child-source reader routing;
- PT-BR redundancy;
- unhealthy same-language fallback;
- EN fallback;
- automatic Yomotsu translation;
- canonical glossary/memory across aliases;
- auth revalidation;
- matching conflict protection;
- decimal/season/offset chapter handling;
- canonical progress surviving source switch;
- no critical Yomotsu regressions.

## Final instruction for new Work conversation

Continue Polaris from GitHub; do not rely on the previous chat.

The repository and documents above are the source of truth.
