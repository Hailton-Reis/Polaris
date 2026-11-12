"""Test source-variant selection against the real SQLDelight merged.sq queries."""
import unittest
from test_merged_sqlite_contract import database, insert_ref, named_sql


class MergeSelectIntegrity(unittest.TestCase):
    def setUp(self):
        self.db = database()

    def tearDown(self):
        self.db.close()

    def members(self, merge_id=900):
        return self.db.execute(named_sql('selectMergedMangasById'), (merge_id,)).fetchall()

    def ids(self, merge_id=900):
        return [m[0] for m in self.members(merge_id)]

    def test_duplicate_child_link_does_not_duplicate_work(self):
        insert_ref(self.db, 101, 7001)
        # Legacy duplicate/corrupt record bypasses idempotent INSERT guarded SQL.
        self.db.execute("""INSERT INTO merged (
            info_manga, get_chapter_updates, chapter_sort_mode, chapter_priority,
            download_chapters, merge_id, merge_url, manga_id, manga_url, manga_source
            ) SELECT info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,
            download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source
            FROM merged LIMIT 1""")
        insert_ref(self.db, 102, 7002)
        insert_ref(self.db, 900, 6969)
        self.assertEqual(self.ids(), [101,102,900])

    def test_uses_explicit_chapter_priority_not_insert_order(self):
        insert_ref(self.db, 900,6969,priority=500)
        insert_ref(self.db,102,7002,priority=2)
        insert_ref(self.db,101,7001,priority=0)
        self.assertEqual(self.ids(),[101,102,900])

    def test_equal_priority_tie_breaks_by_first_reference_id(self):
        insert_ref(self.db,102,7002,priority=1)
        insert_ref(self.db,101,7001,priority=1)
        self.assertEqual(self.ids(),[102,101])

    def test_missing_real_child_is_excluded_but_root_kept(self):
        insert_ref(self.db,101,7001)
        insert_ref(self.db,102,7002)
        insert_ref(self.db,900,6969)
        self.db.execute('DELETE FROM mangas WHERE _id=101')
        self.assertEqual(self.ids(),[102,900])

    def test_other_virtual_parent_links_do_not_leak(self):
        self.db.execute("INSERT INTO mangas VALUES (901,6969,'other')")
        insert_ref(self.db,101,7001)
        insert_ref(self.db,102,7002,merge_id=901)
        self.assertEqual(self.ids(),[101])
        self.assertEqual(self.ids(901),[102])

    def test_updating_reference_priority_reorders_selection(self):
        r1=insert_ref(self.db,101,7001,priority=5)
        r2=insert_ref(self.db,102,7002,priority=10)
        self.assertEqual(self.ids(),[101,102])
        self.db.execute("UPDATE merged SET chapter_priority=1 WHERE _id=?",(r2,))
        self.assertEqual(self.ids(),[102,101])

    def test_duplicate_root_does_not_duplicate_virtual_parent(self):
        insert_ref(self.db,900,6969,priority=100)
        self.db.execute("""INSERT INTO merged (
            info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,
            download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source)
            SELECT info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,
            download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source
            FROM merged LIMIT 1""")
        self.assertEqual(self.ids(),[900])


if __name__ == '__main__':
    unittest.main()
