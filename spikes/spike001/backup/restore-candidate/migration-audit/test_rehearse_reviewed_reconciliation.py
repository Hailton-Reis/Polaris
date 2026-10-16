"""Host tests for explicit operator approval and reversible memory-only rehearsal."""
import contextlib
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from audit_legacy_merges import MEMO_KEY
from rehearse_reviewed_reconciliation import (
    FORMAT, STAGED_DDL, approval_template, fingerprint_database,
    rehearse_approved, main,
)
from test_audit_legacy_merges import seeded, link, UUID


class ApprovedMemoryReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.db = seeded()
        self.addCleanup(self.db.close)

    def duplicate(self, source=11):
        self.db.execute(
            'INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,'
            'download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) '
            'SELECT info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,'
            'download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source '
            'FROM merged WHERE manga_source=?', (source,))
        self.db.commit()
        return self.db.execute('SELECT max(_id) FROM merged').fetchone()[0]

    def approvals(self):
        self.db.commit()
        template=approval_template(self.db)
        return {**template, 'reviewed_by_operator': True,
                'approval_note': 'Confirmed identical source and settings after review',
                'approved_groups': template['available_exact_groups'][:]}

    def test_template_is_unsigned_and_never_approves_migration(self):
        self.duplicate()
        t=approval_template(self.db)
        self.assertEqual(t['format'], FORMAT)
        self.assertFalse(t['reviewed_by_operator'])
        self.assertEqual(t['approved_groups'],[])

    def test_approved_exact_duplicate_rehearses_and_undoes_all_rows(self):
        self.duplicate()
        baseline=fingerprint_database(self.db)
        result=rehearse_approved(self.db,self.approvals())
        self.assertEqual(result['simulation'],'PASS_IN_MEMORY_ONLY')
        self.assertTrue(result['restoration_verified'])
        self.assertFalse(result['migration_approved'])
        self.assertEqual(fingerprint_database(self.db),baseline)
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged').fetchone()[0],4)

    def test_two_independent_exact_groups_recover_both_full_rows(self):
        a=self.duplicate(11);b=self.duplicate(12)
        r=rehearse_approved(self.db,self.approvals())
        self.assertEqual(r['simulation'],'PASS_IN_MEMORY_ONLY')
        self.assertEqual(r['approved_remove_row_ids'],[a,b])
        self.assertTrue(r['restoration_verified'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM merged').fetchone()[0],5)

    def test_partial_approvals_leave_other_conflicts_and_block_ddl(self):
        self.duplicate(11);self.duplicate(12)
        a=self.approvals();a['approved_groups']=a['approved_groups'][:1]
        r=rehearse_approved(self.db,a)
        self.assertNotEqual(r['simulation'],'PASS_IN_MEMORY_ONLY')
        self.assertTrue(r['restoration_verified'])

    def test_rejection_when_no_review_note(self):
        self.duplicate();a=self.approvals();a['approval_note']='  '
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_operator_did_not_explicitly_review(self):
        self.duplicate();a=self.approvals();a['reviewed_by_operator']=False
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_of_unsigned_noop_approval_list(self):
        self.duplicate();a=self.approvals();a['approved_groups']=[]
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_reviewed_db_merged_row_has_changed(self):
        self.duplicate();a=self.approvals()
        self.db.execute('UPDATE merged SET chapter_priority=10 WHERE manga_source=12');self.db.commit()
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_unrelated_manga_memo_has_changed(self):
        self.duplicate();a=self.approvals()
        self.db.execute('UPDATE mangas SET memo=? WHERE _id=101',(b'{"unexpected":1}',));self.db.commit()
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_group_hash_edited(self):
        self.duplicate();a=self.approvals();a['approved_groups'][0]['group_sha256']='bogus'
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_keeper_swapped(self):
        self.duplicate();a=self.approvals();a['approved_groups'][0]['keeper']=999
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_removal_list_tampered(self):
        self.duplicate();a=self.approvals();a['approved_groups'][0]['candidate_removals']=[101]
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_group_repeated(self):
        self.duplicate();a=self.approvals();a['approved_groups'].append(a['approved_groups'][0].copy())
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_trying_to_choose_pending_vs_resolved(self):
        self.duplicate()
        a=self.approvals()
        self.db.execute('UPDATE merged SET manga_id=NULL WHERE _id=(SELECT MAX(_id) FROM merged)');self.db.commit()
        t=approval_template(self.db)
        a['database_rows_sha256']=t['database_rows_sha256']
        a['database_full_sha256']=t['database_full_sha256']
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_rejection_when_virtual_root_conflicts_even_exact(self):
        self.duplicate(6969)
        t=approval_template(self.db)
        self.assertEqual(t['available_exact_groups'],[])
        a={**t,'reviewed_by_operator':True,'approval_note':'root','approved_groups':[{'group_id':'conflict-1'}]}
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_altered_ddl_is_not_considered_pass(self):
        self.duplicate();a=self.approvals()
        ddl=STAGED_DDL.read_text().replace('CREATE UNIQUE INDEX IF NOT EXISTS polaris_merged_source_identity_unique','CREATE INDEX IF NOT EXISTS polaris_merged_source_identity_unique')
        r=rehearse_approved(self.db,a,ddl)
        self.assertEqual(r['reason_code'],'REQUIRED_CONSTRAINTS_ABSENT')
        self.assertTrue(r['restoration_verified'])

    def test_modified_ddl_with_other_unhandled_columns_is_caught(self):
        self.duplicate();a=self.approvals()
        r=rehearse_approved(self.db,a,STAGED_DDL.read_text()+'\nUPDATE mangas SET title="Modified";')
        self.assertFalse(r['restoration_verified'])
        self.assertNotEqual(r['simulation'],'PASS_IN_MEMORY_ONLY')
        self.assertEqual(self.db.execute('SELECT title FROM mangas WHERE _id=900').fetchone()[0],'Virtual')

    def test_foreign_key_to_merged_row_id_requires_manual_review(self):
        self.duplicate();a=self.approvals()
        self.db.execute('CREATE TABLE merged_references(merge_link_id INTEGER REFERENCES merged(_id))');self.db.commit()
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_trigger_attached_to_merged_requires_manual_review(self):
        self.duplicate();a=self.approvals()
        self.db.execute('CREATE TRIGGER track_merge_update AFTER DELETE ON merged BEGIN SELECT 1; END');self.db.commit()
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)

    def test_cli_template_and_simulation_never_approve_even_when_pass(self):
        self.duplicate()
        with TemporaryDirectory() as d:
            path=Path(d)/'db.sqlite';dest=sqlite3.connect(path);self.db.backup(dest);dest.close()
            b=path.read_bytes()
            template_path=Path(d)/'new-template.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path),'--template','--report',str(template_path)]),2)
            plan=json.loads(template_path.read_text())
            self.assertFalse(plan['reviewed_by_operator'])
            plan['approved_groups']=plan['available_exact_groups']
            plan['reviewed_by_operator']=True;plan['approval_note']='Checked exact duplicates'
            approval_path=Path(d)/'human.json';approval_path.write_text(json.dumps(plan))
            outcome=Path(d)/'outcome.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path),'--reviewed-approvals',str(approval_path),'--report',str(outcome)]),2)
            self.assertTrue(json.loads(outcome.read_text())['restoration_verified'])
            self.assertEqual(path.read_bytes(),b)

    def test_cli_refuses_existing_json_report_and_db_as_report(self):
        self.duplicate()
        with TemporaryDirectory() as d:
            db=Path(d)/'backup.json';dest=sqlite3.connect(db);self.db.backup(dest);dest.close()
            original=db.read_bytes()
            existing=Path(d)/'old.json';existing.write_text('DO NOT OVERWRITE')
            for report in (existing, db):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main([str(db),'--template','--report',str(report)]),3)
            self.assertEqual(db.read_bytes(),original)
            self.assertEqual(existing.read_text(),'DO NOT OVERWRITE')

    def test_approval_clones_do_not_leak_urls_or_titles_to_results(self):
        self.duplicate();a=self.approvals()
        r=rehearse_approved(self.db,a)
        rendered=json.dumps(r)
        self.assertNotIn('merged://900',rendered)
        self.assertNotIn('/a',rendered)
        self.assertNotIn('Virtual',rendered)

    def test_approval_format_mismatch_aborts(self):
        self.duplicate();a=self.approvals();a['format']='incorrect'
        with self.assertRaises(ValueError):rehearse_approved(self.db,a)


if __name__=='__main__':unittest.main()
