# Polaris Persistence Schema V1 — Draft

## Principle

Yomotsu's existing `mangas` and `chapters` remain the source-specific truth.

Polaris adds canonical relationships on top. It should not copy page content or replace extension-owned identifiers.

## Tables

### polaris_work
Canonical library identity.
- id
- preferred_title
- original_language
- created_at
- updated_at

### polaris_alias
Known names for the work.
- work_id
- language nullable
- value
- normalized_value
- confidence
- provenance: source / tracker / llm / user

### polaris_external_id
Strong metadata anchor.
- work_id
- namespace
- value
Unique(namespace, value).

### polaris_source_variant
Relationship between canonical work and real Yomotsu manga.
- work_id
- manga_id -> mangas._id
- source_id
- source_work_key/url
- language
- observed_title
- chapter_count
- highest_chapter_number
- last_updated_at

A real manga should belong to at most one canonical work unless manually detached/relinked.

### polaris_source_health
Dynamic source-variant health.
- source_variant_id
- state
- success_rate
- average_latency_ms
- consecutive_failures
- total_successes
- total_failures
- last_success_at
- last_failure_at
- last_failure_kind
- cooldown_until

### polaris_chapter
Canonical chapter identity.
- work_id
- season nullable
- number nullable
- part nullable
- kind
- semantic_key nullable

### polaris_chapter_variant
Relationship from canonical chapter to a real Yomotsu chapter.
- canonical_chapter_id
- source_variant_id
- chapter_id -> chapters._id
- observed_name
- scanlator nullable

## Bootstrap relationship to Spike-001

The Spike-001 `merged` table is temporary bootstrap infrastructure.

Do not delete it during the first runtime proof.

After Polaris canonical persistence works, either:
- migrate merged references into polaris_work/source_variant and retire merged; or
- keep merged only as a compatibility adapter for Yomotsu UI.

Decision should be based on the first Android integration, not guessed now.

## Backup requirement

A Polaris backup eventually needs:
- canonical work identities;
- aliases/external IDs;
- source-variant links;
- source ranking preferences;
- canonical chapter mappings when manually corrected;
- translation canonical context identity.

Transient health history can be omitted or truncated.
