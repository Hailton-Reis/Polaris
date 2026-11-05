import sqlite3
import unittest
from pathlib import Path
SQL = (Path(__file__).parent/'libraryView_candidate.sql').read_text()
class LibraryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(':memory:')
        self.con.execute('PRAGMA foreign_keys=ON')
        self.con.executescript('''
CREATE TABLE mangas(_id INTEGER PRIMARY KEY,source INTEGER NOT NULL,favorite INTEGER NOT NULL,title TEXT NOT NULL);
CREATE TABLE chapters(_id INTEGER PRIMARY KEY,manga_id INTEGER NOT NULL,chapter_number REAL NOT NULL,read INTEGER NOT NULL,date_upload INTEGER NOT NULL,date_fetch INTEGER NOT NULL,bookmark INTEGER NOT NULL,scanlator TEXT);
CREATE TABLE excluded_scanlators(manga_id INTEGER,scanlator TEXT);
CREATE TABLE history(chapter_id INTEGER,last_read INTEGER);
CREATE TABLE mangas_categories(manga_id INTEGER,category_id INTEGER);
CREATE TABLE merged(_id INTEGER PRIMARY KEY,merge_id INTEGER NOT NULL,manga_id INTEGER,manga_source INTEGER NOT NULL,chapter_priority INTEGER NOT NULL,chapter_sort_mode INTEGER NOT NULL);
''')
        self.con.executemany('INSERT INTO mangas VALUES(?,?,?,?)',[(10,111,1,'A'),(20,222,0,'B'),(900,6969,1,'V')]);
        self.con.executemany('INSERT INTO chapters VALUES(?,?,?,?,?,?,?,?)',[(1,10,1.0,1,3,4,1,'a'),(2,10,2.0,0,5,6,0,'a'),(3,20,1.0,0,7,8,0,'b'),(4,20,3.0,0,9,10,1,'b')])
        self.con.executemany('INSERT INTO merged VALUES(?,?,?,?,?,?)',[(1,900,10,111,0,2),(2,900,20,222,1,2),(3,900,900,6969,2147483647,2)])
        self.con.executescript(SQL)
    def tearDown(self): self.con.close()
    def row(self, id=900):
        result=self.con.execute('SELECT totalCount, readCount, bookmarkCount,latestUpload,chapterFetchedAt,lastRead,categories FROM libraryView WHERE _id=?',(id,)).fetchone()
        return result
    def mode(self,mode): self.con.execute('UPDATE merged SET chapter_sort_mode=? WHERE _id=3',(mode,))
    def test_priority_dedupes_cross_source_chapter_number(self): self.assertEqual(self.row()[:3],(3,1,2))
    def test_nonvirtual_favorite_preserves_own_counts(self): self.assertEqual(self.row(10)[:3],(2,1,1))
    def test_nonfavorite_child_not_shown_as_library_work(self): self.assertIsNone(self.row(20))
    def test_no_dedupe_counts_every_original(self):
        self.mode(1);self.assertEqual(self.row()[:3],(4,1,2))
    def test_mode_none_counts_every_original(self):
        self.mode(0);self.assertEqual(self.row()[:3],(4,1,2))
    def test_most_chapters_tie_prefers_first_source(self):
        self.mode(3);self.assertEqual(self.row()[:3],(2,1,1))
    def test_highest_number_picks_source_b(self):
        self.mode(4);self.assertEqual(self.row()[:3],(2,0,1))
    def test_negative_unrecognized_numbers_from_both_sources_are_counted(self):
        self.con.executemany('INSERT INTO chapters VALUES(?,?,?,?,?,?,?,?)',[(5,10,-1,0,10,11,0,'a'),(6,20,-1,0,12,13,0,'b')]);self.assertEqual(self.row()[:3],(5,1,2))
    def test_duplicate_numbers_within_one_source_still_count(self):
        self.con.execute('INSERT INTO chapters VALUES(7,10,1.0,0,0,0,0,\'a\')');self.assertEqual(self.row()[:3],(4,1,2))
    def test_old_duplicate_links_do_not_inflate_counts(self):
        self.con.execute('INSERT INTO merged VALUES(4,900,10,111,50,2)');self.assertEqual(self.row()[:3],(3,1,2))
    def test_bookmark_progress_propagates_live(self):
        self.con.execute('UPDATE chapters SET read=1,bookmark=1 WHERE _id=4');self.assertEqual(self.row()[:3],(3,2,2))
    def test_unlink_one_child_keeps_one_source_stats(self):
        self.con.execute('DELETE FROM merged WHERE manga_id=20');self.assertEqual(self.row()[:3],(2,1,1))
    def test_missing_child_does_not_duplicate_or_break_other_stats(self):
        self.con.execute('DELETE FROM mangas WHERE _id=20');self.assertEqual(self.row()[:3],(2,1,1))
    def test_excluded_scanlator_filters_both_sources(self):
        self.con.execute("INSERT INTO excluded_scanlators VALUES(10,'a')");self.assertEqual(self.row()[:3],(2,0,1))
    def test_last_read_date_latest_fetch_and_categories(self):
        self.con.execute('INSERT INTO history VALUES(1,987)');self.con.execute('INSERT INTO mangas_categories VALUES(900,42)');self.assertEqual(self.row()[3:],(9,10,987,'42'))
    def test_source_priority_switch_updates_winner_progress(self):
        self.con.execute('UPDATE merged SET chapter_priority=-1 WHERE _id=2');self.assertEqual(self.row()[:3],(3,0,1))
    def test_root_missing_falls_back_to_no_dedupe(self):
        self.con.execute('DELETE FROM merged WHERE _id=3');self.assertEqual(self.row()[:3],(4,1,2))
    def test_only_virtual_parent_no_child_has_zero(self):
        self.con.execute('DELETE FROM merged WHERE manga_id!=900');self.assertEqual(self.row()[:3],(0,0,0))
if __name__=='__main__': unittest.main(verbosity=2)