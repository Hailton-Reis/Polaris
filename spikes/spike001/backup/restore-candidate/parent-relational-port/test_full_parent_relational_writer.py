"""Concrete full-table parent-LAST proof over *actual staged SQL* and SQLite fixtures.
49+ assertions including fault injection; never a user's DB. No Android claim.
"""
import copy
import json
import re
import sqlite3
import sys
import unittest
from pathlib import Path
from dataclasses import replace

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/'pinned-schema-bridge'))
from pinned_schema_fixture import connect
from physical_parent_writer import Batch,Edge,restore_fresh_parents, _assert_readback, SQL,MERGED_SQL,UUID_KEY

M14=HERE.parents[2]/'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm'
LEDGER=HERE.parent/'atomic-sqlite/atomic_parent_restore_candidate.sql'
TRIGGERS=HERE.parent/'parent-sqldelight-fields/pinned_update_triggers.sql'
U='123e4567-e89b-42d3-a456-426614174000'
V='c95d6621-e236-4024-ae3c-49dd116d2f30'


def fixture():
    c=connect()
    for path in (M14, LEDGER, TRIGGERS): c.executescript(path.read_text())
    c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(101,77,'/real/101','Real',0,1,1,0,0,0,0)")
    c.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(102,78,'/real/102','Real2',0,1,1,0,0,0,0)")
    for cat, name in ((71,'Read'),(72,'Archive')):c.execute('INSERT INTO categories(_id,name,sort,flags) VALUES(?,?,0,0)',(cat,name))
    c.commit()
    return c


def sample(uuid=U, child_id=101, source=77, parent_url=None):
    url=parent_url or 'merged://polaris/'+uuid
    parent=dict(source=6969,destinationUrl=url,artist='Artist',author=None,
        description='é unicode',genre=['Action','Magic'],title='Example',status=4,
        thumbnailUrl=None,favorite=1,lastUpdate=None,nextUpdate=None,
        initialized=1,viewer=10,chapterFlags=5,coverLastModified=0,dateAdded=120,
        updateStrategy=0,calculateInterval=0,lastModifiedAt=12345678,
        favoriteModifiedAt=15,version=7,isSyncing=0,notes='no overwrite',
        memo={'unknown':{'nested':[1,{'x':True}]},UUID_KEY:uuid})
    chapter=dict(chapterUrl='/ch1',chapterName='One',scanlator='Team',read=1,bookmark=1,
        lastPageRead=23,chapterNumber=1.25,sourceOrder=9,dateFetch=5,dateUpload=6,
        chapterLastModifiedAt=8675309,chapterVersion=12,chapterIsSyncing=0,
        chapterMemo={'status':{'nested':['yes',4]}})
    return Batch(uuid=uuid,digest='b'*64,parent=parent,chapters=[chapter],categories=[71,72],
        history=[dict(chapterUrl='/ch1',lastRead=1000,readDuration=9)],
        tracking=[dict(syncId=3,remoteId=9999,libraryId=7,trackTitle='Tracker',lastChapterRead=1.2,
            totalChapters=55,trackStatus=1,trackScore=9.25,remoteUrl='https://track.test',
            startDate=11,finishDate=22,isPrivate=1)],exclusions=['Scan Bad'],
        edges=[Edge(source=source,url=f'/real/{child_id}',manga_id=child_id,priority=0,info=True,updates=True),
               Edge(source=88,url='/pending',manga_id=None,priority=1),
               Edge(source=6969,url=url,manga_id=None,priority=2147483647)])


def change(b:Batch,**kw):return replace(b,**kw)


def get(c,sql,params=()):return c.execute(sql,params).fetchall()

class RelationalRestoreTest(unittest.TestCase):
    def setUp(self):self.db=fixture();self.addCleanup(self.db.close)
    def restore(self,b=None):return restore_fresh_parents(self.db,[sample() if b is None else b])
    def fail(self,b,code):
        with self.assertRaisesRegex((ValueError,sqlite3.IntegrityError),re.escape(code)):
            self.restore(b)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(get(self.db,'SELECT COUNT(*) FROM polaris_restore_ledger')[0][0],0)
        self.assertEqual(get(self.db,'SELECT COUNT(*) FROM merged')[0][0],0)

    def test_01_true_staged_sql_label_used(self):self.assertIn('insertPolarisRestoredReservedParentLast',SQL)
    def test_02_true_merged_sq_insert_used(self):self.assertIn('insertReturningId',MERGED_SQL)
    def test_03_parent_last_preserves_version_and_timestamp(self):
        self.restore();self.assertEqual(get(self.db,'SELECT version,last_modified_at,is_syncing FROM mangas WHERE source=6969'),[(7,12345678,0)])
    def test_04_all_fk_valid_after_commit(self):self.restore();self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_05_fk_deferral_auto_reset(self):self.restore();self.assertEqual(get(self.db,'PRAGMA defer_foreign_keys'),[(0,)])
    def test_06_exact_full_parent_fields(self):self.restore();self.assertEqual(get(self.db,'SELECT artist,author,description,genre,notes FROM mangas WHERE source=6969'),[('Artist',None,'é unicode','Action, Magic','no overwrite')])
    def test_07_preserve_nested_parent_memo(self):self.restore();self.assertEqual(json.loads(get(self.db,'SELECT memo FROM mangas WHERE source=6969')[0][0])['unknown'],{'nested':[1,{'x':True}]})
    def test_08_preserve_nested_chapter_memo(self):self.restore();self.assertEqual(json.loads(get(self.db,'SELECT memo FROM chapters')[0][0])['status'],{'nested':['yes',4]})
    def test_09_chapter_full_fields(self):self.restore();self.assertEqual(get(self.db,'SELECT read,bookmark,last_page_read,chapter_number,last_modified_at,version,is_syncing FROM chapters'),[(1,1,23,1.25,8675309,12,0)])
    def test_10_history_uses_newly_created_chapter_id(self):
        self.restore();self.assertEqual(get(self.db,'SELECT c.url,h.last_read,h.time_read FROM history h JOIN chapters c ON c._id=h.chapter_id'),[('/ch1',1000,9)])
    def test_11_category_two_without_trigger_drift(self):self.restore();self.assertEqual(get(self.db,'SELECT category_id FROM mangas_categories ORDER BY category_id'),[(71,),(72,)])
    def test_12_tracking_all_fields(self):self.restore();self.assertEqual(get(self.db,'SELECT sync_id,remote_id,score,private FROM manga_sync'),[(3,9999,9.25,1)])
    def test_13_scanlator_exclusion(self):self.restore();self.assertEqual(get(self.db,'SELECT scanlator FROM excluded_scanlators'),[('Scan Bad',)])
    def test_14_edges_correct_source_and_pending(self):self.restore();self.assertEqual(get(self.db,'SELECT manga_source,manga_url,manga_id FROM merged ORDER BY chapter_priority')[:2],[(77,'/real/101',101),(88,'/pending',None)])
    def test_15_root_self_link(self):
        p=self.restore()[0];self.assertEqual(get(self.db,'SELECT manga_source,manga_id FROM merged WHERE manga_source=6969'),[(6969,p)])
    def test_16_uuid_ledger_after_commit(self):
        p=self.restore()[0];self.assertEqual(get(self.db,'SELECT archive_uuid,parent_manga_id,archive_digest FROM polaris_restore_ledger'),[(U,p,'b'*64)])
    def test_17_replay_refused_without_duplicate(self):
        self.restore();with_err=None
        try:self.restore()
        except ValueError as e:with_err=str(e)
        self.assertEqual(with_err,'POLARIS_PARENT_URL_OCCUPIED')
        self.assertEqual(get(self.db,'SELECT count(*) FROM mangas WHERE source=6969'),[(1,)])
    def test_18_two_parents_atomic_and_sorted_ids(self):
        b=sample(V,child_id=102,source=78);pids=restore_fresh_parents(self.db,[sample(),b]);self.assertEqual(len(pids),2);self.assertEqual(pids[1],pids[0]+1)
    def test_19_second_parent_rollback_first_on_fault(self):
        b=sample(V,child_id=102,source=78)
        def fault(step,pid,db):
            if step=='before_parent' and pid>=104:raise RuntimeError('BOOM_SECOND')
        with self.assertRaisesRegex(RuntimeError,'BOOM_SECOND'):
            restore_fresh_parents(self.db,[sample(),b],fault)
        self.assertEqual(get(self.db,'SELECT COUNT(*) FROM mangas WHERE source=6969'),[(0,)])
        self.assertEqual(get(self.db,'SELECT COUNT(*) FROM history'),[(0,)])
    def test_20_detect_local_parent_edit_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE mangas SET notes=? WHERE _id=?',('tampered',pid))
        with self.assertRaisesRegex(ValueError,'POLARIS_PARENT_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
        self.assertEqual(get(self.db,'SELECT COUNT(*) FROM mangas WHERE source=6969'),[(0,)])
    def test_21_detect_chapter_edit_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE chapters SET name=? WHERE manga_id=?',('altered',pid))
        with self.assertRaisesRegex(ValueError,'POLARIS_CHAPTER_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_22_detect_category_missing_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('DELETE FROM mangas_categories WHERE manga_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_CATEGORY_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_23_detect_tracker_drift_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE manga_sync SET score=0 WHERE manga_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_TRACKING_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_24_detect_history_drift_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE history SET time_read=1')
        with self.assertRaisesRegex(ValueError,'POLARIS_HISTORY_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_25_detect_exclusion_drift_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('DELETE FROM excluded_scanlators WHERE manga_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_EXCLUSION_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_26_detect_edge_drift_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE merged SET chapter_priority=3 WHERE manga_source=88')
        with self.assertRaisesRegex(ValueError,'POLARIS_MERGED_EDGES_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_27_detect_ledger_drift_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE polaris_restore_ledger SET archive_digest=? WHERE parent_manga_id=?',('c'*64,pid))
        with self.assertRaisesRegex(ValueError,'POLARIS_LEDGER_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_28_reject_losing_genre_separator(self):
        p=copy.deepcopy(sample().parent);p['genre']=['Magic, Action'];self.fail(change(sample(),parent=p),'POLARIS_LOSSY_GENRE')
    def test_29_reject_missing_uuid_in_memo(self):
        p=copy.deepcopy(sample().parent);del p['memo'][UUID_KEY];self.fail(change(sample(),parent=p),'POLARIS_BAD_MEMO_UUID')
    def test_30_reject_bad_destination_url(self):
        p=copy.deepcopy(sample().parent);p['destinationUrl']='merged://legacy';self.fail(change(sample(),parent=p),'POLARIS_BAD_DESTINATION')
    def test_31_reject_duplicate_chapter_url(self):self.fail(change(sample(),chapters=sample().chapters*2),'POLARIS_BAD_CHAPTER_URLS')
    def test_32_reject_orphan_history(self):self.fail(change(sample(),history=[dict(chapterUrl='/missing',lastRead=0,readDuration=0)]),'POLARIS_BAD_HISTORY')
    def test_33_reject_duplicate_track_sync_id(self):self.fail(change(sample(),tracking=sample().tracking*2),'POLARIS_BAD_TRACKING')
    def test_34_reject_duplicate_category_ids(self):self.fail(change(sample(),categories=[71,71]),'POLARIS_BAD_CATEGORIES')
    def test_35_reject_duplicate_exclusions(self):self.fail(change(sample(),exclusions=['A','A']),'POLARIS_BAD_EXCLUSIONS')
    def test_36_reject_duplicate_edge_source_url(self):self.fail(change(sample(),edges=sample().edges+sample().edges[:1]),'POLARIS_BAD_EDGES')
    def test_37_reject_missing_root(self):self.fail(change(sample(),edges=sample().edges[:-1]),'POLARIS_INVALID_ROOT')
    def test_38_reject_root_wrong_flags(self):
        edges=sample().edges;edges[-1]=replace(edges[-1],info=True)
        self.fail(change(sample(),edges=edges),'POLARIS_INVALID_ROOT')
    def test_39_reject_missing_info_provider(self):
        edges=sample().edges;edges[0]=replace(edges[0],info=False)
        self.fail(change(sample(),edges=edges),'POLARIS_BAD_INFO_EDGE')
    def test_40_reject_ambiguous_physical_source_child(self):
        self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(77,'/real/101','Copy',0,1,1,0,0,0,0)");self.db.commit()
        self.fail(sample(),'POLARIS_STALE_REAL_CHILD')
    def test_41_reject_stale_physical_source_url(self):
        self.db.execute('UPDATE mangas SET url=? WHERE _id=101',('/new',));self.db.commit();self.fail(sample(),'POLARIS_STALE_REAL_CHILD')
    def test_42_reject_pending_child_now_resolved(self):
        self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(88,'/pending','Now',0,1,1,0,0,0,0)");self.db.commit()
        self.fail(sample(),'POLARIS_PENDING_CHILD_NOW_RESOLVED')
    def test_43_reject_missing_category(self):
        self.db.execute('DELETE FROM categories WHERE _id=72');self.db.commit();self.fail(sample(),'POLARIS_UNRESOLVED_CATEGORY')
    def test_44_reject_duplicate_batch_uuid(self):
        with self.assertRaisesRegex(ValueError,'POLARIS_DUPLICATE_ARCHIVE_UUID'):restore_fresh_parents(self.db,[sample(),sample()])
    def test_45_reject_unknown_virtual_parent_memo(self):
        self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES(6969,'merged://other','Other',0,1,1,0,0,0,0,X'FF')");self.db.commit()
        self.fail(sample(),'POLARIS_UNVERIFIABLE_VIRTUAL_MEMO')
    def test_46_reject_existing_legacy_uuid_memo_without_ledger(self):
        self.db.execute('INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES(6969,?,"Other",0,1,1,0,0,0,0,?)',('merged://other',json.dumps({UUID_KEY:U}).encode()));self.db.commit()
        self.fail(sample(),'POLARIS_LEGACY_UUID_OCCUPIED')
    def test_47_reject_fk_disabled(self):
        self.db.execute('PRAGMA foreign_keys=OFF')
        with self.assertRaisesRegex(ValueError,'POLARIS_FOREIGN_KEYS_OFF'):self.restore()
    def test_48_reject_nested_outer_transaction(self):
        self.db.execute('BEGIN')
        with self.assertRaisesRegex(ValueError,'POLARIS_OUTER_TRANSACTION_UNSUPPORTED'):self.restore()
        self.db.rollback()
    def test_49_invalid_digest_rejected(self):self.fail(replace(sample(),digest='BAD'),'POLARIS_BAD_DIGEST')
    def test_50_noncanonical_uuid_rejected(self):
        bad=sample();self.fail(replace(bad,uuid='123E4567-E89B-42D3-A456-426614174000'),'POLARIS_BAD_UUID')
    def test_51_empty_batch_rejected(self):
        with self.assertRaisesRegex(ValueError,'POLARIS_EMPTY_BATCH'):restore_fresh_parents(self.db,[])
    def test_52_no_parent_id_colliding_across_fresh_batch(self):
        b=sample(V,child_id=102,source=78)
        p=restore_fresh_parents(self.db,[sample(),b]);self.assertEqual(len(set(p)),2)

    def test_53_detect_added_extra_tracker(self):
        def fault(step,pid,db):
            if step=='before_readback':
                db.execute("INSERT INTO manga_sync(manga_id,sync_id,remote_id,library_id,title,last_chapter_read,total_chapters,status,score,remote_url,start_date,finish_date,private) VALUES(?,?,1,1,'other',1,2,3,4,'',0,0,0)",(pid,9))
        with self.assertRaisesRegex(ValueError,'POLARIS_TRACKING_COUNT_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_54_detect_deleted_tracker(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('DELETE FROM manga_sync WHERE manga_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_TRACKING_COUNT_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_55_detect_added_chapter(self):
        def fault(step,pid,db):
            if step=='before_readback':
                db.execute("INSERT INTO chapters(manga_id,url,name,read,bookmark,last_page_read,chapter_number,source_order,date_fetch,date_upload) VALUES(?,?,'Another',0,0,0,0,0,0,0)",(pid,'/ch2'))
        with self.assertRaisesRegex(ValueError,'POLARIS_CHAPTER_COUNT_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_56_detect_removed_chapter(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('DELETE FROM chapters WHERE manga_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_CHAPTER_COUNT_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_57_detect_added_history(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('DELETE FROM history')
        with self.assertRaisesRegex(ValueError,'POLARIS_HISTORY_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_58_detect_added_exclusion(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('INSERT INTO excluded_scanlators(manga_id,scanlator) VALUES(?,?)',(pid,'extra'))
        with self.assertRaisesRegex(ValueError,'POLARIS_EXCLUSION_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_59_detect_added_category(self):
        def fault(step,pid,db):
            if step=='before_readback':
                db.execute("INSERT INTO categories(_id,name,sort,flags) VALUES(75,'Extra',0,0)")
                db.execute('INSERT INTO mangas_categories(manga_id,category_id) VALUES(?,?)',(pid,75))
        with self.assertRaisesRegex(ValueError,'POLARIS_PARENT_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_60_detect_deleted_source_edge(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('DELETE FROM merged WHERE manga_source=77 AND merge_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_MERGED_EDGES_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_61_second_parent_readback_failure_rolls_back_first(self):
        def fault(step,pid,db):
            if step=='before_readback' and pid>=104:db.execute('DELETE FROM manga_sync WHERE manga_id=?',(pid,))
        with self.assertRaisesRegex(ValueError,'POLARIS_TRACKING_COUNT_DRIFT'):
            restore_fresh_parents(self.db,[sample(),sample(V,child_id=102,source=78)],fault)
        self.assertEqual(get(self.db,'SELECT count(*) FROM polaris_restore_ledger'),[(0,)])
        self.assertEqual(get(self.db,'SELECT count(*) FROM chapters'),[(0,)])
    def test_62_duplicate_legacy_claim_not_silently_reused(self):
        self.db.execute('INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES(6969,?,"Other",0,1,1,0,0,0,0,?)',('merged://different',json.dumps({UUID_KEY:U}).encode()));self.db.commit()
        with self.assertRaisesRegex(ValueError,'POLARIS_LEGACY_UUID_OCCUPIED'):self.restore()
        self.assertEqual(get(self.db,'SELECT COUNT(*) FROM polaris_restore_ledger'),[(0,)])
    def test_63_all_children_pending_but_real_info_link_rejected(self):
        links=sample().edges;links[0]=replace(links[0],manga_id=None)
        self.fail(change(sample(),edges=links),'POLARIS_PENDING_CHILD_NOW_RESOLVED')
    def test_64_reject_fake_real_child_id(self):
        links=sample().edges;links[0]=replace(links[0],manga_id=99999)
        self.fail(change(sample(),edges=links),'POLARIS_STALE_REAL_CHILD')
    def test_65_detect_memo_modified_before_commit(self):
        def fault(step,pid,db):
            if step=='before_readback':db.execute('UPDATE mangas SET memo=? WHERE _id=?',(b'{}',pid))
        with self.assertRaisesRegex(ValueError,'POLARIS_PARENT_METADATA_DRIFT'):restore_fresh_parents(self.db,[sample()],fault)
    def test_66_id_reservation_is_after_preexisting_real_mangas(self):
        pid=self.restore()[0];self.assertGreater(pid,102)

    def test_67_reject_prepared_parent_id_mismatch(self):
        p=copy.deepcopy(sample().parent);p['reservedParentId']=900
        self.fail(change(sample(),parent=p),'POLARIS_PREPARED_ID_MISMATCH')
    def test_68_reject_prepared_chapter_parent_id_mismatch(self):
        ch=copy.deepcopy(sample().chapters);ch[0]['parentId']=900
        self.fail(change(sample(),chapters=ch),'POLARIS_PREPARED_ID_MISMATCH')

if __name__=='__main__':unittest.main(verbosity=2)
