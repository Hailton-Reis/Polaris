-- Candidate view refresh to be appended to migration 14 only after Android acceptance.
DROP VIEW IF EXISTS libraryView;
CREATE VIEW libraryView AS
WITH
-- Original per-source filtered stats, kept unchanged for normal favorites.
real_counts AS (
    SELECT c.manga_id, COUNT(*) AS total,
           SUM(c.read) AS readCount,
           COALESCE(MAX(c.date_upload),0) AS latestUpload,
           COALESCE(MAX(h.last_read),0) AS lastRead,
           COALESCE(MAX(c.date_fetch),0) AS fetchedAt,
           SUM(c.bookmark) AS bookmarkCount
    FROM chapters c
    LEFT JOIN excluded_scanlators es
      ON c.manga_id=es.manga_id AND c.scanlator=es.scanlator
    LEFT JOIN history h ON c._id=h.chapter_id
    WHERE es.scanlator IS NULL
    GROUP BY c.manga_id
),
-- Collapse corrupt repeated association rows to the first-priority source.
linked_children AS (
    SELECT m.merge_id, m.manga_id,
           MIN(m.chapter_priority) AS priority,
           MIN(m._id) AS first_id
    FROM merged m JOIN mangas child ON child._id=m.manga_id AND child.source=m.manga_source
    JOIN mangas parent ON parent._id=m.merge_id AND parent.source=6969
    WHERE m.manga_id IS NOT NULL AND m.manga_id!=m.merge_id AND m.manga_source!=6969
    GROUP BY m.merge_id,m.manga_id
),
root_modes AS (
    SELECT DISTINCT m.merge_id,
           COALESCE((SELECT root.chapter_sort_mode FROM merged root
                     WHERE root.merge_id=m.merge_id AND root.manga_id=root.merge_id AND root.manga_source=6969
                     ORDER BY root._id LIMIT 1),0) AS mode
    FROM linked_children m
),
source_chapters AS (
    SELECT refs.merge_id, refs.manga_id, refs.priority, refs.first_id,
           ch._id AS chapter_id, ch.chapter_number,
           ch.read, ch.bookmark, ch.date_upload, ch.date_fetch,
           COALESCE((SELECT MAX(last_read) FROM history WHERE chapter_id=ch._id),0) AS last_read
    FROM linked_children refs
    JOIN chapters ch ON ch.manga_id=refs.manga_id
    WHERE NOT EXISTS (SELECT 1 FROM excluded_scanlators ex
                      WHERE ex.manga_id=ch.manga_id AND ex.scanlator=ch.scanlator)
),
source_scores AS (
    SELECT merge_id, manga_id, MIN(priority) AS priority, MIN(first_id) AS first_id,
           COUNT(*) AS chapter_count, MAX(chapter_number) AS high_number
    FROM source_chapters
    GROUP BY merge_id,manga_id
),
most_chapters AS (
    SELECT merge_id,manga_id
    FROM (SELECT merge_id,manga_id,
                 ROW_NUMBER() OVER (PARTITION BY merge_id ORDER BY chapter_count DESC, priority, first_id, manga_id) AS rn
          FROM source_scores)
    WHERE rn=1
),
highest_number AS (
    SELECT merge_id,manga_id
    FROM (SELECT merge_id,manga_id,
                 ROW_NUMBER() OVER (PARTITION BY merge_id ORDER BY high_number DESC, priority, first_id, manga_id) AS rn
          FROM source_scores)
    WHERE rn=1
),
priority_owners AS (
    SELECT merge_id,chapter_number,manga_id
    FROM (SELECT merge_id,chapter_number,manga_id,
                 ROW_NUMBER() OVER (PARTITION BY merge_id,chapter_number ORDER BY priority,first_id,manga_id) AS rn
          FROM (SELECT DISTINCT merge_id,chapter_number,manga_id,priority,first_id
                FROM source_chapters WHERE chapter_number>=0))
    WHERE rn=1
),
selected_virtual_chapters AS (
    SELECT sc.*
    FROM source_chapters sc
    JOIN root_modes root ON root.merge_id=sc.merge_id
    LEFT JOIN most_chapters mc ON mc.merge_id=sc.merge_id AND mc.manga_id=sc.manga_id
    LEFT JOIN highest_number hn ON hn.merge_id=sc.merge_id AND hn.manga_id=sc.manga_id
    LEFT JOIN priority_owners po
       ON po.merge_id=sc.merge_id AND po.chapter_number=sc.chapter_number AND po.manga_id=sc.manga_id
    WHERE root.mode IN (0,1)
       OR (root.mode=2 AND (sc.chapter_number<0 OR po.manga_id IS NOT NULL))
       OR (root.mode=3 AND mc.manga_id IS NOT NULL)
       OR (root.mode=4 AND hn.manga_id IS NOT NULL)
       OR root.mode NOT IN (0,1,2,3,4)
),
virtual_counts AS (
    SELECT merge_id AS manga_id, COUNT(*) AS total,
           SUM(read) AS readCount,
           COALESCE(MAX(date_upload),0) AS latestUpload,
           COALESCE(MAX(last_read),0) AS lastRead,
           COALESCE(MAX(date_fetch),0) AS fetchedAt,
           SUM(bookmark) AS bookmarkCount
    FROM selected_virtual_chapters GROUP BY merge_id
)
SELECT M.*,
       COALESCE(CASE WHEN M.source=6969 THEN VC.total ELSE RC.total END,0) AS totalCount,
       COALESCE(CASE WHEN M.source=6969 THEN VC.readCount ELSE RC.readCount END,0) AS readCount,
       COALESCE(CASE WHEN M.source=6969 THEN VC.latestUpload ELSE RC.latestUpload END,0) AS latestUpload,
       COALESCE(CASE WHEN M.source=6969 THEN VC.fetchedAt ELSE RC.fetchedAt END,0) AS chapterFetchedAt,
       COALESCE(CASE WHEN M.source=6969 THEN VC.lastRead ELSE RC.lastRead END,0) AS lastRead,
       COALESCE(CASE WHEN M.source=6969 THEN VC.bookmarkCount ELSE RC.bookmarkCount END,0) AS bookmarkCount,
       COALESCE(MC.categories,'0') AS categories
FROM mangas M
LEFT JOIN real_counts RC ON RC.manga_id=M._id
LEFT JOIN virtual_counts VC ON VC.manga_id=M._id AND M.source=6969
LEFT JOIN (SELECT manga_id,group_concat(category_id) AS categories
           FROM mangas_categories GROUP BY manga_id) MC ON MC.manga_id=M._id
WHERE M.favorite=1;