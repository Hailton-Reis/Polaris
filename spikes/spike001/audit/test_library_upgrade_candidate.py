"""Candidate SQLite view upgrade; DOES NOT modify deployed Spike-001 or migration14."""
import sqlite3
import unittest
from pathlib import Path
P=Path(__file__).resolve().parent
PINNED=(P/'libraryView.pinned.sq').read_text().split('\nlibrary:\n',1)[0]
CREATION=(P.parent/'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm').read_text()
UPGRADE=(P/'migration14_view_candidate.sql').read_text()
class UpgradeTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''CREATE TABLE mangas(_id INTEGER PRIMARY KEY,source INTEGER NOT NULL,favorite INTEGER NOT NULL,title TEXT NOT NULL);
CREATE TABLE chapters(_id INTEGER PRIMARY KEY,manga_id INTEGER,chapter_number REAL,read INTEGER,date_upload INTEGER,date_fetch INTEGER,bookmark INTEGER,scanlator TEXT);
CREATE TABLE excluded_scanlators(manga_id INTEGER,scanlator TEXT);
CREATE TABLE history(chapter_id INTEGER,last_read INTEGER);
CREATE TABLE mangas_categories(manga_id INTEGER,category_id INTEGER);
''')
        self.db.executescript(PINNED)
        self.db.executemany('INSERT INTO mangas VALUES(?,?,?,?)',[(10,111,1,'A'),(20,222,0,'B'),(900,6969,1,'V')])
        self.db.executemany('INSERT INTO chapters VALUES(?,?,?,?,?,?,?,?)',[(1,10,1,1,1,1,0,'a'),(2,20,2,0,2,2,1,'b')])
    def tearDown(self): self.db.close()
    def apply(self):
        self.db.executescript(CREATION)
        self.db.executemany("""INSERT INTO merged (info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES (0,1,2,?,0,900,'merged://',?, 'u',?)""",[(0,10,111),(1,20,222),(999,900,6969)])
        self.db.executescript(UPGRADE)
    def get(self,id):return self.db.execute('SELECT totalCount,readCount,bookmarkCount FROM libraryView WHERE _id=?',(id,)).fetchone()
    def test_pinned_view_shows_zero_for_virtual_parent(self):self.assertEqual(self.get(900),(0,0,0))
    def test_upgrade_corrects_virtual_counts(self):self.apply();self.assertEqual(self.get(900),(2,1,1))
    def test_upgrade_does_not_change_real_manga_rows(self):
        before=self.db.execute('SELECT * FROM mangas ORDER BY _id').fetchall()
        self.apply();self.assertEqual(self.db.execute('SELECT * FROM mangas ORDER BY _id').fetchall(),before)
    def test_upgrade_does_not_change_chapter_rows(self):
        before=self.db.execute('SELECT * FROM chapters ORDER BY _id').fetchall()
        self.apply();self.assertEqual(self.db.execute('SELECT * FROM chapters ORDER BY _id').fetchall(),before)
    def test_view_columns_are_identical_after_upgrade(self):
        before=[x[1] for x in self.db.execute('PRAGMA table_info(libraryView)')]
        self.apply();after=[x[1] for x in self.db.execute('PRAGMA table_info(libraryView)')];self.assertEqual(before,after)
    def test_nonvirtual_favorite_unchanged_by_upgrade(self):
        before=self.get(10);self.apply();self.assertEqual(self.get(10),before)
    def test_no_extra_migration_15_is_required_in_candidate(self):
        self.assertNotIn('ALTER TABLE',UPGRADE.upper());self.assertIn('DROP VIEW IF EXISTS libraryView;',UPGRADE)
if __name__=='__main__':unittest.main()