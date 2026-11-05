# Spike-004 — CanonicalChapterResolver

Pure Kotlin prototype for turning source-specific chapter lists into canonical chapter identities.

## Why this exists

Source aggregation is easy when every source numbers chapters identically. Real sources do not:
- decimals: 10.5;
- comma decimals: 10,5;
- prologue/epilogue;
- extras/specials;
- seasons that restart numbering;
- Episode vs Chapter naming;
- one source can be offset by +1/-1 from another.

## Scope

This spike implements:
- chapter-name parsing;
- chapter kind classification;
- season extraction;
- decimal normalization;
- canonical grouping;
- conservative source-number offset detection.

It deliberately does NOT silently merge ambiguous specials.

## Offset detection

A small offset (-5..+5, step 0.5) is accepted only when it aligns a large portion of both sources and has enough evidence. This catches common 0-based/1-based or half-step numbering differences without guessing wildly.

## Integration target

After Spike-001 proves multi-source runtime, Polaris should:
1. collect child chapter lists;
2. normalize each chapter into a CanonicalChapterKey;
3. optionally apply a trusted source offset;
4. group variants;
5. let SourceRanker choose the best ChapterVariant inside each canonical chapter.
