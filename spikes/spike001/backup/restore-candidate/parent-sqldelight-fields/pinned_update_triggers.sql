-- Pinned Yomotsu commit 0fb80c439ef816eeb50674f1b90af39918b176d8
-- Relevant trigger bodies transcribed from original mangas.sq, chapters.sq
-- and mangas_categories.sq. Original source names are retained.
CREATE TRIGGER update_last_favorited_at_mangas
AFTER UPDATE OF favorite ON mangas
BEGIN
  UPDATE mangas SET favorite_modified_at = strftime('%s', 'now')
  WHERE _id = new._id;
END;
CREATE TRIGGER update_last_modified_at_mangas
AFTER UPDATE ON mangas
FOR EACH ROW
BEGIN
  UPDATE mangas SET last_modified_at = strftime('%s', 'now')
  WHERE _id = new._id;
END;
CREATE TRIGGER update_manga_version AFTER UPDATE ON mangas
BEGIN
    UPDATE mangas SET version = version + 1
    WHERE _id = new._id AND new.is_syncing = 0 AND (
        new.url != old.url OR new.description != old.description OR new.favorite != old.favorite
    );
END;
CREATE TRIGGER insert_manga_category_update_version AFTER INSERT ON mangas_categories
BEGIN
    UPDATE mangas SET version = version + 1
    WHERE _id = new.manga_id AND (SELECT is_syncing FROM mangas WHERE _id = new.manga_id) = 0;
END;
CREATE TRIGGER update_last_modified_at_chapters
AFTER UPDATE ON chapters FOR EACH ROW BEGIN
  UPDATE chapters SET last_modified_at = strftime('%s', 'now') WHERE _id = new._id;
END;
CREATE TRIGGER update_chapter_and_manga_version AFTER UPDATE ON chapters
WHEN new.is_syncing = 0 AND (
    new.read != old.read OR new.bookmark != old.bookmark OR
    new.last_page_read != old.last_page_read
)
BEGIN
    UPDATE chapters SET version = version + 1 WHERE _id = new._id;
    UPDATE mangas SET version = version + 1
    WHERE _id = new.manga_id AND (SELECT is_syncing FROM mangas WHERE _id = new.manga_id) = 0;
END;
