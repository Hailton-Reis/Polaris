"""Standalone SQLite contract for issue #11 orphan-source reattachment.

Reads the exact staged 14.sqm and merged.sq from this checkout. The candidate
queries are NOT part of production SQLDelight. A red-path diagnostic confirms
that the current INSERT would create an extra link instead of relinking NULL.
"""
from pathlib import Path
import re
import sqlite3
import unittest

HERE = Path(__file__).resolve().parent
SPIKE = HERE.parent
MIGRATION = SPIKE / 'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm'
PROD = SPIKE / 'new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq'
CANDIDATE = HERE / 'orphan_relink_candidate.sql'


def query(name, file):
    text = file.read_text()
    if file == CANDIDATE:
        match = re.search(r'(?ms)^-- name: '+re.escape(name)+r'\s*\n(.*?;)', text)
    else:
        match = re.search(r'(?ms)^'+re.escape(name)+r':\s*\n(.*?;)', text)
    if not match:
        raise ValueError(f'Missing query {name} in {file}')
    return match.group(1)


def connect():
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('CREATE TABLE mangas (_id INTEGER NOT NULL PRIMARY KEY, source INTEGER, url TEXT)')
    db.executemany('INSERT INTO mangas VALUES (?,?,?)', [
        (20, 1001, '/en'), (30, 2002, '/pt'),
        (40, 3003, '/other'), (900, 6969, 'merged://20-30'),
        (901, 6969, 'merged://40-30')
    ])
    db.executescript(MIGRATION.read_text())
    return db


def params(manga_id=None, merge_id=900, source=2002, url='/pt', priority=5):
    return dict(infoManga=0, getChapterUpdates=1, chapterSortMode=2,
                chapterPriority=priority, downloadChapters=0, mergeId=merge_id,
                mergeUrl=f'merged://{merge_id}', mangaId=manga_id,
                mangaSource=source, mangaUrl=url)


def insert(db, manga_id=None, **kwargs):
    return db.execute(query('insert', PROD), params(manga_id=manga_id, **kwargs)).rowcount


def repair(db, manga_id=30, merge_id=900, source=2002, url='/pt'):
    args = dict(resolvedMangaId=manga_id, mergeId=merge_id, childSourceId=source, childUrl=url)
    with db:
        count = db.execute(query('relinkPendingChild', CANDIDATE), args).rowcount
        removed = db.execute(query('dropRedundantPendingChildren', CANDIDATE), args).rowcount
    return count, removed


class PendingSourceRelink(unittest.TestCase):
    def setUp(self):
        self.db = connect()

    def tearDown(self):
        self.db.close()

    def rows(self, parent=900):
        return self.db.execute('SELECT manga_id, manga_source, manga_url, chapter_priority FROM merged WHERE merge_id=? ORDER BY _id',(parent,)).fetchall()

    def test_current_insert_reproduces_the_orphan_to_resolved_duplicate(self):
        insert(self.db)
        self.assertEqual(insert(self.db, 30), 1)  # Proven defect in the current DML.
        self.assertEqual([r[0] for r in self.rows()], [None,30])

    def test_candidate_reuses_existing_pending_row(self):
        insert(self.db, priority=7)
        self.assertEqual(repair(self.db), (1,0))
        self.assertEqual(self.rows(), [(30,2002,'/pt',7)])

    def test_retry_is_idempotent_and_preserves_original_priority(self):
        insert(self.db, priority=11)
        self.assertEqual(repair(self.db), (1,0))
        self.assertEqual(repair(self.db), (0,0))
        self.assertEqual(self.rows(), [(30,2002,'/pt',11)])

    def test_existing_resolved_link_triggers_orphan_cleanup(self):
        insert(self.db)
        insert(self.db,30)
        self.assertEqual(repair(self.db), (0,1))
        self.assertEqual(len(self.rows()), 1)

    def test_legacy_duplicate_orphans_collapse_to_first_reference(self):
        insert(self.db, priority=12)
        self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,1,2,88,0,900,"merged://900",NULL,"/pt",2002)')
        self.assertEqual(repair(self.db), (1,1))
        self.assertEqual(self.rows(), [(30,2002,'/pt',12)])

    def test_exact_source_identity_is_required(self):
        insert(self.db)
        self.assertEqual(repair(self.db,source=3003),(0,0))
        self.assertEqual(self.rows()[0][0],None)

    def test_exact_source_url_is_required(self):
        insert(self.db)
        self.assertEqual(repair(self.db,url='/not-pt'),(0,0))
        self.assertEqual(self.rows()[0][0],None)

    def test_manga_id_must_resolve_to_matching_real_work(self):
        insert(self.db)
        self.assertEqual(repair(self.db,manga_id=40),(0,0))
        self.assertEqual(self.rows()[0][0],None)

    def test_missing_manga_id_is_never_fabricated(self):
        insert(self.db)
        self.assertEqual(repair(self.db,manga_id=999),(0,0))
        self.assertEqual(self.rows()[0][0],None)

    def test_root_synthetic_source_cannot_be_bound_as_child(self):
        insert(self.db,source=6969,url='merged://20-30')
        self.assertEqual(repair(self.db,manga_id=900,source=6969,url='merged://20-30'),(0,0))

    def test_other_parent_is_not_modified(self):
        insert(self.db,merge_id=901)
        insert(self.db,merge_id=900)
        self.assertEqual(repair(self.db,merge_id=900),(1,0))
        self.assertEqual(self.rows(901)[0][0],None)

    def test_orphan_survives_until_source_returns(self):
        insert(self.db)
        self.assertEqual(self.rows(),[(None,2002,'/pt',5)])

    def test_child_removal_then_reappearance_can_relink(self):
        insert(self.db,manga_id=30)
        self.db.execute('DELETE FROM mangas WHERE _id=30')
        self.assertEqual(self.rows()[0][0],None)
        self.db.execute('INSERT INTO mangas VALUES(130,2002,"/pt")')
        self.assertEqual(repair(self.db,manga_id=130),(1,0))
        self.assertEqual(self.rows()[0][0],130)

    def test_deleted_virtual_parent_does_not_reappear(self):
        insert(self.db)
        self.db.execute('DELETE FROM mangas WHERE _id=900')
        self.assertEqual(repair(self.db),(0,0))
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged WHERE merge_id=900').fetchone()[0],0)


if __name__=='__main__':
    unittest.main(verbosity=2)
