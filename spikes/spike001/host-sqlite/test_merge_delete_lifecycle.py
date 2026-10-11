"""Source-scoped deletion contracts for a complete virtual work (issue #8).

Run real staged merged.sq statements against SQLite with foreign keys enabled.
"""
import sqlite3
import unittest
from test_merged_sqlite_contract import database, named_sql, three_refs, insert_ref

VIRTUAL_SOURCE = 6969


def delete_virtual(con, manga_id, source=VIRTUAL_SOURCE):
    sql = named_sql('deleteByMergeId')
    # The old query takes one positional parameter. Comparing both revisions
    # lets the test show the original behavior before the source-safe fix.
    args = {'mergeId': manga_id, 'mergedSourceId': source} if ':mergedSourceId' in sql else (manga_id,)
    con.execute(sql, args)


class DeleteEntireVirtualWorkContracts(unittest.TestCase):
    def setUp(self):
        self.db = database()

    def tearDown(self):
        self.db.close()

    def test_delete_entire_work_removes_parent_and_cascades_references(self):
        three_refs(self.db)
        delete_virtual(self.db, 900)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0], 0)
        self.assertIsNone(self.db.execute('SELECT _id FROM mangas WHERE _id=900').fetchone())
        self.assertEqual({x[0] for x in self.db.execute('SELECT _id FROM mangas')}, {101, 102})

    def test_wrong_source_disallows_deleting_virtual_parent(self):
        three_refs(self.db)
        delete_virtual(self.db, 900, source=7001)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0], 3)
        self.assertIsNotNone(self.db.execute('SELECT _id FROM mangas WHERE _id=900').fetchone())

    def test_real_manga_id_is_never_a_valid_merged_parent_to_delete(self):
        three_refs(self.db)
        insert_ref(self.db, 102, 7002, merge_id=101)
        delete_virtual(self.db, 101)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged WHERE merge_id=101').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas').fetchone()[0], 3)

    def test_repeat_delete_is_idempotent(self):
        three_refs(self.db)
        delete_virtual(self.db, 900)
        delete_virtual(self.db, 900)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0], 0)
        self.assertEqual({x[0] for x in self.db.execute('SELECT _id FROM mangas')}, {101, 102})

    def test_deleting_a_merge_preserves_unrelated_virtual_works(self):
        self.db.execute("INSERT INTO mangas VALUES (901,6969,'merged://another')")
        three_refs(self.db)
        insert_ref(self.db, 101, 7001, merge_id=901)
        delete_virtual(self.db, 900)
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE merge_id=901').fetchone()[0],101)
        self.assertEqual({x[0] for x in self.db.execute('SELECT _id FROM mangas')}, {101,102,901})

    def test_unlink_one_child_leaves_virtual_parent_and_other_child(self):
        first, _, _ = three_refs(self.db)
        self.db.execute(named_sql('deleteById'), (first,))
        self.assertEqual({x[0] for x in self.db.execute('SELECT manga_id FROM merged WHERE merge_id=900')}, {102,900})
        self.assertIsNotNone(self.db.execute('SELECT _id FROM mangas WHERE _id=900').fetchone())

    def test_new_parent_can_be_created_after_full_delete(self):
        three_refs(self.db)
        delete_virtual(self.db, 900)
        self.assertIsNone(self.db.execute("SELECT _id FROM mangas WHERE url='merged://101-102' AND source=6969").fetchone())
        self.db.execute("INSERT INTO mangas VALUES (901,6969,'merged://101-102')")
        insert_ref(self.db, 101, 7001, merge_id=901)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged WHERE merge_id=901').fetchone()[0], 1)

    def test_repository_uses_source_scoped_delete_sql(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / 'new-files/data/src/main/java/tachiyomi/data/manga/MangaMergeRepositoryImpl.kt').read_text()
        self.assertIn('import tachiyomi.domain.source.model.MERGED_SOURCE_ID', source)
        self.assertIn('deleteByMergeId(mergeId = mergeId, mergedSourceId = MERGED_SOURCE_ID)', source)

    def test_foreign_keys_are_enabled_for_cascade_claim(self):
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone()[0],1)


if __name__ == '__main__':
    unittest.main()
