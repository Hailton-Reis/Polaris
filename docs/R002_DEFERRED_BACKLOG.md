# Polaris — R002 / Deferred Backlog

This document protects R001 from scope creep.

## Isolated HTTP sessions and illustrated icon rewards P20261111.1

[Scoped HTTP session storage and illustrated icon rewards](SESSOES_E_ICONES_P20261111_1.md) are implemented in development. Persistent cookies use authenticated Keystore encryption, temporary cookies stay in host memory, and clearing a principal revokes older clients. Artwork replaces the four geometric launcher marks, with reading-point milestones and retained previous choices. Browser profile/login integration and real-provider/ARM acceptance remain open; HTTP cookie persistence does not close generic WebView authentication.

## Sandbox preferences and filters P20261110.3

[Basic typed preferences, stock host widgets and source filters](SANDBOX_PREFERENCIAS_FILTROS_P20261110_3.md) are implemented in development. Package/signer-scoped storage and explicit legacy import preserve native backup keys; restore now rejects non-native source preference namespaces. Real-provider compatibility, dynamic controls, login/WebView, cross-session cookies and novels remain open. Public beta.10 remains unchanged.

## Library review P20261110.2

[Review findings and fixes](REVISAO_BIBLIOTECA_P20261110_2.md): shared numbering validation on reads and transactional commit, correct season/volume/part scope for adjacent ranges, non-favorite preference handling and per-edition parsing. Post-association criterion revalidation is implemented. Semantic renumbering, full real-provider/backup/reader flows, external-reader acceptance and ARM performance remain open.

## Audit checkpoint P20261107.1

See [the current audit](AUDITORIA_GERAL_P20261107_1.md) for implemented components, evidence and outstanding acceptance. Cosmetic titles, launcher icons and themes are implemented in development; they do not close the following backlog. Global search/restored-library work deduplication, novel multi-source continuity, broader sandbox compatibility, cross-edition page correspondence, content-addressed reuse and physical ARM acceptance remain open. The opt-in HTTP sandbox is not a guarantee for compatibility-mode extensions. Public beta.10 remains unchanged.

## Unified search checkpoint P20261109.1

Global comic search now groups corroborated works and can reopen an existing favorite while retaining a per-source view. [Behavior and limits](BUSCA_UNIFICADA_P20261109_1.md). This search checkpoint did not consolidate already-separated library records. The subsequent [P20261110.1 library checkpoint](BIBLIOTECA_UNIFICADA_P20261110_1.md) adds reversible native-record association and grouped presentation; real restored-library/download/reader acceptance remains open. Unknown media and ambiguous metadata are kept separate. Public beta.10 remains unchanged.

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

The user originally deferred this expansion while validating **Polaris P20261031.1**, then authorized advancing after confirming that disabling border crop aligned the saved translation. The initial document implementation was added in P20261031.3. The [P20261031.4 candidate](../integration/document-reader/README.md) adds explicit organization before importing a selected phone file, using content-type and optional format categories. The requirements below remain the intended scope; implementation and device-acceptance limits are recorded there. None of these capabilities are retroactively claimed for the installed P20261031.1 APK. The separate two-source acceptance gate does not block this independent work.

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

The crop-off diagnosis is confirmed. Automatic crop protection and the document candidate still need visual/device acceptance. This does not reopen the completed diagnostic round or require a full OCR rerun.

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
