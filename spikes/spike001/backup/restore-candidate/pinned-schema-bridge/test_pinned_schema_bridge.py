"""Native-shaped pinned Yomotsu schema + isolated Polaris merge bridge checks."""
import copy
import json
import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'full-parent-sqlite'))
from test_atomic_full_parent_v2_host import sample,U1,U2
from pinned_schema_fixture import connect,columns,tables,ORIGIN,SOURCE_BLOBS
from native_restore_sql import open_db,restore

def converted(uid=U1, real_id=101, real_url='/source/1'):
    w=sample(uid)
    w['snapshot']['updateStrategy']=0
    w['edges'][0]['real_id']=real_id
    w['edges'][0]['url']=real_url
    w['edges'][0]['settings']={'infoManga':True,'getChapterUpdates':True,'chapterSortMode':2,'chapterPriority':1,'downloadChapters':False}
    w['edges'][1]['settings']={'infoManga':False,'getChapterUpdates':True,'chapterSortMode':0,'chapterPriority':10,'downloadChapters':False}
    return w

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.db=open_db()
        self.db.execute("INSERT INTO categories(_id,name,sort,flags) VALUES(91,'Read',1,0),(92,'Favorite',2,0)")
        self.db.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES (101,77,'/source/1','Real',0,1,1,0,0,0,0)")
        self.db.commit()
        self.work=converted()
        self.orders={4:'Read',7:'Favorite'}
    def tearDown(self):self.db.close()
    def apply(self,works=None,orders=None,**options):
        return restore(self.db,[self.work] if works is None else works,self.orders if orders is None else orders,**options)
    def count(self,table):return self.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
    def test_01_pinned_sha_is_fixed(self):
        self.assertEqual(len(ORIGIN),40)
        self.assertEqual(len(SOURCE_BLOBS),7)
        self.assertTrue(all(len(h)==40 for h in SOURCE_BLOBS.values()))
    def test_02_upstream_native_schema_has_no_merged_table(self):
        c=connect();self.assertNotIn('merged',tables(c));self.assertNotIn('polaris_restore_ledger',tables(c));c.close()
    def test_03_staged_select_from_merged_fails_before_bridge(self):
        c=connect()
        with self.assertRaisesRegex(sqlite3.OperationalError,'no such table: merged'):
            c.execute('SELECT * FROM merged LIMIT 1')
        c.close()
    def test_04_bridge_adds_missing_tables_only(self):
        self.assertIn('merged',tables(self.db))
        self.assertIn('polaris_restore_ledger',tables(self.db))
        self.assertNotIn('payload_json',columns(self.db,'mangas'))
        self.assertNotIn('memo_b64',columns(self.db,'mangas'))
    def test_05_native_mangas_has_original_columns(self):
        names=columns(self.db,'mangas')
        for key in ('favorite_modified_at','update_strategy','notes','memo','is_syncing','genre','viewer','version'):
            self.assertIn(key,names)
    def test_06_native_chapters_has_original_columns(self):
        for key in ('last_page_read','chapter_number','bookmark','memo','last_modified_at','source_order'):
            self.assertIn(key,columns(self.db,'chapters'))
    def test_07_category_uses_sort_column_not_order(self):
        self.assertIn('sort',columns(self.db,'categories'))
        self.assertNotIn('order',columns(self.db,'categories'))
    def test_08_native_tracking_table_is_manga_sync(self):
        self.assertNotIn('tracking',tables(self.db));self.assertIn('manga_sync',tables(self.db))
    def test_09_history_refs_chapter_id_not_parent_id(self):
        self.assertIn('chapter_id',columns(self.db,'history'))
        self.assertNotIn('manga_id',columns(self.db,'history'))
    def test_10_missing_ledger_fkey_is_refused(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO polaris_restore_ledger VALUES('uuid',-999,'bad')")
        self.db.rollback()
    def test_11_full_parent_native_columns_and_uuid_url(self):
        pid=self.apply()[0]
        v=self.db.execute('SELECT source,url,title,notes,viewer,chapter_flags,update_strategy,version,artist,author,description,genre,status,thumbnail_url,favorite,date_added,last_modified_at,favorite_modified_at FROM mangas WHERE _id=?',(pid,)).fetchone()
        self.assertEqual(v,(6969,'merged://polaris/'+U1,'Português 漫画','Keep this note!',9,8,0,4,'A','B','Preserve original','Action, Drama',2,'https://example.invalid/cover',1,14,22,23))
    def test_12_memo_retains_unknown_user_keys(self):
        pid=self.apply()[0]
        m=json.loads(self.db.execute('SELECT memo FROM mangas WHERE _id=?',(pid,)).fetchone()[0])
        self.assertEqual(m['nested'],{'hello':'world'});self.assertEqual(m['user.key'],'important');self.assertEqual(m['polaris.merge.work.uuid'],U1)
    def test_13_chapter_progress_and_bookmark_real_columns(self):
        pid=self.apply()[0]
        v=self.db.execute('SELECT url,name,read,bookmark,last_page_read,source_order,date_fetch,date_upload,version,memo FROM chapters WHERE manga_id=?',(pid,)).fetchone()
        self.assertEqual(v[:9],('/chapter1','Chapter One',1,1,19,4,10,20,1));self.assertEqual(json.loads(v[-1])['chapter.extra'],'value')
    def test_14_history_matches_actual_inserted_chapter(self):
        pid=self.apply()[0]
        self.assertEqual(self.db.execute('SELECT c.url,h.last_read,h.time_read FROM history h JOIN chapters c ON c._id=h.chapter_id WHERE c.manga_id=?',(pid,)).fetchone(),('/chapter1',123456,99))
    def test_15_real_manga_sync_fields(self):
        pid=self.apply()[0]
        self.assertEqual(self.db.execute('SELECT sync_id,remote_id,library_id,last_chapter_read,score,private FROM manga_sync WHERE manga_id=?',(pid,)).fetchone(),(2,42,11,2.5,8.5,0))
    def test_16_replay_does_not_duplicate_full_parent(self):
        pid=self.apply()[0];self.assertEqual(self.apply()[0],pid)
        for table,n in [('polaris_restore_ledger',1),('manga_sync',1),('history',1),('chapters',1),('merged',2),('mangas_categories',2)]:self.assertEqual(self.count(table),n,table)
    def test_17_pending_source_kept_null(self):
        pid=self.apply()[0]
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE merge_id=? AND manga_source=88',(pid,)).fetchone(),(None,))
    def test_18_replay_refuses_modified_user_note(self):
        pid=self.apply()[0];self.db.execute("UPDATE mangas SET notes='user edit' WHERE _id=?",(pid,));self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_19_replay_refuses_changed_chapter_progress(self):
        self.apply();self.db.execute('UPDATE chapters SET last_page_read=100');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_20_replay_refuses_missing_history(self):
        self.apply();self.db.execute('DELETE FROM history');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_21_replay_refuses_detached_source_link(self):
        self.apply();self.db.execute('DELETE FROM merged WHERE manga_source=77');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_22_replay_refuses_changed_child_source_id(self):
        self.apply();self.db.execute('UPDATE mangas SET source=111 WHERE _id=101');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_23_category_order_name_missing_refused(self):
        with self.assertRaises(ValueError):self.apply(orders={4:'Read',7:'Missing'})
    def test_24_duplicate_destination_category_name_refused(self):
        self.db.execute("INSERT INTO categories(_id,name,sort,flags) VALUES(99,'Read',99,0)");self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_25_second_parent_rollback_all_native_relations(self):
        second=converted(U2,102,'/source/2')
        self.db.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES (102,77,'/source/2','Two',0,1,1,0,0,0,0)");self.db.commit()
        with self.assertRaises(RuntimeError):self.apply([self.work,second],fail_after_parent=1)
        self.assertEqual(self.count('polaris_restore_ledger'),0)
        for t in ['history','chapters','mangas_categories','manga_sync','merged','excluded_scanlators']:self.assertEqual(self.count(t),0,t)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas WHERE source=6969').fetchone()[0],0)
    def test_26_full_parent_readback_failure_rolls_back(self):
        bad=copy.deepcopy(self.work);bad['snapshot']['history']=[{'url':'/not-present','lastRead':1,'readDuration':1}]
        with self.assertRaises(ValueError):self.apply([bad])
        self.assertEqual(self.count('polaris_restore_ledger'),0)
    def test_27_duplicate_merged_key_refused_by_index(self):
        pid=self.apply()[0]
        row=self.db.execute('SELECT info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source FROM merged WHERE merge_id=? LIMIT 1',(pid,)).fetchone()
        with self.assertRaises(sqlite3.IntegrityError):self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES (?,?,?,?,?,?,?,?,?,?)',row)
        self.db.rollback()
    def test_28_parent_deletion_cascades_ledger_and_edges(self):
        pid=self.apply()[0];self.db.execute('DELETE FROM mangas WHERE _id=?',(pid,));self.db.commit()
        for t in ['polaris_restore_ledger','merged','chapters','history','manga_sync','mangas_categories']:
            self.assertEqual(self.count(t),0,t)
    def test_29_real_child_deletion_sets_link_pending_id_null(self):
        pid=self.apply()[0];self.db.execute('DELETE FROM mangas WHERE _id=101');self.db.commit()
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged WHERE merge_id=? AND manga_source=77',(pid,)).fetchone(),(None,))
        with self.assertRaises(ValueError):self.apply()
    def test_30_ambiguous_real_source_url_refused(self):
        self.db.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES (102,77,'/source/1','Duplicate',0,1,1,0,0,0,0)");self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_31_unknown_archived_memo_uuid_rejected(self):
        import base64
        w=copy.deepcopy(self.work)
        w['snapshot']['memo_b64']=base64.b64encode(b'{"polaris.merge.work.uuid":"foreign"}').decode()
        with self.assertRaises(ValueError):self.apply([w])
    def test_32_genre_list_with_delimiter_rejected_fail_closed(self):
        w=copy.deepcopy(self.work);w['snapshot']['genre']=['Action, Drama']
        with self.assertRaisesRegex(ValueError,'Genre cannot be represented losslessly'):self.apply([w])
    def test_33_ledger_uuid_collision_rejected(self):
        self.apply();self.db.execute("UPDATE polaris_restore_ledger SET archive_digest='edited'");self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_34_legacy_memo_uuid_collision_refused(self):
        self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES (6969,'legacy://1','Legacy',0,1,1,0,0,0,0,?)",(json.dumps({'polaris.merge.work.uuid':U1}).encode(),));self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_35_ledger_parent_id_enforced_unique(self):
        pid=self.apply()[0]
        with self.assertRaises(sqlite3.IntegrityError):self.db.execute('INSERT INTO polaris_restore_ledger VALUES (?,?,?)',(U2,pid,'hash'))
        self.db.rollback()
    def test_36_no_extra_json_fixture_columns_in_any_table(self):
        for t in ['mangas','chapters','history','manga_sync','categories','excluded_scanlators']:
            self.assertTrue('payload_json' not in columns(self.db,t),t)
    def test_37_missing_categories_refused_without_partial_insert(self):
        with self.assertRaises(ValueError):self.apply(orders={4:'Read',7:'Absent'})
        self.assertEqual(self.count('polaris_restore_ledger'),0)
    def test_38_manga_sync_unique_constraint_replaces_existing_track(self):
        pid=self.apply()[0]
        self.db.execute('INSERT INTO manga_sync(manga_id,sync_id,remote_id,title,last_chapter_read,total_chapters,status,score,remote_url,start_date,finish_date) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(pid,2,43,'Changed',1,1,1,1,'x',1,1))
        self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_39_stage_index_duplicate_real_manga_reference(self):
        pid=self.apply()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,1,0,0,0,?,?,?,\'/other\',999)',(pid,'merged://polaris/'+U1,101))
        self.db.rollback()
    def test_40_typed_memo_json_byte_container_preserved(self):
        self.apply(); blob=self.db.execute('SELECT memo FROM mangas WHERE source=6969').fetchone()[0]
        self.assertIsInstance(blob,(bytes,bytearray))
    def test_41_composite_category_fk_enforced(self):
        pid=self.apply()[0]
        with self.assertRaises(sqlite3.IntegrityError):self.db.execute('INSERT INTO mangas_categories(manga_id,category_id) VALUES(?,?)',(pid,999999))
        self.db.rollback()
    def test_42_missing_child_history_strict(self):
        w=copy.deepcopy(self.work);w['snapshot']['chapters']=[]
        with self.assertRaises(ValueError):self.apply([w])
    def test_43_readback_catches_modified_tracker(self):
        self.apply();self.db.execute('UPDATE manga_sync SET last_chapter_read=999');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_44_readback_catches_modified_scanlator_exclusion(self):
        self.apply();self.db.execute('DELETE FROM excluded_scanlators');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_45_replay_detects_modified_chapter_last_modified_at(self):
        self.apply();self.db.execute('UPDATE chapters SET last_modified_at=555');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_46_replay_detects_local_manga_download_schedule_change(self):
        self.apply();self.db.execute('UPDATE mangas SET next_update=500 WHERE source=6969');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_47_replay_detects_cover_last_modified_change(self):
        self.apply();self.db.execute('UPDATE mangas SET cover_last_modified=99 WHERE source=6969');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_48_replay_detects_locally_changed_sync_flag(self):
        self.apply();self.db.execute('UPDATE mangas SET is_syncing=0 WHERE source=6969');self.db.commit()
        with self.assertRaises(ValueError):self.apply()
    def test_49_replay_detects_locally_changed_chapter_sync_flag(self):
        self.apply();self.db.execute('UPDATE chapters SET is_syncing=0');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

if __name__=='__main__':unittest.main()
