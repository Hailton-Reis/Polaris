-- Polaris R001 staging bridge only; NOT a production migration.
-- Pinned Yomotsu SHA 0fb80c439ef816eeb50674f1b90af39918b176d8
-- contains no merged.sq/table. These columns are required by existing
-- candidate SqlDelightPolarisAtomicVirtualWorkPort and polarisRestore.sq.
-- Real Android schema/migration must be separately reviewed and generated.
CREATE TABLE merged (
 _id INTEGER NOT NULL PRIMARY KEY,
 info_manga INTEGER NOT NULL,
 get_chapter_updates INTEGER NOT NULL,
 chapter_sort_mode INTEGER NOT NULL,
 chapter_priority INTEGER NOT NULL,
 download_chapters INTEGER NOT NULL,
 merge_id INTEGER NOT NULL,
 merge_url TEXT NOT NULL,
 manga_id INTEGER,
 manga_url TEXT NOT NULL,
 manga_source INTEGER NOT NULL,
 FOREIGN KEY (merge_id) REFERENCES mangas(_id) ON DELETE CASCADE,
 FOREIGN KEY (manga_id) REFERENCES mangas(_id) ON DELETE SET NULL
);
CREATE INDEX polaris_merged_parent_lookup ON merged(merge_id);
CREATE UNIQUE INDEX polaris_merged_source_identity_unique
 ON merged(merge_id,manga_source,manga_url);
CREATE UNIQUE INDEX polaris_merged_real_id_unique
 ON merged(merge_id,manga_id) WHERE manga_id IS NOT NULL;
CREATE TABLE polaris_restore_ledger (
 archive_uuid TEXT NOT NULL PRIMARY KEY,
 parent_manga_id INTEGER NOT NULL UNIQUE,
 archive_digest TEXT NOT NULL,
 FOREIGN KEY(parent_manga_id) REFERENCES mangas(_id) ON DELETE CASCADE
);
