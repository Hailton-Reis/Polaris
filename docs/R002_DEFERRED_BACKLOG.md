# Polaris — R002 / Deferred Backlog

This document protects R001 from scope creep.

## R001 must prove only

- one canonical work can link multiple real source manga;
- chapters are canonicalized conservatively;
- the best real source variant is selected automatically;
- PT-BR redundancy works;
- foreign fallback works;
- Yomotsu translation is invoked automatically when needed;
- canonical read/bookmark survives source switch;
- user authentication/challenge is interactive;
- app works without a personal server.

Anything below is valuable but must not block that proof.

## R002 — quality, reuse and resilience

### Cross-source translation reuse
Input: Spike-015.

Add a secondary content-addressed cache index using page SHA-256 + translation pipeline revision.

Goal:
if two sources serve identical page bytes, reuse OCR/translation even though their URLs differ.

Do not replace Yomotsu's source-specific translation files until runtime evidence justifies it.

### Backup / restore
Input: Spike-018.

Extend Yomotsu backup with Polaris canonical state.

Restore relationships by:
sourceId + sourceWorkKey + chapterUrl,
never by destination-local DB IDs.

Unresolved variants should be reported, not silently discarded.

### Better diagnostics
Input: Spike-017.

Advanced/debug UI:
- source selected;
- reason/score;
- excluded variants and health reason;
- translation decision;
- current canonical work/chapter mapping.

Default reader UX remains simple.

### Smarter source health
Potential future layers:
- source-wide health;
- title-specific variant health;
- endpoint-specific health;
- rolling time windows;
- adaptive retry/cooldown.

Do not aggressively background-probe sources.

### Page correspondence
Optional future feature:
- perceptual/image hashes;
- page-to-page correspondence across sources;
- partial reading resume after source switch.

Until this exists, never copy page indexes across variants.

### Better translation cache invalidation
Separate revisions for:
- OCR geometry;
- OCR text;
- translation provider/model;
- glossary;
- inpainting;
- typesetting/render.

This can avoid recomputing OCR when only final rendering changes.

## R002 — novels

Polaris should reuse Yomotsu's novel reader/runtime.

For textual chapters:
- bypass OCR;
- use text translation directly;
- apply same CanonicalWork / aliases / SourceHealth / SourceRanker concepts;
- share canonical translation memory/glossary;
- preserve paragraph/section progress according to the novel reader's existing model.

Do not force manga page abstractions onto novels.

## Document formats and broad discovery — requested 2026-10-31

The user explicitly deferred this expansion to a later version while validating the current **Polaris P20261031.1** candidate. These are requirements, not capabilities added to that APK. This deferral does not make the separate two-source acceptance gate a prerequisite for independent reader improvements.

Requested formats and uses:

- PDF articles, books and comics, including image-based/scanned pages.
- EPUB text books as well as illustrated EPUBs. The inspected upstream EPUB loader currently exposes embedded images as reader pages; that is partial EPUB support, not a complete text-book reading path.
- DOCX documents and TXT files, alongside existing supported comic archives.
- Reading progress, suitable text layout and translation appropriate to each document type. Native text should use text translation; image/scanned content needs OCR. Preserve figures and reading order where supported.

Requested discovery:

- Search by name/title, author, DOI and related bibliographic fields.
- Combine multiple bibliographic indexes, repositories and configurable source providers; support importing local files and opening/importing direct document URLs.
- Allow user-selected external/non-curated sources instead of restricting discovery to the initial bundled repository catalog. Identify the source of each result and keep extension trust/platform checks distinct from document compatibility.
- A broad federated search must state which providers it queried. Do not claim exhaustive coverage of the entire internet or availability of a downloadable full text for every result.

Before this expansion, the immediate user test is the installed revision in About, the same Guilty Library page in paginated and long-strip modes, and zoom/pan behavior. The current PDF/EPUB/DOCX/TXT expansion is not part of that acceptance claim.

## R002 — optional accelerator server

A personal server remains optional.

Only add it after profiling proves value for:
- large local models;
- expensive OCR/inpainting;
- translation batch jobs;
- background/prefetch while phone is idle;
- Ollama/local LLM.

Architecture rule:
server must implement an optional provider/worker interface. App behavior cannot depend on server availability.

## Later

- sync canonical library between devices;
- richer metadata provider integrations;
- optional creator/official links;
- import/export interoperability;
- public distribution hardening;
- accessibility/voice/TTS improvements;
- polished canonical-work UI;
- automatic benchmark-based provider routing.

## Anti-goals

Do not add:
- server merely as API proxy;
- generic anti-bot bypass;
- central copyrighted content hosting;
- source-specific hacks in Polaris core when an extension owns that responsibility.
