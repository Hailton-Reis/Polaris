# Polaris

Polaris is a multilingual, multi-source reader focused on a simple idea:

> Choose the work. Polaris chooses the best available source.

## Goals

- Treat a work as the primary entity instead of tying the library to one source.
- Correlate equivalent releases across languages and providers.
- Prefer healthy PT-BR sources when available.
- Fall back automatically to another source or language when needed.
- Translate content to PT-BR when the preferred language is unavailable.
- Keep reading progress attached to the canonical work.
- Run app-first, without requiring a personal backend.
- Use external LLM/API providers directly when they improve quality or speed.
- Keep a personal server optional as an accelerator only.

## Technical direction

Current engineering baseline:

- Yomotsu / Mihon ecosystem as the Android foundation.
- Merged Manga concepts from TachiyomiSY for multi-source aggregation.
- Polaris-specific CanonicalWork, SourceVariant, SourceHealth and SourceRanker layers.
- Existing Yomotsu OCR, translation, inpainting, glossary and translation-memory capabilities as the starting point for multilingual reading.

## Current milestone

R001 — Multi-source foundation.

The first milestone proves that one virtual/canonical work can aggregate chapters from multiple sources and open each chapter using its real underlying source. Automatic work matching and intelligent source ranking are layered on top only after that foundation is stable.

## Status

Early private development.

See the R001 engineering documents on the development branch for current implementation status and handoff notes.

The Android candidate now includes download-and-translate actions, English-source download translation, translation layout corrections, a bundled repository catalog and clearer chapter variants. See the [reader implementation and verification](integration/reader-translation-ux/README.md) and [30 October candidate test guide](docs/reader/DISCOVERY_CHAPTER_CLARITY_2026_10_30.md). Build/unit verification does not replace the pending visual checks on the Windows test device.

The [P20261031.2 reader candidate](docs/reader/PAGER_CROP_FIX_P20261031_2.md) preserves original image borders on translated pages. The user confirmed that disabling border crop aligns the prior candidate; automatic handling in the new candidate still needs Windows visual acceptance.

The [P20261031.4 document candidate](integration/document-reader/README.md) adds PDF pages, reflowable EPUB/DOCX/TXT reading, selective local import, federated article/book search and a configurable in-app search website. Documents are included only after an explicit selection and organization step, with content-type and optional format categories. See the [organization guide](docs/reader/DOCUMENT_ORGANIZATION_P20261031_4.md) and [reader acceptance guide](docs/reader/DOCUMENTS_P20261031_3.md); Android import, rendering and visual acceptance remain pending device testing.

Local Android builds now detect CPU/RAM, enable Gradle cache/parallelism and combine APK assembly with tests per variant. See the [build-performance profile and verification limits](docs/r001/LOCAL_BUILD_PERFORMANCE_2026_10_31.md); performance on the user’s Windows PC remains to be measured.

## License and attribution

Polaris is intended to remain compatible with the Apache-2.0 lineage of Mihon, Yomotsu and TachiyomiSY where code is reused. See `LICENSE` and `NOTICE`.

Third-party models, libraries and assets may have their own licenses and must be reviewed individually before distribution.
