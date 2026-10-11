"""Contracts for atomic idempotent reference inserts (not a DB uniqueness constraint).

These execute the *real staged SQLDelight SQL* on SQLite, not mock SQL strings.
"""
import unittest
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from test_merged_sqlite_contract import database, named_sql, insert_ref


class MergeInsertIdempotency(unittest.TestCase):
    def setUp(self):
        self.db = database()

    def tearDown(self):
        self.db.close()

    def params(self, manga_id=101, source=7001, url='101', merge_id=900, priority=0):
        return {
            'infoManga': 0, 'getChapterUpdates': 1, 'chapterSortMode': 2,
            'chapterPriority': priority, 'downloadChapters': 0,
            'mergeId': merge_id, 'mergeUrl': 'merged://101-102',
            'mangaId': manga_id, 'mangaUrl': url, 'mangaSource': source,
        }

    def count(self):
        return self.db.execute('SELECT count(*) FROM merged').fetchone()[0]

    def test_single_insert_replay_is_a_noop(self):
        p = self.params()
        first = self.db.execute(named_sql('insertReturningId'), p).fetchone()
        second = self.db.execute(named_sql('insertReturningId'), p).fetchone()
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(self.count(), 1)

    def test_batch_query_replay_is_idempotent(self):
        for _ in range(3):
            with self.db:
                for p in [self.params(), self.params(102, 7002, '102'), self.params(900,6969,'merged://101-102')]:
                    self.db.execute(named_sql('insert'), p)
        self.assertEqual(self.count(),3)

    def test_existing_priority_and_settings_are_preserved(self):
        p = self.params(priority=1)
        self.db.execute(named_sql('insert'), p)
        self.db.execute(named_sql('insert'), self.params(priority=999))
        self.assertEqual(self.db.execute('SELECT chapter_priority FROM merged').fetchone()[0],1)

    def test_different_children_still_insert(self):
        self.db.execute(named_sql('insert'), self.params())
        self.db.execute(named_sql('insert'), self.params(102, 7002,'102'))
        self.assertEqual(self.count(),2)

    def test_delete_single_reference_allows_future_relink(self):
        ref = self.db.execute(named_sql('insertReturningId'), self.params()).fetchone()[0]
        self.db.execute(named_sql('deleteById'),(ref,))
        second = self.db.execute(named_sql('insertReturningId'), self.params()).fetchone()
        self.assertIsNotNone(second)
        self.assertEqual(self.count(),1)

    def test_deleted_child_orphan_retries_match_nullable_source_url(self):
        self.db.execute(named_sql('insert'), self.params())
        self.db.execute('DELETE FROM mangas WHERE _id=101')
        self.assertIsNone(self.db.execute('SELECT manga_id FROM merged').fetchone()[0])
        self.db.execute(named_sql('insert'),self.params(None,7001,'101'))
        self.assertEqual(self.count(),1)

    def test_distinct_orphan_urls_can_coexist(self):
        self.db.execute(named_sql('insert'),self.params(None,7001,'old-url'))
        self.db.execute(named_sql('insert'),self.params(None,7001,'new-url'))
        self.assertEqual(self.count(),2)

    def test_same_child_id_new_url_is_still_a_noop(self):
        self.db.execute(named_sql('insert'),self.params())
        self.db.execute(named_sql('insert'),self.params(101,7001,'new-manga-url'))
        self.assertEqual(self.count(),1)

    def test_multiple_sqlite_connections_write_same_child_at_most_once(self):
        # SQLite host race exercise with separate connections and no Python lock;
        # Android's bundled driver concurrency still needs on-device validation.
        self.db.commit()
        with tempfile.TemporaryDirectory() as tmp:
            name = str(Path(tmp) / 'shared.sqlite')
            with __import__('sqlite3').connect(name) as disk:
                self.db.backup(disk)
            barrier = Barrier(4)
            def worker(i):
                with __import__('sqlite3').connect(name, timeout=10, isolation_level=None) as con:
                    con.execute('PRAGMA busy_timeout = 10000')
                    barrier.wait(timeout=5)
                    con.execute(named_sql('insert'), self.params(priority=i))
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(worker, range(4)))
            with __import__('sqlite3').connect(name) as final:
                self.assertEqual(final.execute('SELECT count(*) FROM merged').fetchone()[0], 1)

    def test_different_parent_work_keeps_separate_membership(self):
        self.db.execute("INSERT INTO mangas VALUES (901,6969,'merged://other')")
        self.db.execute(named_sql('insert'),self.params())
        self.db.execute(named_sql('insert'),self.params(merge_id=901))
        self.assertEqual(self.count(),2)


if __name__ == '__main__':
    unittest.main()
