"""Additional v2 release-readiness checks: exact physical roots and ledger binding.

Host tests against the REAL authored Polaris migration14 and ledger DDL,
plus the previously verified pinned-Yomotsu-shaped SQLite fixture.
"""
import json
import sqlite3
import unittest
from audit_v2_readiness import audit_v2_restore_readiness, UUID_MEMO_KEY
from verify_layering import (new_baseline, apply_spike14, LEDGER_CANDIDATE,
                             seed_parent, seed_link, audit_existing_links)
U1 = '123e4567-e89b-42d3-a456-426614174000'
U2 = '123e4567-e89b-42d3-a456-426614174001'
GOOD_DIGEST = 'a' * 64

class V2PhysicalReadiness(unittest.TestCase):
    def setUp(self):
        self.db = new_baseline()
        self.addCleanup(self.db.close)
        apply_spike14(self.db)
        self.db.executescript(LEDGER_CANDIDATE.read_text())
        self.db.commit()

    def valid(self, *, id=500, child=101, uid=U1, root=True, ledger=True, claim=True):
        seed_parent(self.db, parent_id=id, child_id=child)
        seed_link(self.db, parent_id=id, child_id=child,
                  url=f'/real/{child}', source=77)
        if root:
            seed_link(self.db, parent_id=id, child_id=id, source=6969,
                      url=f'merged://polaris/{id}', priority=2147483647)
            self.db.execute('UPDATE merged SET info_manga=0, get_chapter_updates=0 WHERE merge_id=? AND manga_source=6969',(id,))
        if claim:
            self.db.execute('UPDATE mangas SET memo=? WHERE _id=?',
                            (json.dumps({UUID_MEMO_KEY:uid, 'other':{'preserved':True}}).encode(), id))
        if ledger:
            self.db.execute('INSERT INTO polaris_restore_ledger VALUES (?,?,?)',
                            (uid, id, GOOD_DIGEST))
        # Normal UUID-stable restored parent: source+URL reflects archive UUID;
        # merged.merge_url and self-link manga_url must be updated too.
        if uid and claim:
            target='merged://polaris/'+uid
            self.db.execute('UPDATE mangas SET url=? WHERE _id=?',(target,id))
            self.db.execute('UPDATE merged SET merge_url=? WHERE merge_id=?',(target,id))
            self.db.execute('UPDATE merged SET manga_url=? WHERE merge_id=? AND manga_source=6969',(target,id))
        self.db.commit()

    def reasons(self):
        before=list(self.db.iterdump())
        got=audit_v2_restore_readiness(self.db)
        self.assertEqual(before,list(self.db.iterdump()),'audit changed live database')
        return set(got)

    def has(self, reason):
        self.assertIn(reason,self.reasons())
    def clean(self):
        self.assertEqual(self.reasons(),set())

    def test_01_fresh_db_with_empty_ledger_is_ready(self): self.clean()
    def test_02_valid_uuid_parent_with_root_child_and_digest(self): self.valid();self.clean()
    def test_03_multiple_distinct_canonical_uuids_valid(self):
        self.valid();self.valid(id=600,child=102,uid=U2);self.clean()
    def test_04_legitimate_legacy_manual_parent_without_uuid_still_valid(self):
        self.valid(claim=False,ledger=False);self.clean()
    def test_05_pending_child_null_is_valid(self):
        self.valid();self.db.execute('UPDATE merged SET manga_id=NULL WHERE manga_source=77');self.db.commit();self.clean()
    def test_06_pending_child_can_stay_null_after_real_source_exists(self):
        self.valid();self.db.execute('UPDATE merged SET manga_id=NULL WHERE manga_source=77');self.db.commit();self.clean()
    def test_07_missing_ledger_table_blocks(self):
        self.db.execute('DROP TABLE polaris_restore_ledger');self.db.commit();self.has('REQUIRED_RESTORE_TABLE_MISSING')
    def test_08_missing_merged_table_blocks(self):
        self.db.execute('DROP TABLE merged');self.db.commit();self.has('REQUIRED_RESTORE_TABLE_MISSING')
    def test_09_missing_virtual_root_rejected(self):
        self.valid(root=False);self.has('ROOT_REFERENCE_CARDINALITY')
    def test_10_original_layering_audit_did_not_reject_missing_root(self):
        self.valid(root=False)
        self.assertEqual(audit_existing_links(self.db),())
        self.has('ROOT_REFERENCE_CARDINALITY')
    def test_11_duplicate_root_unpatched_database_fails(self):
        self.valid();self.db.execute('DROP INDEX polaris_merged_source_identity_unique')
        self.db.execute('DROP INDEX polaris_merged_real_id_unique')
        seed_link(self.db,parent_id=500,child_id=500,source=6969,url='merged://polaris/500')
        # duplicate row is already untrustworthy; no attempt to choose one
        self.db.commit();self.has('ROOT_REFERENCE_CARDINALITY')
    def test_12_root_points_at_wrong_local_manga(self):
        self.valid();self.db.execute('UPDATE merged SET manga_id=NULL WHERE manga_source=6969');self.db.commit();self.has('ROOT_REFERENCE_IDENTITY')
    def test_13_root_has_wrong_saved_url(self):
        self.valid();self.db.execute("UPDATE merged SET manga_url='merged://foreign' WHERE manga_source=6969");self.db.commit();self.has('ROOT_REFERENCE_IDENTITY')
    def test_14_root_must_not_own_info_metadata(self):
        self.valid();self.db.execute('UPDATE merged SET info_manga=1 WHERE manga_source=6969');self.db.commit();self.has('ROOT_REFERENCE_IDENTITY')
    def test_15_wrong_root_merged_source_id(self):
        self.valid();self.db.execute('UPDATE merged SET manga_source=999 WHERE manga_source=6969');self.db.commit();self.has('ROOT_REFERENCE_CARDINALITY')
    def test_16_real_child_claiming_parent_as_source_manga(self):
        self.valid();self.db.execute('UPDATE merged SET manga_source=6969 WHERE manga_source=77');self.db.commit();self.has('ROOT_REFERENCE_IDENTITY')
    def test_17_changed_parent_url_rejected(self):
        self.valid();self.db.execute("UPDATE mangas SET url='merged://changed' WHERE _id=500");self.db.commit();self.has('MERGE_URL_DRIFT')
    def test_18_changed_merge_url_rejected(self):
        self.valid();self.db.execute("UPDATE merged SET merge_url='merged://changed' WHERE manga_source=77");self.db.commit();self.has('MERGE_URL_DRIFT')
    def test_19_parent_source_changed_to_real_rejected(self):
        self.valid();self.db.execute('UPDATE mangas SET source=77 WHERE _id=500');self.db.commit();self.has('MERGE_PARENT_WRONG_SOURCE')
    def test_20_missing_virtual_parent_memo_object_rejected(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(b'not-json',));self.db.commit();self.has('INVALID_PARENT_MEMO')
    def test_21_virtual_parent_memo_json_array_rejected(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(b'[]',));self.db.commit();self.has('INVALID_PARENT_MEMO')
    def test_22_invalid_uuid_memo_type_rejected(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(json.dumps({UUID_MEMO_KEY:12}).encode(),));self.db.commit();self.has('INVALID_UUID_MEMO')
    def test_23_uppercase_uuid_memo_rejected_as_noncanonical(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(json.dumps({UUID_MEMO_KEY:U1.upper()}).encode(),));self.db.commit();self.has('INVALID_UUID_MEMO')
    def test_24_uuid_memo_and_ledger_disagree(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(json.dumps({UUID_MEMO_KEY:U2}).encode(),));self.db.commit();self.has('LEDGER_MEMO_DISAGREEMENT')
    def test_25_uuid_memo_without_ledger_rejected(self):
        self.valid(ledger=False);self.has('UUID_CLAIM_WITHOUT_LEDGER')
    def test_26_ledger_without_uuid_memo_rejected(self):
        self.valid(claim=False);self.has('LEDGER_MEMO_DISAGREEMENT')
    def test_27_ledger_parent_url_must_have_stable_uuid(self):
        self.valid();self.db.execute("UPDATE mangas SET url='merged://polaris/custom' WHERE _id=500");self.db.execute("UPDATE merged SET merge_url='merged://polaris/custom' WHERE merge_id=500");self.db.execute("UPDATE merged SET manga_url='merged://polaris/custom' WHERE manga_source=6969");self.db.commit();self.has('LEDGER_PARENT_URL_DRIFT')
    def test_28_bad_digest_length_rejected(self):
        self.valid();self.db.execute("UPDATE polaris_restore_ledger SET archive_digest='abc'");self.db.commit();self.has('INVALID_ARCHIVE_DIGEST')
    def test_29_digest_uppercase_rejected(self):
        self.valid();self.db.execute("UPDATE polaris_restore_ledger SET archive_digest=?",('A'*64,));self.db.commit();self.has('INVALID_ARCHIVE_DIGEST')
    def test_30_digest_true_sha256_lowercase_valid(self): self.valid();self.clean()
    def test_31_invalid_ledger_uuid_rejected(self):
        self.valid();self.db.execute("UPDATE polaris_restore_ledger SET archive_uuid='not-uuid'");self.db.commit();self.has('INVALID_LEDGER_UUID')
    def test_32_ledger_parent_deleted_physically_cascades_no_false_positive(self):
        self.valid();self.db.execute('DELETE FROM mangas WHERE _id=500');self.db.commit();self.clean()
    def test_33_missing_resolved_child_is_bad_if_fk_is_disabled(self):
        self.valid();self.db.commit();self.db.execute('PRAGMA foreign_keys=OFF');self.db.execute('DELETE FROM mangas WHERE _id=101');self.db.commit();self.has('REAL_CHILD_IDENTITY_CONFLICT')
    def test_34_source_child_changes_url_rejected(self):
        self.valid();self.db.execute("UPDATE mangas SET url='/moved' WHERE _id=101");self.db.commit();self.has('REAL_CHILD_IDENTITY_CONFLICT')
    def test_35_source_child_changes_source_rejected(self):
        self.valid();self.db.execute('UPDATE mangas SET source=88 WHERE _id=101');self.db.commit();self.has('REAL_CHILD_IDENTITY_CONFLICT')
    def test_36_ambiguous_real_source_url_rejected(self):
        self.valid();self.db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES (102,77,\'/real/101\',\'Duplicate\',0,1,1,0,0,0,0)');self.db.commit();self.has('REAL_CHILD_IDENTITY_CONFLICT')
    def test_37_pending_real_child_keeps_saved_source_provenance(self):
        self.valid();self.db.execute('DELETE FROM mangas WHERE _id=101');self.db.commit()
        self.assertEqual(self.db.execute('SELECT manga_id,manga_source,manga_url FROM merged WHERE manga_source=77').fetchone(),(None,77,'/real/101'))
        self.clean()
    def test_38_invalid_blank_saved_child_url_rejected(self):
        self.valid();self.db.execute("UPDATE merged SET manga_url='' WHERE manga_source=77");self.db.commit();self.has('INVALID_CHILD_IDENTITY')
    def test_39_invalid_blank_parent_url_rejected(self):
        self.valid();self.db.execute("UPDATE mangas SET url='' WHERE _id=500");self.db.commit();self.has('INVALID_PARENT_URL')
    def test_40_virtual_parent_with_no_any_links_is_not_release_ready(self):
        seed_parent(self.db);self.db.commit();self.has('ROOT_REFERENCE_CARDINALITY')
    def test_41_foreign_key_check_detects_broken_parent_fk(self):
        self.valid();self.db.commit();self.db.execute('PRAGMA foreign_keys=OFF')
        self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(0,1,2,0,0,999,\'merged://unknown\',NULL,\'/pending\',77)')
        self.db.commit();self.has('FOREIGN_KEY_VIOLATION')
    def test_42_uuid_meta_keys_must_not_be_erased(self):
        self.valid();self.assertIn('other',json.loads(self.db.execute('SELECT memo FROM mangas WHERE _id=500').fetchone()[0]));self.clean()

    def test_43_duplicate_virtual_parent_url_rejected(self):
        self.valid();self.valid(id=600,child=102,uid=U2,claim=False,ledger=False)
        current=self.db.execute('SELECT url FROM mangas WHERE _id=500').fetchone()[0]
        self.db.execute('UPDATE mangas SET url=? WHERE _id=600',(current,))
        self.db.execute('UPDATE merged SET merge_url=? WHERE merge_id=600',(current,))
        self.db.execute('UPDATE merged SET manga_url=? WHERE merge_id=600 AND manga_source=6969',(current,))
        self.db.commit();self.has('DUPLICATE_VIRTUAL_URL')
    def test_44_second_parent_claims_same_archive_uuid(self):
        self.valid();self.valid(id=600,child=102,uid=U2,claim=False,ledger=False)
        self.db.execute('UPDATE mangas SET memo=? WHERE _id=600',(json.dumps({UUID_MEMO_KEY:U1}).encode(),))
        self.db.commit();self.has('DUPLICATE_UUID_CLAIM')
    def test_45_uuid_ledger_attached_to_real_manga_id(self):
        self.valid();self.db.execute('UPDATE polaris_restore_ledger SET parent_manga_id=101')
        self.db.commit();self.has('INVALID_LEDGER_PARENT')
    def test_46_unknown_nested_memo_keys_do_not_invalidate_uuid(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',
            (json.dumps({UUID_MEMO_KEY:U1,'deep':{'array':[1,{'value':'x'}]}}).encode(),))
        self.db.commit();self.clean()
    def test_47_noncanonical_uppercase_ledger_uuid_rejected(self):
        self.valid();self.db.execute('UPDATE polaris_restore_ledger SET archive_uuid=?',(U1.upper(),))
        self.db.commit();self.has('INVALID_LEDGER_UUID')
    def test_48_binary_non_utf8_memo_is_not_silently_ignored(self):
        self.valid();self.db.execute('UPDATE mangas SET memo=? WHERE _id=500',(b'\xff\x80',))
        self.db.commit();self.has('INVALID_PARENT_MEMO')
    def test_49_audit_reason_codes_do_not_leak_uuid_or_source_url(self):
        self.valid();self.db.execute('UPDATE mangas SET url=? WHERE _id=500',
            ('https://private.example/secret?api_token=abc',))
        self.db.commit();result=str(self.reasons())
        self.assertNotIn(U1,result)
        self.assertNotIn('private.example',result)
        self.assertNotIn('api_token',result)

if __name__=='__main__':unittest.main(verbosity=2)
