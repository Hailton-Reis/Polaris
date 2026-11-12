"""Check actual Polaris Spike-001 merged.sq and migration14, not a second merged table.

All in-memory, local host checks. No real Android database is opened.
"""
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path
from verify_layering import (
    PINNED_YOMOTSU, STAGED_BLOBS, STAGED_SQL, STAGED_MIGRATION,
    LEDGER_CANDIDATE, OLD_BRIDGE, UUID_KEY,
    git_blob, new_baseline, apply_spike14, ddl_from_merged_sq,
    native_columns, sql_objects, audit_existing_links, in_memory_rehearsal,
    seed_parent, seed_link, verify_staged_and_migration_shape,
)
U1='123e4567-e89b-42d3-a456-426614174000'
U2='123e4567-e89b-42d3-a456-426614174001'

class Spike14ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.db=new_baseline()
        self.addCleanup(self.db.close)
        apply_spike14(self.db)
        self.db.commit()
    def populated(self):
        seed_parent(self.db);seed_link(self.db)
        self.db.commit()
        return self.db
    def upgrade(self):
        self.db.executescript(LEDGER_CANDIDATE.read_text())
        self.db.commit()

    def test_01_pinned_upstream_commit_exact(self):
        self.assertEqual(PINNED_YOMOTSU,'0fb80c439ef816eeb50674f1b90af39918b176d8')
    def test_02_staged_merged_source_git_blob_exact(self):
        self.assertEqual(git_blob(STAGED_SQL),STAGED_BLOBS['merged.sq'])
    def test_03_staged_migration14_git_blob_exact(self):
        self.assertEqual(git_blob(STAGED_MIGRATION),STAGED_BLOBS['14.sqm'])
    def test_04_pinned_upstream_no_merge_before_spike14(self):
        upstream=new_baseline();self.addCleanup(upstream.close)
        self.assertNotIn('merged',sql_objects(upstream))
    def test_05_real_spike14_creates_merged(self):
        self.assertEqual(sql_objects(self.db)['merged'],'table')
    def test_06_merged_sql_is_same_physical_table_as_migration14(self):
        self.assertEqual(verify_staged_and_migration_shape()[0],native_columns(self.db,'merged'))
    def test_07_merge_staged_has_correct_11_columns(self):
        self.assertEqual(native_columns(self.db,'merged'),('_id','info_manga','get_chapter_updates','chapter_sort_mode','chapter_priority','download_chapters','merge_id','merge_url','manga_id','manga_url','manga_source'))
    def test_08_real_spike14_has_two_fk_actions(self):
        fks=list(self.db.execute('PRAGMA foreign_key_list(merged)'))
        actions={(x[3],x[6]) for x in fks}
        self.assertEqual(actions,{('manga_id','SET NULL'),('merge_id','CASCADE')})
    def test_09_existing_nonunique_parent_index_present(self):
        self.assertIn('merged_merge_id_index',sql_objects(self.db))
    def test_10_spike14_does_not_contain_new_restore_ledger(self):
        self.assertNotIn('polaris_restore_ledger',sql_objects(self.db))
    def test_11_candidates_are_only_additive_after_14(self):
        self.assertNotIn('CREATE TABLE MERGED',LEDGER_CANDIDATE.read_text().upper())
        self.upgrade()
        self.assertIn('merged',sql_objects(self.db))
        self.assertIn('polaris_restore_ledger',sql_objects(self.db))
    def test_12_old_bridge_is_not_reapplicable_to_spike14(self):
        with self.assertRaisesRegex(sqlite3.OperationalError,'already exists'):
            self.db.executescript(OLD_BRIDGE.read_text())
    def test_13_ledger_was_not_in_original_spike14(self):
        self.assertNotIn('polaris_restore_ledger',STAGED_MIGRATION.read_text())
    def test_14_additive_candidate_adds_expected_indexes(self):
        self.upgrade()
        objects=sql_objects(self.db)
        self.assertIn('polaris_merged_source_identity_unique',objects)
        self.assertIn('polaris_merged_real_id_unique',objects)
    def test_15_source_and_real_id_index_uniqueness_flags(self):
        self.upgrade()
        got={row[1]:(row[2],row[4]) for row in self.db.execute('PRAGMA index_list(merged)')}
        self.assertEqual(got['polaris_merged_source_identity_unique'],(1,0))
        self.assertEqual(got['polaris_merged_real_id_unique'],(1,1))
    def test_16_clean_empty_spike14_audit_passes(self):
        self.assertEqual(audit_existing_links(self.db),())
    def test_17_clean_existing_merge_audit_passes(self):
        self.populated()
        self.assertEqual(audit_existing_links(self.db),())
    def test_18_upgrade_preserves_existing_parent_and_real_manga(self):
        self.populated()
        before=self.db.execute('SELECT * FROM mangas ORDER BY _id').fetchall()
        self.upgrade()
        after=self.db.execute('SELECT * FROM mangas ORDER BY _id').fetchall()
        self.assertEqual(before,after)
    def test_19_upgrade_preserves_all_existing_merged_edges(self):
        self.populated()
        before=self.db.execute('SELECT * FROM merged ORDER BY _id').fetchall()
        self.upgrade()
        self.assertEqual(before,self.db.execute('SELECT * FROM merged ORDER BY _id').fetchall())
    def test_20_rehearsal_clones_in_memory_without_live_schema_changes(self):
        self.populated();before=list(self.db.iterdump())
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'PASS_IN_MEMORY_ONLY')
        self.assertEqual(before,list(self.db.iterdump()))
    def test_21_rehearsal_explicit_not_android_approval(self):
        self.populated();r=in_memory_rehearsal(self.db)
        self.assertFalse(r['applied_to_android'])
        self.assertFalse(r['live_database_modified'])
    def test_22_duplicate_source_url_preflight_fails_without_mutation(self):
        self.populated();seed_link(self.db,child_id=None)
        self.db.commit();before=list(self.db.iterdump())
        self.assertIn('DUPLICATE_SOURCE_IDENTITY',audit_existing_links(self.db))
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'BLOCKED_READ_ONLY')
        self.assertEqual(before,list(self.db.iterdump()))
    def test_23_duplicate_real_id_different_claim_preflight_fails(self):
        self.populated();seed_link(self.db,child_id=101,source=88,url='/other')
        self.db.commit()
        self.assertIn('DUPLICATE_REAL_ROW',audit_existing_links(self.db))
        self.assertIn('STALE_RESOLVED_CHILD',audit_existing_links(self.db))
    def test_24_parent_that_is_not_virtual_refused(self):
        self.populated();self.db.execute('UPDATE mangas SET source=999 WHERE _id=500');self.db.commit()
        self.assertIn('INVALID_VIRTUAL_PARENT',audit_existing_links(self.db))
    def test_25_wrong_saved_real_url_refused(self):
        self.populated();self.db.execute("UPDATE mangas SET url='/moved' WHERE _id=101");self.db.commit()
        self.assertIn('STALE_RESOLVED_CHILD',audit_existing_links(self.db))
    def test_26_invalid_virtual_parent_memo_refused(self):
        self.populated();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(b'not-json',));self.db.commit()
        self.assertIn('UNVERIFIABLE_VIRTUAL_MEMO',audit_existing_links(self.db))
    def test_27_uuid_claim_without_ledger_requires_review(self):
        self.populated();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(json.dumps({UUID_KEY:U1}).encode(),));self.db.commit()
        self.assertIn('UNTRACKED_UUID_CLAIM',audit_existing_links(self.db))
    def test_28_duplicate_uuid_claims_fails_before_upgrade(self):
        self.populated();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(json.dumps({UUID_KEY:U1}).encode(),))
        self.db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                        (501,6969,'merged://legacy/2','Other',0,1,1,0,0,0,0,json.dumps({UUID_KEY:U1}).encode()))
        self.db.commit()
        self.assertIn('DUPLICATE_UUID_CLAIM',audit_existing_links(self.db))
    def test_29_stage14_fk_deleting_real_child_becomes_pending(self):
        self.populated();self.db.execute('DELETE FROM mangas WHERE _id=101');self.db.commit()
        self.assertEqual(self.db.execute('SELECT manga_id FROM merged').fetchone()[0],None)
    def test_30_stage14_fk_deleting_virtual_parent_cascades_links(self):
        self.populated();self.db.execute('DELETE FROM mangas WHERE _id=500');self.db.commit()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],0)
    def test_31_restore_ledger_fk_deleting_parent_cascades(self):
        self.populated();self.upgrade()
        self.db.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(U1,500,'digest'))
        self.db.execute('DELETE FROM mangas WHERE _id=500');self.db.commit()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone()[0],0)
    def test_32_ledger_refuses_unknown_parent_id(self):
        self.upgrade()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(U1,-42,'digest'))
        self.db.rollback()
    def test_33_ledger_refuses_two_uuids_same_parent(self):
        self.populated();self.upgrade()
        self.db.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(U1,500,'digest'))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(U2,500,'digest'))
        self.db.rollback()
    def test_34_unique_index_refuses_duplicate_same_source_url(self):
        self.populated();self.upgrade()
        with self.assertRaises(sqlite3.IntegrityError):seed_link(self.db,child_id=None)
        self.db.rollback()
    def test_35_unique_index_refuses_repeated_real_id_with_changed_saved_source(self):
        self.populated();self.upgrade()
        with self.assertRaises(sqlite3.IntegrityError):seed_link(self.db,child_id=101,source=88,url='/wrong')
        self.db.rollback()
    def test_36_same_source_url_may_exist_under_different_parents(self):
        self.populated();seed_parent(self.db,parent_id=600,child_id=102)
        seed_link(self.db,parent_id=600,child_id=None,source=77,url='/real/101')
        self.db.commit();self.upgrade()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM merged WHERE manga_url='/real/101'").fetchone()[0],2)
    def test_37_duplicate_legacy_source_url_is_blocked_before_new_unique_index(self):
        self.populated();seed_link(self.db,child_id=None);self.db.commit()
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'BLOCKED_READ_ONLY')
        self.assertNotIn('polaris_restore_ledger',sql_objects(self.db))
    def test_38_pinned_merged_sql_insert_has_physical_merged_query(self):
        s=STAGED_SQL.read_text()
        self.assertIn('insertReturningId:',s)
        self.assertIn('WHERE NOT EXISTS (',s)
        self.assertIn('deleteByMergeId:',s)
        self.assertIn('selectMergedMangasById:',s)
    def test_39_spike14_contains_no_future_canonical_migration15(self):
        self.assertFalse((STAGED_MIGRATION.parent / '15.sqm').exists())
    def test_40_after_audit_pending_and_resolved_distinct_urls_can_coexist(self):
        self.populated();seed_link(self.db,child_id=None,source=88,url='/pending')
        self.db.commit();self.assertEqual(audit_existing_links(self.db),())
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'PASS_IN_MEMORY_ONLY')
    def test_41_future_duplicate_parent_uuid_collision_not_resolved_by_title(self):
        self.populated();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(json.dumps({UUID_KEY:U1}).encode(),));self.db.commit()
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'BLOCKED_READ_ONLY')
    def test_42_physical_unique_indexes_do_not_delete_legacy_rows(self):
        self.populated();seed_link(self.db,child_id=None,source=88,url='/pending')
        self.db.commit();before={t:self.db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('mangas','merged')}
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'PASS_IN_MEMORY_ONLY')
        self.assertEqual(before,{t:self.db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('mangas','merged')})

    def test_43_actual_sql_schema_matches_migration14_normalized(self):
        self.assertEqual(ddl_from_merged_sq().strip(), STAGED_MIGRATION.read_text().strip())
    def test_44_actual_insert_returning_id_is_idempotent(self):
        import re
        text=STAGED_SQL.read_text()
        sql=re.search(r'(?ms)^insertReturningId:\s*\n(.*?;)', text).group(1)
        self.populated()
        params={'infoManga':1,'getChapterUpdates':1,'chapterSortMode':2,'chapterPriority':1,
            'downloadChapters':0,'mergeId':500,'mergeUrl':'merged://polaris/500',
            'mangaId':101,'mangaUrl':'/real/101','mangaSource':77}
        self.assertIsNone(self.db.execute(sql,params).fetchone())
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],1)
    def test_45_actual_staged_select_includes_root_by_design(self):
        import re
        self.populated()
        seed_link(self.db,500,500,6969,'merged://polaris/500',priority=2147483647)
        sql=re.search(r'(?ms)^selectMergedMangasById:\s*\n(.*?;)',STAGED_SQL.read_text()).group(1)
        rows=self.db.execute(sql,(500,)).fetchall()
        self.assertEqual({r[0] for r in rows},{101,500})
    def test_46_audit_catches_blank_pending_identity(self):
        self.populated();seed_link(self.db,500,None,88,'')
        self.db.commit()
        self.assertIn('INVALID_LINK_IDENTITY',audit_existing_links(self.db))
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'BLOCKED_READ_ONLY')
    def test_47_root_deleted_with_existing_new_ledger_cascades_all(self):
        self.populated();seed_link(self.db,500,500,6969,'merged://polaris/500',priority=2147483647)
        self.db.commit();self.upgrade()
        self.db.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(U1,500,'hash'))
        self.db.execute('DELETE FROM mangas WHERE _id=500');self.db.commit()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas WHERE _id=101').fetchone()[0],1)

    def test_48_stale_merge_parent_url_fail_closed(self):
        self.populated()
        self.db.execute("UPDATE merged SET merge_url='merged://other/100' WHERE merge_id=500")
        self.db.commit()
        self.assertIn('STALE_MERGE_PARENT_URL',audit_existing_links(self.db))
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'BLOCKED_READ_ONLY')
    def test_49_ambiguous_physical_real_child_source_and_url_refused(self):
        self.populated()
        self.db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                        (103,77,'/real/101','Different local row',0,1,1,0,0,0,0))
        self.db.commit()
        self.assertIn('AMBIGUOUS_SOURCE_ROW',audit_existing_links(self.db))
        self.assertEqual(in_memory_rehearsal(self.db)['status'],'BLOCKED_READ_ONLY')

if __name__=='__main__':unittest.main()
