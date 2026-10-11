-- CANDIDATE ONLY: not wired into the Yomotsu SQLDelight build.
-- Execute relink + cleanup within one transaction after the real child row exists.
-- Preserve the existing settings/priority of the oldest pending reference.
-- The real manga's source+URL must match exactly; source 6969 is excluded.

-- name: relinkPendingChild
UPDATE merged
SET manga_id = :resolvedMangaId
WHERE _id = (
    SELECT MIN(_id) FROM merged
    WHERE merge_id = :mergeId
      AND manga_id IS NULL
      AND manga_source = :childSourceId
      AND manga_url = :childUrl
)
AND :childSourceId != 6969
AND EXISTS (
    SELECT 1 FROM mangas real
    WHERE real._id = :resolvedMangaId
      AND real.source = :childSourceId
      AND real.url = :childUrl
)
AND NOT EXISTS (
    SELECT 1 FROM merged already
    WHERE already.merge_id = :mergeId AND already.manga_id = :resolvedMangaId
);

-- name: dropRedundantPendingChildren
DELETE FROM merged
WHERE merge_id = :mergeId
  AND manga_id IS NULL
  AND manga_source = :childSourceId
  AND manga_url = :childUrl
  AND :childSourceId != 6969
  AND EXISTS (
      SELECT 1 FROM mangas real
      JOIN merged attached ON attached.manga_id = real._id
      WHERE attached.merge_id = :mergeId
        AND real._id = :resolvedMangaId
        AND real.source = :childSourceId
        AND real.url = :childUrl
  );
