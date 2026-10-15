"""SQLite host specification for the proposed atomic parent restore port.

All cases are HOST_ONLY, not the Android SQLDelight dialect/compiler.
"""
import sqlite3
import unittest
from pathlib import Path
from dataclasses import replace
import json
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from atomic_parent_restore_host import (Work, Link, commit_all_or_throw,
                                        fingerprint, MEMO_KEY)

HERE = Path(__file__).parent
A = '123e4567-e89b-42d3-a456-426614174000'
B = '123e4567-e89b-42d3-a456-426614174001'

SCHEMA = '''
CREATE TABLE mangas (
 _id INTEGER NOT NULL PRIMARY KEY,
 source INTEGER NOT NULL, url TEXT NOT NULL, artist TEXT, author TEXT,
 description TEXT, genre TEXT, title TEXT NOT NULL, status INTEGER NOT NULL,
 thumbnail_url TEXT, favorite INTEGER NOT NULL, last_update INTEGER,
 next_update INTEGER, initialized INTEGER NOT NULL,
 viewer INTEGER NOT NULL, chapter_flags INTEGER NOT NULL,
 cover_last_modified INTEGER NOT NULL, date_added INTEGER NOT NULL,
 update_strategy INTEGER NOT NULL DEFAULT 0, calculate_interval INTEGER DEFAULT 0 NOT NULL,
 last_modified_at INTEGER NOT NULL DEFAULT 0, favorite_modified_at INTEGER,
 version INTEGER NOT NULL DEFAULT 0, is_syncing INTEGER NOT NULL DEFAULT 0,
 notes TEXT NOT NULL DEFAULT '', memo BLOB NOT NULL DEFAULT '{}'
);
CREATE TABLE merged (
 _id INTEGER NOT NULL PRIMARY KEY,
 info_manga INTEGER NOT NULL, get_chapter_updates INTEGER NOT NULL,
 chapter_sort_mode INTEGER NOT NULL, chapter_priority INTEGER NOT NULL,
 download_chapters INTEGER NOT NULL, merge_id INTEGER NOT NULL,
 merge_url TEXT NOT NULL, manga_id INTEGER, manga_url TEXT NOT NULL,
 manga_source INTEGER NOT NULL,
 FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE SET NULL,
 FOREIGN KEY(merge_id) REFERENCES mangas(_id) ON DELETE CASCADE
);
'''

def db(with_indexes=True):
    c = sqlite3.connect(':memory:')
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript(SCHEMA)
    if with_indexes:
        c.executescript((HERE/'atomic_parent_restore_candidate.sql').read_text())
    c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(101,11,'/a','A',0,0,1,0,0,0,0)")
    c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(202,12,'/b','B',0,0,1,0,0,0,0)")
    c.commit()
    return c

def work(uuid=A, children=None):
    return Work(uuid, 'Shared work', tuple(children if children is not None else (
        Link(11,'/a',101,False,info=True,priority=0),
        Link(12,'/b',202,False,priority=1))))

def count(c,table):return c.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]

class AtomicRestoreHostTests(unittest.TestCase):
    def setUp(self):self.c=db();self.addCleanup(self.c.close)
    def test_new_restore_creates_one_parent_three_links_and_ledger(self):
        ids=commit_all_or_throw(self.c,[work()]);self.assertEqual(len(ids),1)
        self.assertEqual(count(self.c,'mangas'),3)
        self.assertEqual(count(self.c,'merged'),3)
        self.assertEqual(count(self.c,'polaris_restore_ledger'),1)
    def test_exact_source_keys_preserved(self):
        parent=commit_all_or_throw(self.c,[work()])[0]
        keys=self.c.execute('SELECT manga_source,manga_url FROM merged WHERE merge_id=? ORDER BY chapter_priority',(parent,)).fetchall()
        self.assertEqual(keys[:2],[(11,'/a'),(12,'/b')])
    def test_retry_same_archive_does_not_create_new_rows(self):
        first=commit_all_or_throw(self.c,[work()])
        second=commit_all_or_throw(self.c,[work()])
        self.assertEqual(first,second);self.assertEqual(count(self.c,'merged'),3)
    def test_pending_link_keeps_null_even_with_real_manga_present(self):
        pending=work(children=[Link(11,'/a',101,False), Link(12,'/b',None,True)])
        parent=commit_all_or_throw(self.c,[pending])[0]
        self.assertEqual(self.c.execute('SELECT manga_id FROM merged WHERE merge_id=? AND manga_source=12',(parent,)).fetchone()[0],None)
    def test_root_points_to_real_virtual_parent_id(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        self.assertEqual(self.c.execute('SELECT manga_id FROM merged WHERE merge_id=? AND manga_source=6969',(p,)).fetchone()[0],p)
    def test_parent_memo_contains_canonical_uuid(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        memo=self.c.execute('SELECT memo FROM mangas WHERE _id=?',(p,)).fetchone()[0]
        self.assertEqual(json.loads(memo)[MEMO_KEY],A)
    def test_two_parents_can_link_same_real_child(self):
        ids=commit_all_or_throw(self.c,[work(),work(B)])
        self.assertEqual(len(set(ids)),2);self.assertEqual(count(self.c,'merged'),6)
    def test_conflicting_archive_version_rejected_on_retry(self):
        commit_all_or_throw(self.c,[work()])
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[replace(work(),title='Changed')])
        self.assertEqual(count(self.c,'merged'),3)
    def test_deliberately_removed_link_is_not_recreated_on_retry(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        self.c.execute('DELETE FROM merged WHERE merge_id=? AND manga_source=12',(p,));self.c.commit()
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work()])
        self.assertEqual(count(self.c,'merged'),2)
    def test_corrupt_parent_uuid_rejected_on_retry(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        self.c.execute('UPDATE mangas SET memo=? WHERE _id=?',(b'{"polaris.merge.work.uuid":"different"}',p));self.c.commit()
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work()])
    def test_corrupt_parent_source_rejected_on_retry(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        self.c.execute('UPDATE mangas SET source=999 WHERE _id=?',(p,));self.c.commit()
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work()])
    def test_missing_real_child_aborts_all(self):
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work(children=[Link(12,'/b',999,False)])])
        self.assertEqual(count(self.c,'polaris_restore_ledger'),0)
    def test_mismatched_source_identity_aborts_all(self):
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work(children=[Link(88,'/b',202,False)])])
        self.assertEqual(count(self.c,'mangas'),2)
    def test_ambiguous_same_source_url_aborts_all(self):
        self.c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(303,11,'/a','dup',0,0,1,0,0,0,0)");self.c.commit()
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work()])
        self.assertEqual(count(self.c,'polaris_restore_ledger'),0)
    def test_partial_write_failure_rolls_back_parent_and_root(self):
        with self.assertRaises(RuntimeError):commit_all_or_throw(self.c,[work()],fail_after_parent=0)
        self.assertEqual(count(self.c,'mangas'),2);self.assertEqual(count(self.c,'merged'),0);self.assertEqual(count(self.c,'polaris_restore_ledger'),0)
    def test_second_parent_failure_rolls_back_first_parent_too(self):
        with self.assertRaises(RuntimeError):commit_all_or_throw(self.c,[work(),work(B)],fail_after_parent=1)
        self.assertEqual(count(self.c,'mangas'),2);self.assertEqual(count(self.c,'polaris_restore_ledger'),0)
    def test_existing_untracked_uuid_memo_requires_manual_reconcile(self):
        self.c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES(900,6969,'merged://old','old',0,1,1,0,0,0,0,?)",(json.dumps({MEMO_KEY:A}).encode(),));self.c.commit()
        with self.assertRaisesRegex(ValueError,'without ledger'):commit_all_or_throw(self.c,[work()])
        self.assertEqual(count(self.c,'polaris_restore_ledger'),0)
    def test_duplicate_uuid_within_one_batch_rejected_pretransaction(self):
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work(),work()])
        self.assertEqual(count(self.c,'mangas'),2)
    def test_malformed_uuid_rejected(self):
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work('bad')])
    def test_mismatched_pending_status_rejected(self):
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work(children=[Link(11,'/a',101,True)])])
    def test_two_metadata_sources_rejected(self):
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work(children=[Link(11,'/a',101,False,info=True),Link(12,'/b',202,False,info=True)])])
    def test_unique_source_url_index_prevents_pending_resolved_dup(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,0,2,5,0,?,?,NULL,?,?)',(p,'/parent','/a',11))
        self.c.rollback()
    def test_unique_real_id_prevents_mismatched_url_copy(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,0,2,5,0,?,?,?,?,?)',(p,'/parent',101,'/alt',88))
        self.c.rollback()
    def test_ledger_rejects_two_uuid_keys_claiming_same_parent(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(B,p,'other'))
        self.c.rollback()
    def test_foreign_key_removes_ledger_when_parent_deleted(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        self.c.execute('DELETE FROM mangas WHERE _id=?',(p,));self.c.commit()
        self.assertEqual(count(self.c,'merged'),0);self.assertEqual(count(self.c,'polaris_restore_ledger'),0)
    def test_constraint_install_fails_on_legacy_duplicate_rows(self):
        c=db(False);self.addCleanup(c.close)
        c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(900,6969,'merged://old','Old',0,1,1,0,0,0,0)")
        vals=(0,0,2,1,0,900,'merged://old',101,'/a',11)
        c.executemany('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(?,?,?,?,?,?,?,?,?,?)',[vals,vals]);c.commit()
        with self.assertRaises(sqlite3.IntegrityError):c.executescript((HERE/'atomic_parent_restore_candidate.sql').read_text())
    def test_fail_closed_when_called_inside_implicit_open_transaction(self):
        self.c.execute('INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(99,"/tmp","tmp",0,0,1,0,0,0,0)')
        with self.assertRaises(RuntimeError):commit_all_or_throw(self.c,[work()])
        self.c.rollback()
    def test_two_database_connections_importing_same_archive_create_one_parent(self):
        with TemporaryDirectory() as td:
            dbpath=str(Path(td)/'polaris.db')
            with sqlite3.connect(dbpath) as setup:
                setup.execute('PRAGMA foreign_keys=ON')
                setup.executescript(SCHEMA)
                setup.executescript((HERE/'atomic_parent_restore_candidate.sql').read_text())
                setup.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(101,11,'/a','A',0,0,1,0,0,0,0)")
                setup.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(202,12,'/b','B',0,0,1,0,0,0,0)")
            barrier=Barrier(2)
            def contender():
                c=sqlite3.connect(dbpath,timeout=10)
                try:
                    c.execute('PRAGMA foreign_keys=ON')
                    barrier.wait(timeout=5)
                    return commit_all_or_throw(c,[work()])[0]
                finally:c.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(contender);second=pool.submit(contender)
                self.assertEqual(first.result(timeout=10),second.result(timeout=10))
            with sqlite3.connect(dbpath) as verify:
                self.assertEqual(count(verify,'polaris_restore_ledger'),1)
                self.assertEqual(count(verify,'merged'),3)

    def test_two_database_connections_with_conflicting_archive_are_not_both_accepted(self):
        with TemporaryDirectory() as td:
            dbpath=str(Path(td)/'polaris.db')
            with sqlite3.connect(dbpath) as setup:
                setup.execute('PRAGMA foreign_keys=ON')
                setup.executescript(SCHEMA)
                setup.executescript((HERE/'atomic_parent_restore_candidate.sql').read_text())
                setup.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(101,11,'/a','A',0,0,1,0,0,0,0)")
                setup.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(202,12,'/b','B',0,0,1,0,0,0,0)")
            barrier=Barrier(2)
            def contender(w):
                c=sqlite3.connect(dbpath,timeout=10)
                try:
                    c.execute('PRAGMA foreign_keys=ON')
                    barrier.wait(timeout=5)
                    return commit_all_or_throw(c,[w])[0]
                finally:c.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(contender,work())
                second=pool.submit(contender,replace(work(),title='Conflicting work'))
                results=[]
                for future in [first,second]:
                    try:results.append(('success',future.result(timeout=10)))
                    except ValueError:results.append(('rejected',None))
            self.assertEqual(sorted(r[0] for r in results),['rejected','success'])
            with sqlite3.connect(dbpath) as verify:
                self.assertEqual(count(verify,'polaris_restore_ledger'),1)
                self.assertEqual(count(verify,'merged'),3)

    def test_fingerprint_stable_across_equal_objects(self):
        self.assertEqual(fingerprint(work()),fingerprint(work()))
    def test_manual_local_edit_to_priority_does_not_get_overwritten(self):
        p=commit_all_or_throw(self.c,[work()])[0]
        self.c.execute('UPDATE merged SET chapter_priority=99 WHERE merge_id=? AND manga_source=11',(p,));self.c.commit()
        with self.assertRaises(ValueError):commit_all_or_throw(self.c,[work()])
        self.assertEqual(self.c.execute('SELECT chapter_priority FROM merged WHERE merge_id=? AND manga_source=11',(p,)).fetchone()[0],99)

if __name__=='__main__':unittest.main()
