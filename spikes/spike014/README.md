# Spike-014 — Stable canonical translation scope

## Problem

Yomotsu currently uses `ComicTranslationContext.mangaTitle` for two different jobs:

1. human/LLM context: "what series is this?"
2. persistent storage identity for TranslationMemory/TranslationCache/Glossary.

Polaris cannot keep those coupled.

A canonical work can change preferred display title and can have child source titles in different languages. Translation intelligence must remain one stable scope.

## Proposed compatible change

Extend Yomotsu context conceptually to:

```kotlin
data class ComicTranslationContext(
    val mangaTitle: String,       // display/prompt title
    val chapterName: String,
    val memoryScopeKey: String = mangaTitle,
)
```

Existing Yomotsu callers remain source-compatible because the third argument has a default.

Polaris calls it with:

```kotlin
ComicTranslationContext(
    mangaTitle = canonicalWork.preferredTitle,
    chapterName = realChapter.name,
    memoryScopeKey = "polaris:" + canonicalWork.stableKey,
)
```

## Required Yomotsu modifications

### TranslationMemory
Every persistent key currently based on:
`normalizeMangaKey(context.mangaTitle)`

must use:
`contextMemoryKey(context)`

where:

```kotlin
internal fun contextMemoryKey(context: ComicTranslationContext): String =
    context.memoryScopeKey.trim().lowercase()
```

The registered scope should still retain `context.mangaTitle` as the friendly display label.

### TranslationCache
The manga portion of cache scope must use the same stable memory key.

### TranslationIntelligence backup/export
Registered scope snapshots must carry both:
- stable scope key;
- friendly manga title.

Restore must rebuild `ComicTranslationContext` with both values.

### TranslationGlossary
No algorithm change is necessary if it continues to access TranslationMemory through ComicTranslationContext.

### Prompt
Prompt should continue using `context.mangaTitle`, not the storage key.

## Migration compatibility

Old non-Polaris manga:
- memoryScopeKey defaults to mangaTitle;
- behavior remains unchanged.

Polaris canonical work:
- stable key survives source/title changes;
- one glossary/memory/cache across EN/PT/KO/etc variants.

## R001 acceptance

Change preferred display title for a canonical work after adding glossary entries.
Expected:
- prompt shows new title;
- previously stored glossary/memory is still found through stable scope key.
