# Spike-007 — ChapterOpenPlanner

Composition layer for the core Polaris user story:

> Open this canonical chapter using the best available source, translating only when necessary.

It combines:
- Spike-002 SourceRanker;
- source/language health information;
- Spike-006 TranslationDecisionPolicy.

## Output

The planner returns:
- selected ChapterVariant;
- ranking diagnostics;
- whether the chapter can open directly;
- whether cached translation should be used;
- whether Yomotsu translation should be queued.

## Runtime target

In the Android integration this planner sits immediately before launching/opening a chapter.

The real chapter remains attached to its real child manga/source. Polaris only decides which child chapter to open.
