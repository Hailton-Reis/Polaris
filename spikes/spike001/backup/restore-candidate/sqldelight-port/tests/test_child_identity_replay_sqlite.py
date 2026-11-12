"""Regression evidence for UUID-ledger replay vs real SQLite row identity.

These tests execute the staged SQLDelight-labelled query against SQLite, NOT
SQLDelight Kotlin code-generation. No production DB is ever opened.
"""
from pathlib import Path
import re
import sqlite3
import unittest

CANDIDATE = Path(__file__).resolve().parents[1] / 'sql-candidate' / 'polarisRestore.sq'
parts = re.split(r'(?m)^([a-zA-Z]\w*):\s*\n', CANDIDATE.read_text())
DDL = parts[0]
QUERIES = {parts[i].strip(): parts[i+1].strip() for i in range(1, len(parts), 2)}
SCHEMA = '''
CREATE TABLE mangas (_id INTEGER PRIMARY KEY, source INTEGER NOT NULL,
    url TEXT NOT NULL, title TEXT NOT NULL, status INTEGER NOT NULL,
    favorite INTEGER NOT NULL, initialized INTEGER NOT NULL,
    viewer INTEGER NOT NULL, chapter_flags INTEGER NOT NULL,
    cover_last_modified INTEGER NOT NULL, date_added INTEGER NOT NULL,
    memo BLOB NOT NULL DEFAULT '{}');
CREATE TABLE merged (_id INTEGER PRIMARY KEY, info_manga INTEGER NOT NULL,
    get_chapter_updates INTEGER NOT NULL, chapter_sort_mode INTEGER NOT NULL,
    chapter_priority INTEGER NOT NULL, download_chapters INTEGER NOT NULL,
    merge_id INTEGER NOT NULL, merge_url TEXT NOT NULL, manga_id INTEGER,
    manga_url TEXT NOT NULL, manga_source INTEGER NOT NULL,
    FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE SET NULL,
    FOREIGN KEY(merge_id) REFERENCES mangas(_id) ON DELETE CASCADE);
'''


def new_database():
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript(SCHEMA + DDL)
    for manga_id, source, url in ((101, 11, '/a'), (202, 12, '/b'), (900, 6969, 'merged://polaris/u')):
        conn.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                     (manga_id, source, url, 'manga', 0, 1, 1, 0, 0, 0, 0))
    conn.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)', ('u', 900, 'fingerprint'))
    conn.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,1,2,0,0,900,\'merged://polaris/u\',101,\'/a\',11)')
    conn.commit()
    return conn


def source_ids(conn, source=11, url='/a'):
    return [row[0] for row in conn.execute(QUERIES['selectAllExactSourceChildIds'], dict(sourceId=source, sourceUrl=url))]


class ReplayIdentitySqliteTests(unittest.TestCase):
    def setUp(self):
        self.db = new_database()
        self.addCleanup(self.db.close)

    def test_original_child_id_is_exactly_one_row(self):
        self.assertEqual(source_ids(self.db), [101])

    def test_same_ledger_after_real_url_mutation_has_stale_edge(self):
        self.db.execute("UPDATE mangas SET url='/moved' WHERE _id=101")
        self.assertEqual(source_ids(self.db), [])
        self.assertEqual(self.db.execute('SELECT manga_id,manga_url FROM merged WHERE manga_source=11').fetchone(), (101, '/a'))
        self.assertEqual(self.db.execute('SELECT parent_manga_id FROM polaris_restore_ledger').fetchone(), (900,))

    def test_same_ledger_after_real_source_change_has_stale_edge(self):
        self.db.execute('UPDATE mangas SET source=98 WHERE _id=101')
        self.assertEqual(source_ids(self.db), [])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged WHERE merge_id=900').fetchone(), (1,))

    def test_child_deletion_nullifies_fk_but_does_not_delete_parent_ledger(self):
        self.db.execute('DELETE FROM mangas WHERE _id=101')
        self.assertEqual(source_ids(self.db), [])
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE merge_id=900').fetchone(), (None,))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone(), (1,))

    def test_source_identity_query_exposes_ambiguous_rows_not_arbitrary_first(self):
        self.db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(303,11,\'/a\',\'duplicate\',0,0,1,0,0,0,0)')
        self.assertEqual(source_ids(self.db), [101, 303])

    def test_pending_link_does_not_automatically_rebind_after_real_arrives(self):
        self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,0,2,1,0,900,\'merged://polaris/u\',NULL,\'/future\',25)')
        self.db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(333,25,\'/future\',\'new\',0,0,1,0,0,0,0)')
        self.assertEqual(source_ids(self.db, 25, '/future'), [333])
        self.assertIsNone(self.db.execute('SELECT manga_id FROM merged WHERE manga_source=25').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
