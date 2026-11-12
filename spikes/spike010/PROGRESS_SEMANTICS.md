# Canonical progress semantics

## Chapter-level state

Polaris canonical state is authoritative for:
- read/unread;
- bookmark;
- last canonical chapter opened/read;
- last real variant used.

## Page-level state

Do not blindly copy `last_page_read` across source variants.

Two sources can:
- split pages differently;
- use double pages;
- have different scan releases;
- have different image counts.

For an unfinished chapter:
- preserve page index on the exact child chapter used;
- store `last_variant_chapter_id` on the canonical chapter;
- resume that same variant when still healthy/available;
- if forced to switch variants, resume the chapter from the beginning unless a future page-matching algorithm exists.

## Read propagation

When a canonical chapter becomes fully read:
- mark canonical `read = true`;
- optionally mark all mapped child chapters read to remain compatible with Mihon UI/filter semantics.

When one child chapter is marked read outside Polaris:
- canonical chapter may be promoted to read if the mapping is trusted.

Do not infer page-level progress from another variant.
