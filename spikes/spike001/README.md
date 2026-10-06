# Polaris — Spike-001 patch bundle

This bundle is a first engineering port for the agreed architecture:

- Base: Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`
- Reference: TachiyomiSY `14648c7cf0aa84e5a35d48de9dbf1386df6cca42`
- Both upstream projects use Apache License 2.0.

## Goal

Prove a virtual work can reference multiple source-specific manga entries and expose one aggregated chapter list, while each chapter still opens through its original source.

## Deliberate constraints

This is NOT yet CanonicalWork, SourceHealth, SourceRanker, automatic title matching, or translation routing.

It intentionally avoids ReaderViewModel changes because Yomotsu's `MangaScreen.openChapter()` already starts the reader with `chapter.mangaId`; aggregated chapters therefore retain their real source identity.

## Implemented in staging

- SQLDelight `merged` table + migration 14
- merge domain model/repository
- merge CRUD/use cases
- merged chapter aggregation adapted to Yomotsu's existing ChapterRepository API
- virtual `MergedSource`
- manual `CreateMergedManga` use case for the spike
- replacement `GetMangaWithChapters` that automatically routes merged works

## Before PASS

1. Apply existing-file modifications in `MODIFICATIONS.md`.
2. Build Yomotsu.
3. Create two child manga entries with populated chapters.
4. Call `CreateMergedManga(listOf(idA, idB))`.
5. Open the virtual manga and verify aggregated/deduplicated chapters.
6. Open one chapter from each source.
7. Remove one reference and verify the virtual work survives.

See `VALIDATION.md` for completed compiler/domain tests.
