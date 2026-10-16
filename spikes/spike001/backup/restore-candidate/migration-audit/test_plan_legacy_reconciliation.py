"""Host-only legacy reconciliation planner and immutable SQLite clone tests."""
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
from plan_legacy_reconciliation import candidate_plan, simulate_exact_candidates, inspect_copy, main
from test_audit_legacy_merges import seeded, link, UUID


def expected_type(plan):
    return plan['review_groups'][0]['classification']


class LegacyReconciliationPlanTests(unittest.TestCase):
    def setUp(self):
        self.db = seeded()
        self.addCleanup(self.db.close)

    def duplicate(self, row_id=2, **overrides):
        # Clone the child source A link, including settings and pending state.
        self.db.row_factory = sqlite3.Row
        row = self.db.execute('SELECT * FROM merged WHERE manga_source=11').fetchone()
        values = {key:row[key] for key in row.keys() if key != '_id'}
        values.update(overrides)
        keys = list(values)
        self.db.execute(f'INSERT INTO merged({",".join(keys)}) VALUES({",".join("?" for _ in keys)})', [values[k] for k in keys])
        self.db.commit()
        return self.db.execute('SELECT MAX(_id) FROM merged').fetchone()[0]

    def file_copy(self, parent):
        path = Path(parent)/'copy.sqlite'
        target = sqlite3.connect(path)
        self.db.backup(target)
        target.close()
        return path

    def test_clean_rows_have_no_reconciliation_groups(self):
        plan=candidate_plan(self.db)
        self.assertTrue(plan['ready_for_review'])
        self.assertEqual(plan['summary']['groups'],0)
        self.assertFalse(plan['automatic_changes_permitted'])

    def test_exact_duplicate_is_only_proposed_for_review_not_deleted(self):
        row_id=self.duplicate()
        plan=candidate_plan(self.db)
        self.assertEqual(expected_type(plan),'EXACT_DUPLICATE_CANDIDATE_REVIEW')
        self.assertEqual(plan['review_groups'][0]['candidate_redundant_row_ids'],[row_id])
        self.assertTrue(plan['review_groups'][0]['manual_review_required'])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],4)

    def test_different_priority_never_auto_selected(self):
        self.duplicate(chapter_priority=123)
        plan=candidate_plan(self.db)
        self.assertEqual(expected_type(plan),'SETTINGS_OR_IDENTITY_MANUAL_REVIEW')
        self.assertIsNone(plan['review_groups'][0]['candidate_keep_row_id'])

    def test_mixed_pending_and_resolved_require_human_review(self):
        self.duplicate(manga_id=None)
        plan=candidate_plan(self.db)
        self.assertEqual(expected_type(plan),'PENDING_VS_RESOLVED_MANUAL_REVIEW')
        self.assertEqual(plan['review_groups'][0]['candidate_redundant_row_ids'],[])

    def test_different_sources_sharing_same_real_id_requires_review(self):
        self.duplicate(manga_source=13,manga_url='/different')
        self.assertEqual(expected_type(candidate_plan(self.db)),'REAL_IDENTITY_MANUAL_REVIEW')

    def test_root_duplications_are_always_manual_even_if_identical(self):
        self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) SELECT info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source FROM merged WHERE manga_source=6969')
        self.db.commit()
        self.assertEqual(expected_type(candidate_plan(self.db)),'VIRTUAL_ROOT_REVIEW_REQUIRED')

    def test_transitive_conflicts_are_a_single_review_group(self):
        self.duplicate(manga_id=None)
        self.duplicate(manga_source=13,manga_url='/different')
        plan=candidate_plan(self.db)
        self.assertEqual(plan['summary']['groups'],1)
        self.assertEqual(plan['summary']['rows_in_conflicts'],3)
        self.assertTrue(all(g['candidate_keep_row_id'] is None for g in plan['review_groups']))

    def test_same_child_identity_in_different_parents_is_allowed(self):
        self.db.execute('INSERT INTO mangas VALUES(901,6969,"merged://901","Virtual two",?)',(b'{}',))
        link(self.db,901,901,'merged://901',6969)
        link(self.db,901,101,'/a',11)
        self.db.commit()
        self.assertEqual(candidate_plan(self.db)['summary']['groups'],0)

    def test_no_sensitive_source_urls_or_titles_in_output(self):
        self.db.execute("UPDATE merged SET manga_url='/secret?bearer=abc' WHERE manga_source=11")
        self.duplicate()
        text=json.dumps(candidate_plan(self.db),ensure_ascii=False)
        self.assertNotIn('secret',text)
        self.assertNotIn('Virtual',text)
        self.assertNotIn('bearer',text)

    def test_plan_fingerprint_changes_on_settings_edit(self):
        self.duplicate()
        first=candidate_plan(self.db)['review_groups'][0]['row_fingerprint_sha256']
        self.db.execute('UPDATE merged SET chapter_priority=102 WHERE manga_source=11 LIMIT 1')
        self.db.commit()
        second=candidate_plan(self.db)['review_groups'][0]['row_fingerprint_sha256']
        self.assertNotEqual(first,second)

    def test_exact_clone_simulation_passes_after_only_candidate_removal(self):
        duplicate_id=self.duplicate()
        report=simulate_exact_candidates(self.db)
        self.assertEqual(report['simulation'],'PASS_IN_MEMORY_ONLY')
        self.assertEqual(report['candidate_removed_row_ids_in_memory_only'],[duplicate_id])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],4)

    def test_conflicting_settings_simulation_is_blocked_without_changes(self):
        self.duplicate(chapter_priority=9)
        report=simulate_exact_candidates(self.db)
        self.assertEqual(report['simulation'],'BLOCKED_IN_MEMORY_ONLY')
        self.assertEqual(report['candidate_removed_row_ids_in_memory_only'],[])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],4)

    def test_pending_resolved_conflict_never_drops_row_even_in_clone(self):
        self.duplicate(manga_id=None)
        self.assertEqual(simulate_exact_candidates(self.db)['candidate_removed_row_ids_in_memory_only'],[])

    def test_unreconciled_uuid_memo_still_blocks_clone_migration(self):
        self.duplicate()
        self.db.execute('UPDATE mangas SET memo=? WHERE _id=900', (json.dumps({MEMO_KEY:UUID}),))
        self.db.commit()
        result=simulate_exact_candidates(self.db)
        self.assertEqual(result['simulation'],'BLOCKED_IN_MEMORY_ONLY')
        self.assertIn('UUID_WITHOUT_MATCHING_LEDGER',result['remaining_blocker_codes'])

    def test_clone_catches_destructive_ddl(self):
        report=simulate_exact_candidates(self.db,ddl='DELETE FROM merged;')
        self.assertEqual(report['simulation'],'BLOCKED_IN_MEMORY_ONLY')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM merged').fetchone()[0],3)

    def test_file_remains_byte_identical_after_simulation(self):
        self.duplicate()
        with TemporaryDirectory() as folder:
            path=self.file_copy(folder)
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            report=inspect_copy(path,simulate=True)
            self.assertEqual(report['in_memory_simulation']['simulation'],'PASS_IN_MEMORY_ONLY')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_report_path_existing_file_fails_without_clobber(self):
        with TemporaryDirectory() as folder:
            dbpath=self.file_copy(folder)
            rpath=Path(folder)/'report.json'
            rpath.write_text('keep')
            with contextlib.redirect_stderr(io.StringIO()),contextlib.redirect_stdout(io.StringIO()):
                code=main([str(dbpath),'--report',str(rpath),'--simulate-exact'])
            self.assertEqual(code,3)
            self.assertEqual(rpath.read_text(),'keep')

    def test_cli_report_contains_redacted_review_groups(self):
        self.duplicate()
        with TemporaryDirectory() as folder:
            dbpath=self.file_copy(folder)
            dest=Path(folder)/'new-report.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(dbpath),'--simulate-exact','--report',str(dest)]),2)
            output=json.loads(dest.read_text())
            self.assertEqual(output['plan']['summary']['groups'],1)
            self.assertEqual(dest.stat().st_mode & 0o777,0o600)

    def test_clean_database_cli_returns_zero_when_no_review_needed(self):
        with TemporaryDirectory() as folder:
            dbpath=self.file_copy(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(dbpath),'--simulate-exact']),0)

    def test_untracked_uuid_returns_blocking_exit_without_duplicate_links(self):
        self.db.execute('UPDATE mangas SET memo=? WHERE _id=900', (json.dumps({MEMO_KEY:UUID}),))
        self.db.commit()
        with TemporaryDirectory() as folder:
            dbpath=self.file_copy(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(dbpath)]),2)

    def test_no_or_malformed_schema_never_claims_approval(self):
        c=sqlite3.connect(':memory:')
        self.addCleanup(c.close)
        self.assertFalse(candidate_plan(c)['ready_for_review'])
        self.assertEqual(simulate_exact_candidates(c)['simulation'],'BLOCKED')

    def test_dataset_with_multiple_exact_components_is_deterministic(self):
        self.duplicate()
        self.db.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) SELECT info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source FROM merged WHERE manga_source=12')
        self.db.commit()
        report=candidate_plan(self.db)
        self.assertEqual(report['summary']['groups'],2)
        self.assertEqual([g['classification'] for g in report['review_groups']],['EXACT_DUPLICATE_CANDIDATE_REVIEW']*2)

if __name__ == '__main__':
    unittest.main()
