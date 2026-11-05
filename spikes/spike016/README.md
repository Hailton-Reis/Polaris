# Spike-016 — Canonical progress policy

Polaris owns source-independent chapter completion/bookmark state, but page indexes remain source-variant specific.

## Rules

- completing any child chapter marks the canonical chapter read;
- reading another variant later must not erase canonical completion;
- bookmark can be mirrored across currently linked child rows for Yomotsu UI compatibility;
- lastVariantChapterId records which real child produced the current page progress;
- page index resumes only when reopening that exact child chapter;
- when switching source variants, start that chapter from page 0 until page/image correspondence exists;
- canonical mark-read/unread can be mirrored to all currently linked child chapter rows.

This prevents dangerous assumptions such as “page 17 in Source A == page 17 in Source B”.

Pure Kotlin tests cover same-variant resume, source switch, completion persistence and child-state mirroring.
