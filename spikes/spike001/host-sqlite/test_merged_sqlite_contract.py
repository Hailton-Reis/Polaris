"""Execute the actual staged Spike-001 SQLDelight migration and SQL in SQLite.

Independent offline backend contract tests; not a replacement for Android runtime.
"""
from pathlib import Path
import re
import sqlite3
import sys
import unittest

HERE = Path(__file__).resolve().parent
MIGRATION = HERE.parent / 'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm'
QUERIES = HERE.parent / 'new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq'


def named_sql(name: str) -> str:
    text = QUERIES.read_text()
    match = re.search(rf'(?ms)^{re.escape(name)}:\s*\n(.*?;)', text)
    if match is None:
        raise ValueError(f'SQLDelight query not found: {name}')
    return match.group(1)


def database():
    con = sqlite3.connect(':memory:')
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('CREATE TABLE mangas (_id INTEGER NOT NULL PRIMARY KEY, source INTEGER, url TEXT)')
    con.executemany('INSERT INTO mangas VALUES (?,?,?)', [
        (101, 7001, 'source-a'), (102, 7002, 'source-b'),
        (900, 6969, 'merged://101-102'),
    ])
    con.executescript(MIGRATION.read_text())
    return con


def insert_ref(con, child_id, source, priority=0, merge_id=900):
    return con.execute(named_sql('insertReturningId'), {
        'infoManga': 0, 'getChapterUpdates': 1, 'chapterSortMode': 2,
        'chapterPriority': priority, 'downloadChapters': 0,
        'mergeId': merge_id, 'mergeUrl': 'merged://101-102',
        'mangaId': child_id, 'mangaUrl': str(child_id), 'mangaSource': source,
    }).fetchone()[0]


def three_refs(con):
    return (
        insert_ref(con, 101, 7001, 0),
        insert_ref(con, 102, 7002, 1),
        insert_ref(con, 900, 6969, 2),
    )


class MergedSqliteContract(unittest.TestCase):
    def setUp(self):
        self.db = database()

    def tearDown(self):
        self.db.close()

    def test_schema_migration_matches_sqldelight_create_table_and_index(self):
        staged = QUERIES.read_text()
        canonical = staged.split('selectByMergeId:', 1)[0].replace('import kotlin.Boolean;', '').replace('INTEGER AS Boolean', 'INTEGER').strip()
        migration = MIGRATION.read_text().strip()
        self.assertEqual(canonical, migration)
        columns = [r[1] for r in self.db.execute('PRAGMA table_info(merged)')]
        self.assertEqual(columns, ['_id', 'info_manga', 'get_chapter_updates', 'chapter_sort_mode',
                                   'chapter_priority', 'download_chapters', 'merge_id', 'merge_url',
                                   'manga_id', 'manga_url', 'manga_source'])

    def test_parent_and_two_real_children_are_persisted(self):
        a,b,root = three_refs(self.db)
        rows = self.db.execute(named_sql('selectByMergeId'), (900,)).fetchall()
        self.assertEqual(len(rows),3)
        self.assertEqual({row[8] for row in rows}, {101,102,900})
        self.assertEqual({row[10] for row in rows}, {7001,7002,6969})
        self.assertEqual(len({a,b,root}),3)

    def test_delete_one_child_reference_keeps_b_and_parent(self):
        a,_,_ = three_refs(self.db)
        self.db.execute(named_sql('deleteById'), (a,))
        members = {r[8] for r in self.db.execute(named_sql('selectByMergeId'),(900,))}
        self.assertEqual(members, {102,900})
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas').fetchone()[0],3)

    def test_delete_virtual_parent_cascades_references_not_children(self):
        three_refs(self.db)
        self.db.execute('DELETE FROM mangas WHERE _id=900')
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged').fetchone()[0],0)
        self.assertEqual({r[0] for r in self.db.execute('SELECT _id FROM mangas')}, {101,102})

    def test_child_manga_removal_leaves_nullable_orphan_reference(self):
        three_refs(self.db)
        self.db.execute('DELETE FROM mangas WHERE _id=101')
        affected=self.db.execute('SELECT manga_id, manga_source, merge_id FROM merged WHERE manga_source=7001').fetchone()
        self.assertEqual(affected,(None,7001,900))
        self.assertEqual({r[8] for r in self.db.execute(named_sql('selectByMergeId'),(900,))}, {None,102,900})

    def test_missing_real_or_parent_fk_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            insert_ref(self.db, 9999, 7001)
        with self.assertRaises(sqlite3.IntegrityError):
            insert_ref(self.db, 101, 7001, merge_id=9999)
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged').fetchone()[0],0)

    def test_reference_transaction_rolls_back_all_entries_on_failure(self):
        self.db.commit()
        self.db.execute('BEGIN')
        with self.assertRaises(sqlite3.IntegrityError):
            insert_ref(self.db, 101, 7001)
            insert_ref(self.db, 9999, 7002)
        self.db.rollback()
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM mangas WHERE _id=900').fetchone()[0],1)

    def test_existing_null_settings_are_not_overwritten(self):
        a,_,_=three_refs(self.db)
        self.db.execute(named_sql('updateSettingsById'), {
            'id':a, 'getChapterUpdates':None, 'downloadChapters':None,
            'infoManga':None, 'chapterPriority':5, 'chapterSortMode':None,
        })
        self.assertEqual(self.db.execute('SELECT get_chapter_updates,chapter_priority,chapter_sort_mode FROM merged WHERE _id=?',(a,)).fetchone(),(1,5,2))

    def test_delete_entire_merge_removes_only_virtual_parent_with_cascade(self):
        three_refs(self.db)
        self.db.execute(named_sql('deleteByMergeId'), {'mergeId':900,'mergedSourceId':6969})
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged').fetchone()[0],0)
        self.assertEqual({r[0] for r in self.db.execute('SELECT _id FROM mangas')}, {101, 102})

    def test_select_merged_manga_join_excludes_deleted_child(self):
        three_refs(self.db)
        self.db.execute('DELETE FROM mangas WHERE _id=101')
        rows=self.db.execute(named_sql('selectMergedMangasById'),(900,)).fetchall()
        self.assertEqual({r[0] for r in rows},{102,900})


if __name__ == '__main__':
    unittest.main(verbosity=2)
