"""New-parent-only, deferred-FK parent-LAST insertion; disposable SQLite only.

This is a proof of a POSSIBLE strategy, not validated Android/SQLDelight code.
"""
import sqlite3
import sys
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from test_parent_sqldelight_fields import (q,parent_params,chapter_params,M14,
                                            LEDGER,TRIGGERS,connect,UUID)


def new_db():
    c=connect();c.executescript(M14.read_text());c.executescript(LEDGER.read_text());
    c.executescript(TRIGGERS.read_text());c.commit()
    return c


def insert_child(c):
    c.execute('''INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added)
                 VALUES (101,77,'/real/101','Real',0,1,1,0,0,0,0)''')


def add_edges(c,pid,uuid,with_pending=True):
    url='merged://polaris/'+uuid
    for source, manga_url, manga_id,priority in [(77,'/real/101',101,0),
         *(([(88,'/pending',None,1)] if with_pending else [])),(6969,url,pid,999)]:
        c.execute('''INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (int(source==77),int(source==77),2,priority,0,pid,url,manga_id,manga_url,source))


def insert_reserved(c,pid,uuid=UUID,**kw):
    p=parent_params(is_syncing=0,**kw)
    p['parentId']=pid;p['destinationUrl']='merged://polaris/'+uuid
    return q(c,'insertPolarisRestoredReservedParentLast',p).fetchone()[0]


def make_full(c,pid=900,uuid=UUID,category=True,chapter=True,tracking=True,edges=True):
    if category:
        c.execute("INSERT INTO categories(_id,name,sort,flags) VALUES (91,'Read',1,0)")
        q(c,'insertPolarisRestoredCategoryExact',{'parentId':pid,'categoryId':91})
    if chapter:
        cid=q(c,'insertPolarisRestoredChapterFull',chapter_params(pid,last=6789) | {'chapterIsSyncing':0}).fetchone()[0]
        q(c,'insertPolarisRestoredHistoryExact',{'chapterId':cid,'lastRead':700,'readDuration':56})
    if tracking:
        q(c,'insertPolarisRestoredTrackExact',dict(parentId=pid,syncId=5,remoteId=456,
          libraryId=77,trackTitle='Tracked',lastChapterRead=1.5,totalChapters=3,
          trackStatus=2,trackScore=8.25,remoteUrl='/t',startDate=1,finishDate=2,isPrivate=0))
    q(c,'insertPolarisRestoredExclusionExact',{'parentId':pid,'excludedScanlator':'HIDE'})
    if edges:add_edges(c,pid,uuid)
    c.execute('INSERT INTO polaris_restore_ledger(archive_uuid,parent_manga_id,archive_digest) VALUES(?,?,?)',(uuid,pid,'0'*64))
    insert_reserved(c,pid,uuid)


class ParentLastDeferredFkTest(unittest.TestCase):
    def setUp(self):self.db=new_db();self.addCleanup(self.db.close);insert_child(self.db);self.db.commit()
    def begin(self,defer=True):
        self.db.execute('BEGIN IMMEDIATE')
        if defer:self.db.execute('PRAGMA defer_foreign_keys=ON')
    def restore(self, pid=900, uuid=UUID):
        self.begin()
        make_full(self.db,pid,uuid)
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.db.commit()

    def test_01_foreign_keys_are_enabled_in_original_schema(self):
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone(),(1,))

    def test_02_deferred_constraints_are_opt_in_for_one_transaction(self):
        self.begin()
        self.assertEqual(self.db.execute('PRAGMA defer_foreign_keys').fetchone(),(1,))
        self.db.rollback()
        self.assertEqual(self.db.execute('PRAGMA defer_foreign_keys').fetchone(),(0,))

    def test_03_future_parent_fk_would_fail_without_deferral(self):
        self.begin(defer=False)
        self.db.execute("INSERT INTO categories(_id,name,sort,flags) VALUES(91,'Read',1,0)")
        with self.assertRaises(sqlite3.IntegrityError):
            q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':900,'categoryId':91})
        self.db.rollback()

    def test_04_category_trigger_noop_before_parent_exists(self):
        self.begin();self.db.execute("INSERT INTO categories(_id,name,sort,flags) VALUES(91,'Read',1,0)")
        q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':900,'categoryId':91})
        self.assertEqual(self.db.execute('SELECT count(*) FROM mangas WHERE _id=900').fetchone(),(0,))
        insert_reserved(self.db,900)
        self.assertEqual(self.db.execute('SELECT version,last_modified_at,is_syncing FROM mangas WHERE _id=900').fetchone(),(7,123456789,0))
        self.db.commit()

    def test_05_full_parent_child_history_memo_version_exact_after_commit(self):
        self.restore()
        r=self.db.execute('SELECT notes,last_modified_at,version,is_syncing,memo FROM mangas WHERE _id=900').fetchone()
        self.assertEqual(r[:4],('Archive notes',123456789,7,0))
        self.assertIn(b'"custom"',r[4]);self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.assertEqual(self.db.execute('SELECT last_modified_at,is_syncing FROM chapters').fetchone(),(6789,0))

    def test_06_no_parent_update_trigger_fired_for_new_record(self):
        self.restore();self.assertEqual(self.db.execute('SELECT favorite_modified_at FROM mangas WHERE _id=900').fetchone(),(180,))

    def test_07_category_readback_matches_archive_destination_id(self):
        self.restore();self.assertEqual(q(self.db,'selectPolarisParentCategoriesFull',{'parentId':900}).fetchall(),[(91,)])

    def test_08_history_and_tracking_use_parent_id_after_commit(self):
        self.restore()
        self.assertEqual(q(self.db,'selectPolarisParentHistoryFull',{'parentId':900}).fetchone()[-2:],(700,56))
        self.assertEqual(q(self.db,'selectPolarisParentTrackingFull',{'parentId':900}).fetchone()[1],900)

    def test_09_pending_child_keeps_null_link_on_commit(self):
        self.restore();self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE manga_source=88').fetchone(),(None,))

    def test_10_self_root_and_real_edges_are_same_parent(self):
        self.restore()
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE manga_source=6969').fetchone(),(900,))
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE manga_source=77').fetchone(),(101,))

    def test_11_second_parent_failure_rolls_back_first(self):
        self.begin();make_full(self.db,900)
        with self.assertRaises(sqlite3.IntegrityError):insert_reserved(self.db,900,notes='duplicate')
        self.db.rollback()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas WHERE _id=900').fetchone(),(0,))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas_categories').fetchone(),(0,))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone(),(0,))

    def test_12_missing_parent_cannot_commit_even_with_defer_fk(self):
        self.begin();self.db.execute("INSERT INTO categories(_id,name,sort,flags) VALUES(91,'Read',1,0)")
        q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':900,'categoryId':91})
        with self.assertRaises(sqlite3.IntegrityError):self.db.commit()
        self.db.rollback()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas_categories').fetchone(),(0,))

    def test_13_existing_row_id_cannot_be_automatically_overwritten(self):
        self.db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(900,77,"/someone","Existing",0,1,1,0,0,0,0)')
        self.db.commit();self.begin()
        with self.assertRaises(sqlite3.IntegrityError):insert_reserved(self.db,900)
        self.db.rollback()
        self.assertEqual(self.db.execute('SELECT title FROM mangas WHERE _id=900').fetchone(),('Existing',))

    def test_14_transaction_commit_resets_defer_setting(self):
        self.restore();self.assertEqual(self.db.execute('PRAGMA defer_foreign_keys').fetchone(),(0,))

    def test_15_readback_rejects_post_restore_local_edit(self):
        self.restore()
        self.db.execute('UPDATE mangas SET notes=? WHERE _id=900',('edited',))
        self.assertNotEqual(self.db.execute('SELECT notes,last_modified_at FROM mangas WHERE _id=900').fetchone(),('Archive notes',123456789))

    def test_16_deferred_pending_parent_edges_cannot_resolve_to_wrong_source_id(self):
        self.restore()
        self.db.execute('DELETE FROM mangas WHERE _id=101')
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE manga_source=77').fetchone(),(None,))
        self.assertEqual(self.db.execute('SELECT _id FROM mangas WHERE _id=900').fetchone(),(900,))


if __name__=='__main__':unittest.main()
