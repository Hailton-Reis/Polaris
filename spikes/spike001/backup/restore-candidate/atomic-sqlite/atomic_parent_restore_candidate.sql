-- POLARIS R001 CANDIDATE ONLY. Do not add to migration 15 yet.
-- Apply after an explicit legacy-duplicate audit, inside a schema migration
-- that aborts rather than silently deleting or picking duplicate links.
-- Uses ordinary SQLite constraints, no JSON1/expression-index dependency.
-- Production Android migration/SQLDelight compatibility is NOT established.
CREATE TABLE IF NOT EXISTS polaris_restore_ledger (
    archive_uuid TEXT NOT NULL PRIMARY KEY,
    parent_manga_id INTEGER NOT NULL UNIQUE,
    archive_digest TEXT NOT NULL,
    FOREIGN KEY(parent_manga_id) REFERENCES mangas(_id) ON DELETE CASCADE
);

-- One source URL/identity per parent, whether resolved or pending. This
-- prevents the older partial NOT EXISTS checks from racing each other.
CREATE UNIQUE INDEX IF NOT EXISTS polaris_merged_source_identity_unique
ON merged(merge_id, manga_source, manga_url);

-- Also block a single real manga row being attached twice to one parent,
-- even when a corrupted reference's saved source/URL differs.
CREATE UNIQUE INDEX IF NOT EXISTS polaris_merged_real_id_unique
ON merged(merge_id, manga_id) WHERE manga_id IS NOT NULL;
