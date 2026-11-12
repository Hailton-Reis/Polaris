# Existing-file modifications for Spike-001

Baseline: Yomotsu commit `0fb80c439ef816eeb50674f1b90af39918b176d8`.

## DomainModule.kt

Add merge repository/interactor registrations and change:

```kotlin
addFactory { GetMangaWithChapters(get(), get()) }
```

to:

```kotlin
addFactory { GetMangaWithChapters(get(), get(), get()) }
```

## GetMangaWithChapters.kt

Add `GetMergedChaptersByMangaId` as a third constructor dependency and route chapter reads based on `MERGED_SOURCE_ID`.

The replacement body is stored in `REPLACEMENT_GetMangaWithChapters.kt`.

## AndroidSourceManager.kt

Register the virtual source:

```kotlin
MERGED_SOURCE_ID to MergedSource(),
```

## MangaScreen.kt

No reader change is needed for the spike. `openChapter()` already launches the reader with `chapter.mangaId`, so a chapter aggregated from Source B opens Source B's real manga automatically.

For Spike-001, disable bulk download/translation actions while the parent source is `MergedSource`, because those operations still assume one parent source.

## Creation hook

`CreateMergedManga` is deliberately domain-only in this patch. Call it from a debug action/test using two already-existing manga IDs. The final product will replace this manual hook with `AutomaticWorkMatcher`.
