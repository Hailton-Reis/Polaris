# Spike-010 — Canonical persistence schema

Proposed SQLDelight persistence for Polaris after Spike-001 runtime passes.

## Principle

Do not replace Yomotsu/Mihon's `mangas` and `chapters` tables.

Instead:
- one virtual manga row represents the canonical/library entry;
- child manga rows remain source-specific and continue to work with the existing Reader;
- Polaris tables connect them and own canonical identity, health and cross-source progress.

All tables are prefixed `polaris_` to reduce upstream collision risk.

## Tables

- `polaris_works`: canonical identity -> virtual manga.
- `polaris_work_aliases`: multilingual aliases.
- `polaris_external_ids`: AniList/MAL/etc anchors.
- `polaris_source_variants`: child manga entries + coverage/alignment.
- `polaris_source_health`: source-level reliability state.
- `polaris_canonical_chapters`: source-independent chapter identity/read state.
- `polaris_chapter_variants`: maps real child chapters to canonical chapters.

## Progress

Canonical chapter read/bookmark state belongs to `polaris_canonical_chapters`.

Page-level progress remains attached to the real child chapter because page indexes may differ between sources. `last_variant_chapter_id` remembers which real variant the user was reading.

## Migration sequencing

Baseline Yomotsu migrations end at 13.
Spike-001 stages migration 14 for `merged`.
This schema is therefore staged as migration 15.

Do not apply migration 15 until the Spike-001 Android runtime gate passes.
