"""Executable SQL statements + upstream-trigger regression, not SQLDelight codegen.

All writes occur on disposable in-memory SQLite, never a user DB.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import unittest
import uuid

HERE = Path(__file__).resolve().parent
BACKUP = HERE.parents[1]
SPIKE = BACKUP.parent
sys.path.insert(0, str(BACKUP / 'restore-candidate/pinned-schema-bridge'))
from pinned_schema_fixture import connect, SOURCE_BLOBS

QUERIES = HERE / 'PolarisParentMetadataRestore.sq'
TRIGGERS = HERE / 'pinned_update_triggers.sql'
M14 = SPIKE / 'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm'
MERGED = SPIKE / 'new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq'
LEDGER = BACKUP / 'restore-candidate/atomic-sqlite/atomic_parent_restore_candidate.sql'
UUID = '123e4567-e89b-42d3-a456-426614174000'


def labels():
    source = QUERIES.read_text(encoding='utf-8')
    # All queries in this candidate are single-statement SELECT/INSERT queries.
    return {m.group(1):m.group(2).strip() for m in re.finditer(
        r'(?ms)^([a-zA-Z][A-Za-z0-9_]*):\s*\n(.*?;)',source)}


def q(db, label, params=None):
    return db.execute(labels()[label], params or {})


def parent_params(*, is_syncing=1, notes='Archive notes', url=None, version=7, last=123456789):
    return dict(destinationUrl=url or f'merged://polaris/{UUID}', artist='Artist',
        author='Author', description='About', genre='Action, Adventure', title='Example',
        status=1,thumbnailUrl='https://example.test/cover.png', favorite=1,
        lastUpdate=0,nextUpdate=0, initialized=1, viewer=2,chapterFlags=3,
        coverLastModified=0,dateAdded=150,updateStrategy=0,calculateInterval=0,
        lastModifiedAt=last, favoriteModifiedAt=180,version=version,
        isSyncing=is_syncing, notes=notes,
        memo=json.dumps({'custom':{'deep':[1,2,{'a':True}]},'polaris.merge.work.uuid':UUID}).encode('utf-8'))


def chapter_params(parent_id,*,url='/chapter/1', last=99):
    return dict(parentId=parent_id, chapterUrl=url,chapterName='One',scanlator='Team',
        read=1,bookmark=1,lastPageRead=12,chapterNumber=1.5,sourceOrder=4,
        dateFetch=5,dateUpload=6,chapterLastModifiedAt=last,chapterVersion=3,
        chapterIsSyncing=1,chapterMemo=b'{"page":{"translated":true}}')


class CandidateQueriesTest(unittest.TestCase):
    def setUp(self):
        self.db=connect()
        self.addCleanup(self.db.close)
        self.db.executescript(M14.read_text())
        self.db.executescript(LEDGER.read_text())
        self.db.executescript(TRIGGERS.read_text())
        self.db.commit()

    def parent(self, **kw):
        return q(self.db, 'insertPolarisRestoredParentFull', parent_params(**kw)).fetchone()[0]

    def test_01_spike_migration_and_sq_are_known_original_git_blobs(self):
        for path,sha in ((M14,'8f23dc5219f49a0368705ba21d0c4e5a0d7fb1fb'),
                         (MERGED,'3e9fb499d0e1d0523aaaaaae336dd9bf5b2d4b62')):
            data=path.read_bytes()
            self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(),sha)

    def test_02_original_pinned_manga_schema_origin_is_identified(self):
        self.assertEqual(SOURCE_BLOBS['mangas.sq'],'b5d1909f759683136978e0bf2df182287ca4065d')

    def test_03_no_schema_mutation_or_unsafe_replace_in_candidate(self):
        sql=QUERIES.read_text()
        self.assertNotRegex(sql,r'(?i)\b(DROP|ALTER|REPLACE|DELETE|UPDATE|PRAGMA|ATTACH|DETACH)\b\s+(TABLE|INTO|mangas|chapters|merged)')
        self.assertNotIn('CREATE TABLE merged',sql)

    def test_04_labels_are_unique(self):
        names=re.findall(r'(?m)^([A-Za-z][A-Za-z0-9_]*):$',QUERIES.read_text())
        self.assertEqual(len(names),len(set(names)))
        self.assertEqual(len(names),len(labels()))

    def test_05_select_full_parent_from_original_columns(self):
        pid=self.parent()
        result=q(self.db,'selectPolarisRestoredParentFull',{'parentId':pid}).fetchone()
        cols=[d[0] for d in q(self.db,'selectPolarisRestoredParentFull',{'parentId':pid}).description]
        self.assertEqual(result[cols.index('notes')],'Archive notes')
        self.assertEqual(result[cols.index('version')],7)

    def test_06_parent_destination_url_is_uuid_stable(self):
        pid=self.parent()
        self.assertEqual(self.db.execute('SELECT url FROM mangas WHERE _id=?',(pid,)).fetchone()[0],f'merged://polaris/{UUID}')

    def test_07_archived_memo_other_keys_survive_insert(self):
        pid=self.parent()
        memo=json.loads(self.db.execute('SELECT memo FROM mangas WHERE _id=?',(pid,)).fetchone()[0])
        self.assertEqual(memo['custom']['deep'][2],{'a':True})

    def test_08_full_parent_fields_preserved_on_initial_insert(self):
        pid=self.parent()
        row=self.db.execute('SELECT artist,author,description,genre,status,thumbnail_url,favorite,initialized,viewer,chapter_flags,date_added,update_strategy,last_modified_at,favorite_modified_at,version,notes FROM mangas WHERE _id=?',(pid,)).fetchone()
        self.assertEqual(row,('Artist','Author','About','Action, Adventure',1,'https://example.test/cover.png',1,1,2,3,150,0,123456789,180,7,'Archive notes'))

    def test_09_nulls_are_preserved_by_full_parent_insert(self):
        p=parent_params();p['artist']=None;p['thumbnailUrl']=None
        pid=q(self.db,'insertPolarisRestoredParentFull',p).fetchone()[0]
        self.assertEqual(self.db.execute('SELECT artist,thumbnail_url FROM mangas WHERE _id=?',(pid,)).fetchone(),(None,None))

    def test_10_full_parent_select_does_not_find_nonvirtual_source(self):
        self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(77,'/ordinary','Ordinary',0,1,1,0,0,0,0)")
        pid=self.db.execute("SELECT _id FROM mangas WHERE source=77").fetchone()[0]
        self.assertIsNone(q(self.db,'selectPolarisRestoredParentFull',{'parentId':pid}).fetchone())

    def test_11_exact_category_name_candidates(self):
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('Books',0,0)")
        self.assertEqual(len(q(self.db,'selectPolarisRestoreCategoryCandidates',{'categoryName':'Books'}).fetchall()),1)
        self.assertEqual(q(self.db,'selectPolarisRestoreCategoryCandidates',{'categoryName':'books'}).fetchall(),[])

    def test_12_category_name_lookup_does_not_silently_choose_between_duplicates(self):
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('Books',0,0)")
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('Books',1,0)")
        self.assertEqual(len(q(self.db,'selectPolarisRestoreCategoryCandidates',{'categoryName':'Books'}).fetchall()),2)

    def test_13_exact_source_url_candidates(self):
        self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(77,'/real','Child',0,1,1,0,0,0,0)")
        self.assertEqual(len(q(self.db,'selectPolarisRestoreRealChildCandidates',{'childSource':77,'childUrl':'/real'}).fetchall()),1)
        self.assertEqual(q(self.db,'selectPolarisRestoreRealChildCandidates',{'childSource':78,'childUrl':'/real'}).fetchall(),[])

    def test_14_same_source_and_url_duplicates_must_be_detectable(self):
        for _ in range(2):self.db.execute("INSERT INTO mangas(source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(77,'/real','Child',0,1,1,0,0,0,0)")
        self.assertEqual(len(q(self.db,'selectPolarisRestoreRealChildCandidates',{'childSource':77,'childUrl':'/real'}).fetchall()),2)

    def test_15_parent_url_candidates_detect_unledgered_collisions(self):
        self.parent();self.parent()
        self.assertEqual(len(q(self.db,'selectPolarisRestoreParentUrlCandidates',{'destinationUrl':f'merged://polaris/{UUID}'}).fetchall()),2)

    def test_16_chapter_insert_exact_physical_fields(self):
        pid=self.parent()
        cid=q(self.db,'insertPolarisRestoredChapterFull',chapter_params(pid)).fetchone()[0]
        r=self.db.execute('SELECT manga_id,url,name,scanlator,read,bookmark,last_page_read,chapter_number,source_order,date_fetch,date_upload,last_modified_at,version,is_syncing,memo FROM chapters WHERE _id=?',(cid,)).fetchone()
        self.assertEqual(r, (pid,'/chapter/1','One','Team',1,1,12,1.5,4,5,6,99,3,1,b'{"page":{"translated":true}}'))

    def test_17_chapter_fk_prevents_orphan(self):
        with self.assertRaises(sqlite3.IntegrityError):
            q(self.db,'insertPolarisRestoredChapterFull',chapter_params(12345)).fetchone()

    def test_18_history_binds_to_restored_chapter_id_not_original_backup_id(self):
        pid=self.parent();cid=q(self.db,'insertPolarisRestoredChapterFull',chapter_params(pid)).fetchone()[0]
        q(self.db,'insertPolarisRestoredHistoryExact',{'chapterId':cid,'lastRead':123,'readDuration':45})
        self.assertEqual(q(self.db,'selectPolarisParentHistoryFull',{'parentId':pid}).fetchone(),(cid,'/chapter/1',123,45))

    def test_19_history_duplicates_error_instead_of_additive_upsert(self):
        pid=self.parent();cid=q(self.db,'insertPolarisRestoredChapterFull',chapter_params(pid)).fetchone()[0]
        args={'chapterId':cid,'lastRead':123,'readDuration':45}
        q(self.db,'insertPolarisRestoredHistoryExact',args)
        with self.assertRaises(sqlite3.IntegrityError):q(self.db,'insertPolarisRestoredHistoryExact',args)

    def test_20_tracking_exact_manga_sync_fields(self):
        pid=self.parent()
        q(self.db,'insertPolarisRestoredTrackExact',dict(parentId=pid,syncId=5,remoteId=901,
          libraryId=77,trackTitle='Title',lastChapterRead=17.5,totalChapters=22,
          trackStatus=1,trackScore=8.5,remoteUrl='/track',startDate=100,finishDate=200,isPrivate=1))
        row=q(self.db,'selectPolarisParentTrackingFull',{'parentId':pid}).fetchone()
        self.assertEqual(row[1:],(pid,5,901,77,'Title',17.5,22,1,8.5,'/track',100,200,1))

    def test_21_tracking_fk_prevents_orphan(self):
        with self.assertRaises(sqlite3.IntegrityError):
            q(self.db,'insertPolarisRestoredTrackExact',dict(parentId=456777,syncId=5,remoteId=901,
              libraryId=77,trackTitle='Title',lastChapterRead=17.5,totalChapters=22,
              trackStatus=1,trackScore=8.5,remoteUrl='/track',startDate=100,finishDate=200,isPrivate=1))

    def test_22_excluded_scanlators_roundtrip(self):
        pid=self.parent()
        q(self.db,'insertPolarisRestoredExclusionExact',dict(parentId=pid,excludedScanlator='Skipped Team'))
        self.assertEqual(q(self.db,'selectPolarisParentExclusionsFull',{'parentId':pid}).fetchall(),[('Skipped Team',)])

    def test_23_parent_category_fk_and_readback(self):
        pid=self.parent();self.db.execute("INSERT INTO categories(name,sort,flags) VALUES ('Read',1,0)")
        cat=self.db.execute("SELECT _id FROM categories WHERE name='Read'").fetchone()[0]
        q(self.db,'insertPolarisRestoredCategoryExact',dict(parentId=pid,categoryId=cat))
        self.assertEqual(q(self.db,'selectPolarisParentCategoriesFull',{'parentId':pid}).fetchall(),[(cat,)])

    def test_24_ledger_and_merged_edge_physical_readback(self):
        pid=self.parent()
        self.db.execute('INSERT INTO polaris_restore_ledger(archive_uuid,parent_manga_id,archive_digest) VALUES(?,?,?)',(UUID,pid,'a'*64))
        self.db.execute('''INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source)
             VALUES(0,0,2,999,0,?,?,?, ?,6969)''',(pid,f'merged://polaris/{UUID}',pid,f'merged://polaris/{UUID}'))
        rows=q(self.db,'selectPolarisParentEdgesFull',{'parentId':pid}).fetchall()
        self.assertEqual(len(rows),1);self.assertEqual(rows[0][-1],6969)

    def test_25_category_trigger_increments_version_when_not_syncing(self):
        pid=self.parent(is_syncing=0)
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('History',0,0)")
        cat=self.db.execute("SELECT _id FROM categories WHERE name='History'").fetchone()[0]
        q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':pid,'categoryId':cat})
        self.assertEqual(self.db.execute('SELECT version FROM mangas WHERE _id=?',(pid,)).fetchone()[0],8)

    def test_26_category_trigger_changes_archived_timestamp_when_not_syncing(self):
        pid=self.parent(is_syncing=0,last=123456789)
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('History',0,0)")
        cat=self.db.execute("SELECT _id FROM categories WHERE name='History'").fetchone()[0]
        q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':pid,'categoryId':cat})
        self.assertNotEqual(self.db.execute('SELECT last_modified_at FROM mangas WHERE _id=?',(pid,)).fetchone()[0],123456789)

    def test_27_is_syncing_one_avoids_category_version_but_is_not_valid_final_state(self):
        pid=self.parent(is_syncing=1,last=123456789)
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('History',0,0)")
        cat=self.db.execute("SELECT _id FROM categories WHERE name='History'").fetchone()[0]
        q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':pid,'categoryId':cat})
        self.assertEqual(self.db.execute('SELECT version,last_modified_at,is_syncing FROM mangas WHERE _id=?',(pid,)).fetchone(),(7,123456789,1))

    def test_28_finalizing_sync_flag_triggers_timestamp_drift(self):
        pid=self.parent(is_syncing=1,last=123456789)
        self.db.execute('UPDATE mangas SET is_syncing=0 WHERE _id=?',(pid,))
        self.assertEqual(self.db.execute('SELECT is_syncing FROM mangas WHERE _id=?',(pid,)).fetchone()[0],0)
        self.assertNotEqual(self.db.execute('SELECT last_modified_at FROM mangas WHERE _id=?',(pid,)).fetchone()[0],123456789)

    def test_29_chapter_finalizing_sync_flag_triggers_timestamp_drift(self):
        pid=self.parent();cid=q(self.db,'insertPolarisRestoredChapterFull',chapter_params(pid,last=98765)).fetchone()[0]
        self.db.execute('UPDATE chapters SET is_syncing=0 WHERE _id=?',(cid,))
        self.assertNotEqual(self.db.execute('SELECT last_modified_at FROM chapters WHERE _id=?',(cid,)).fetchone()[0],98765)

    def test_30_triggers_are_originally_named_and_enable_update_stamp(self):
        names={x[0] for x in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        self.assertTrue({'update_last_modified_at_mangas','insert_manga_category_update_version',
           'update_last_modified_at_chapters','update_chapter_and_manga_version'}<=names)

    def test_31_finalizing_sync_state_fail_closed_rolls_back_complete_transaction(self):
        self.db.commit();self.db.execute('BEGIN IMMEDIATE')
        try:
            pid=self.parent(is_syncing=1,last=123456789)
            q(self.db,'insertPolarisRestoredChapterFull',chapter_params(pid,last=900))
            self.db.execute('UPDATE mangas SET is_syncing=0 WHERE _id=?',(pid,))
            row=self.db.execute('SELECT last_modified_at FROM mangas WHERE _id=?',(pid,)).fetchone()[0]
            if row != 123456789:raise ValueError('Unable to preserve archived lastModifiedAt with pinned triggers')
            self.fail('Unexpected exact timestamp; update the regression expectations')
        except ValueError:
            self.db.rollback()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM chapters').fetchone()[0],0)

    def test_32_two_parent_trigger_conflict_rolls_back_both(self):
        self.db.commit();self.db.execute('BEGIN IMMEDIATE')
        try:
            first=self.parent(is_syncing=1)
            self.db.execute('UPDATE mangas SET is_syncing=0 WHERE _id=?',(first,))
            self.assertNotEqual(self.db.execute('SELECT last_modified_at FROM mangas WHERE _id=?',(first,)).fetchone()[0],123456789)
            _=self.parent(is_syncing=1,notes='Second')
            raise ValueError('Injected strict metadata readback rejection')
        except ValueError:
            self.db.rollback()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas').fetchone()[0],0)

    def test_33_foreign_keys_remain_enabled_after_staged_migration(self):
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone()[0],1)

    def test_34_source_parent_link_is_deleted_on_parent_delete(self):
        pid=self.parent()
        self.db.execute('''INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source)
             VALUES(0,0,2,999,0,?,?,?, ?,6969)''',(pid,f'merged://polaris/{UUID}',pid,f'merged://polaris/{UUID}'))
        self.db.execute('DELETE FROM mangas WHERE _id=?',(pid,))
        self.assertEqual(q(self.db,'selectPolarisParentEdgesFull',{'parentId':pid}).fetchall(),[])

    def test_35_full_metadata_readback_all_tables_without_user_edits(self):
        pid=self.parent()
        self.db.execute("INSERT INTO categories(name,sort,flags) VALUES('Read',0,0)")
        cat=self.db.execute("SELECT _id FROM categories WHERE name='Read'").fetchone()[0]
        q(self.db,'insertPolarisRestoredCategoryExact',{'parentId':pid,'categoryId':cat})
        cid=q(self.db,'insertPolarisRestoredChapterFull',chapter_params(pid)).fetchone()[0]
        q(self.db,'insertPolarisRestoredHistoryExact',dict(chapterId=cid,lastRead=42,readDuration=5))
        q(self.db,'insertPolarisRestoredExclusionExact',dict(parentId=pid,excludedScanlator='Team'))
        self.assertEqual(len(q(self.db,'selectPolarisParentChaptersFull',{'parentId':pid}).fetchall()),1)
        self.assertEqual(len(q(self.db,'selectPolarisParentHistoryFull',{'parentId':pid}).fetchall()),1)
        self.assertEqual(len(q(self.db,'selectPolarisParentCategoriesFull',{'parentId':pid}).fetchall()),1)
        self.assertEqual(len(q(self.db,'selectPolarisParentExclusionsFull',{'parentId':pid}).fetchall()),1)
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])


if __name__=='__main__':unittest.main(verbosity=2)
