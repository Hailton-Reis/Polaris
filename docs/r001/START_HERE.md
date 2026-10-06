# Polaris — R001 Handoff

Date: 2026-10-06

## Product direction frozen for R001

Base candidate: Yomotsu on top of Mihon 0.20.4.

Architecture:
- Work-first, not source-first.
- A canonical work owns many source variants.
- The best source is selected per chapter.
- PT-BR is preferred when usable.
- Same-language source selection considers health, coverage, freshness, success history and latency.
- If PT-BR is unavailable, use the next configured language (EN is the default first fallback) and translate.
- LLM/API calls may be frequent when useful.
- A personal server is optional acceleration only; it is never required.
- Authentication/challenge resolution is user-interactive; valid sessions are reused.

## Baselines

Yomotsu:
- repository: kiritsuguxs/yomotsu
- branch: main
- pinned commit: 0fb80c439ef816eeb50674f1b90af39918b176d8

TachiyomiSY reference:
- repository: jobobby04/TachiyomiSY
- branch: master
- pinned commit: 14648c7cf0aa84e5a35d48de9dbf1386df6cca42

## Spike-001

Purpose: minimal Merged Manga infrastructure port for Yomotsu.

Validation already completed:
- patch applicator fixture: PASS;
- Kotlin compilation of domain + virtual source: PASS;
- priority dedupe test: PASS;
- most chapters mode: PASS;
- highest chapter mode: PASS;
- no-dedupe mode: PASS.

Important finding:
Yomotsu's MangaScreen opens ReaderActivity using chapter.mangaId. Child chapters displayed by a virtual merged work therefore naturally open with the real child manga/source. No invasive ReaderViewModel port is needed for the first proof.

## Spike-002

Purpose: source-selection semantics independent of Android.

Contains tested pure Kotlin models:
- CanonicalWork;
- SourceVariant;
- ChapterVariant;
- SourceHealthState/Snapshot;
- SourceRanker.

Tests already passing:
- healthy PT-BR 83 chapters beats healthy PT-BR 80;
- challenged PT-BR 83 loses to healthy PT-BR 80;
- usable PT-BR beats EN regardless of EN's larger coverage;
- EN is selected when PT-BR is not available/usable for the chapter;
- AUTH_REQUIRED falls back until session is revalidated;
- source hysteresis prevents minor source flapping;
- materially worse current source is replaced;
- rate-limit cooldown behavior.

## R001 next engineering order

1. Full Yomotsu build with Spike-001.
2. Real two-source merged work test.
3. Integrate SourceRanker prototype.
4. Add SourceHealth persistence/history.
5. Implement per-chapter resolver.
6. Add canonical work/source variant persistence.
7. Add automatic work matching (rules first, LLM for ambiguity).
8. Connect the selected foreign ChapterVariant to Yomotsu translation pipeline.
9. Add PT-BR -> same-language fallback -> EN translated acceptance scenario.
10. Only then improve UX and background discovery.
