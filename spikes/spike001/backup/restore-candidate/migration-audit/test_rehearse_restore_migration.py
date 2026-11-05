"""Host-only tests: never write the source database during DDL rehearsal."""
import contextlib
import hashlib
import io
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from audit_legacy_merges import main as audit_main, save_report_without_overwrite
from rehearse_restore_migration import (DEFAULT_DDL, inspect_copy, main, rehearse_connection)
from test_audit_legacy_merges import seeded, link, UUID, MEMO_KEY


class MigrationRehearsalSafetyTests(unittest.TestCase):
    def setUp(self):
        self.source = seeded()
        self.addCleanup(self.source.close)
        self.sql = DEFAULT_DDL.read_text()

    def rehearse(self, code=None):
        self.source.commit()
        return rehearse_connection(self.source, self.sql if code is None else code)

    def test_clean_legacy_source_passes_only_on_memory_clone(self):
        r = self.rehearse()
        self.assertTrue(r['safe_to_install_unique_indexes'])
        self.assertEqual(r['rehearsal'], 'PASS_IN_MEMORY_ONLY')
        self.assertFalse(r['live_database_modified'])

    def test_source_schema_and_original_rows_are_not_changed(self):
        before = self.source.iterdump()
        original = '\n'.join(before)
        self.rehearse()
        self.assertEqual('\n'.join(self.source.iterdump()), original)

    def test_duplicate_pending_resolved_links_abort_before_ddl(self):
        link(self.source, 900, None, '/a', 11)
        r = self.rehearse()
        self.assertEqual(r['rehearsal'], 'BLOCKED')
        self.assertEqual(r['reason_code'], 'LEGACY_AUDIT_BLOCKER')

    def test_preledger_uuid_requires_manual_reconciliation(self):
        self.source.execute('UPDATE mangas SET memo=? WHERE _id=900',
                            ('{"polaris.merge.work.uuid":"' + UUID + '"}',))
        self.assertEqual(self.rehearse()['rehearsal'], 'BLOCKED')

    def test_wrong_parent_root_rejected_before_migration(self):
        self.source.execute('DELETE FROM merged WHERE manga_source=6969')
        self.assertEqual(self.rehearse()['reason_code'], 'LEGACY_AUDIT_BLOCKER')

    def test_malformed_sql_fails_without_modifying_source(self):
        self.assertEqual(self.rehearse('CREATE INDEX')['reason_code'], 'DDL_REHEARSAL_FAILED')
        self.assertEqual(self.source.execute('SELECT COUNT(*) FROM merged').fetchone()[0], 3)

    def test_missing_required_index_is_detected_after_ddl(self):
        ddl = self.sql.replace(
            'CREATE UNIQUE INDEX IF NOT EXISTS polaris_merged_source_identity_unique',
            'CREATE INDEX IF NOT EXISTS polaris_merged_source_identity_unique')
        self.assertEqual(self.rehearse(ddl)['reason_code'], 'REQUIRED_CONSTRAINTS_ABSENT')

    def test_bad_partial_unique_index_is_detected(self):
        ddl = self.sql.replace('ON merged(merge_id, manga_id) WHERE manga_id IS NOT NULL;',
                               'ON merged(merge_id, manga_id);')
        self.assertEqual(self.rehearse(ddl)['reason_code'], 'REQUIRED_CONSTRAINTS_ABSENT')

    def test_preexisting_wrong_ledger_table_is_not_silently_accepted(self):
        self.source.execute('CREATE TABLE polaris_restore_ledger (archive_uuid TEXT PRIMARY KEY, parent_manga_id INTEGER, archive_digest TEXT)')
        self.assertEqual(self.rehearse()['reason_code'], 'REQUIRED_CONSTRAINTS_ABSENT')

    def test_rehearsal_detects_destructive_ddl_attempt(self):
        self.assertEqual(self.rehearse('DELETE FROM merged;\n' + self.sql)['reason_code'],
                         'ORIGINAL_ROWS_CHANGED_IN_REHEARSAL')
        self.assertEqual(self.source.execute('SELECT COUNT(*) FROM merged').fetchone()[0], 3)

    def test_report_cannot_replace_original_sqlite_even_with_json_extension(self):
        with TemporaryDirectory() as d:
            path = Path(d) / 'database.json'
            dest = sqlite3.connect(path)
            self.source.backup(dest)
            dest.close()
            before = hashlib.sha256(path.read_bytes()).digest()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(path), '--report', str(path)]), 3)
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), before)

    def test_report_symlink_to_existing_database_is_rejected(self):
        with TemporaryDirectory() as d:
            db = Path(d) / 'db.sqlite'
            target = Path(d) / 'my-report.json'
            dest = sqlite3.connect(db)
            self.source.backup(dest)
            dest.close()
            target.symlink_to(db)
            with self.assertRaises((ValueError, FileExistsError)):
                save_report_without_overwrite(db, target, '{}')
            self.assertNotEqual(db.stat().st_size, 2)

    def test_report_hard_link_to_database_is_rejected(self):
        with TemporaryDirectory() as d:
            db = Path(d) / 'db.sqlite'
            target = Path(d) / 'my-report.json'
            dest = sqlite3.connect(db)
            self.source.backup(dest)
            dest.close()
            os.link(db, target)
            before = db.read_bytes()
            with self.assertRaises(FileExistsError):
                save_report_without_overwrite(db, target, '{}')
            self.assertEqual(db.read_bytes(), before)

    def test_existing_report_does_not_get_overwritten(self):
        with TemporaryDirectory() as d:
            path = Path(d) / 'audit.json'
            path.write_text('important')
            with self.assertRaises(FileExistsError):
                save_report_without_overwrite(Path(d) / 'db.sqlite', path, '{}')
            self.assertEqual(path.read_text(), 'important')

    def test_existing_database_sidecar_report_is_rejected(self):
        with TemporaryDirectory() as d:
            db = Path(d) / 'db.sqlite'
            for suffix in ('-wal', '-shm', '-journal'):
                with self.subTest(suffix=suffix):
                    with self.assertRaises(ValueError):
                        save_report_without_overwrite(db, Path(str(db) + suffix), '{}')

    def test_report_creation_is_exclusive_and_private(self):
        with TemporaryDirectory() as d:
            report = Path(d) / 'audit.json'
            save_report_without_overwrite(Path(d) / 'db.sqlite', report, '{"safe":true}')
            self.assertEqual(report.read_text(), '{"safe":true}\n')
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                save_report_without_overwrite(Path(d) / 'db.sqlite', report, '{"evil":true}')

    def test_read_only_file_rehearsal_does_not_change_db_bytes(self):
        with TemporaryDirectory() as d:
            path = Path(d) / 'db.sqlite'
            dest = sqlite3.connect(path)
            self.source.backup(dest)
            dest.close()
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(inspect_copy(path)['rehearsal'], 'PASS_IN_MEMORY_ONLY')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_rehearsal_report_redacts_urls_titles_and_uuids(self):
        self.source.execute("UPDATE mangas SET title='private title' WHERE _id=900")
        self.source.execute("UPDATE mangas SET url='https://secret.example?token=a' WHERE _id=101")
        self.source.commit()
        report = str(inspect_copy_from_memory(self.source, self.sql))
        self.assertNotIn('secret.example', report)
        self.assertNotIn('private title', report)
        self.assertNotIn(UUID, report)

    def test_audit_cli_also_rejects_overwriting_same_database(self):
        with TemporaryDirectory() as d:
            path = Path(d) / 'live.json'
            dest = sqlite3.connect(path)
            self.source.backup(dest)
            dest.close()
            before = path.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(audit_main([str(path), '--report', str(path)]), 3)
            self.assertEqual(path.read_bytes(), before)

    def test_missing_database_does_not_create_it(self):
        with TemporaryDirectory() as d:
            path = Path(d) / 'missing.sqlite'
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([str(path)]), 3)
            self.assertFalse(path.exists())


def inspect_copy_from_memory(c, ddl):
    c.commit()
    return rehearse_connection(c, ddl)


if __name__ == '__main__':
    unittest.main()
