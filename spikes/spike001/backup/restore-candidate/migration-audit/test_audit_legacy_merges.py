"""Read-only migration checks against a shape-compatible pinned Yomotsu schema."""
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest
from audit_legacy_merges import inspect_database, inspect_file, main, MEMO_KEY

SCHEMA = '''
CREATE TABLE mangas(_id INTEGER PRIMARY KEY,source INTEGER NOT NULL,url TEXT NOT NULL,
 title TEXT NOT NULL,memo BLOB NOT NULL DEFAULT '{}');
CREATE TABLE merged(_id INTEGER PRIMARY KEY,info_manga INTEGER NOT NULL,
 get_chapter_updates INTEGER NOT NULL,chapter_sort_mode INTEGER NOT NULL,chapter_priority INTEGER NOT NULL,
 download_chapters INTEGER NOT NULL,merge_id INTEGER NOT NULL,merge_url TEXT NOT NULL,
 manga_id INTEGER,manga_url TEXT NOT NULL,manga_source INTEGER NOT NULL,
 FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE SET NULL,
 FOREIGN KEY(merge_id) REFERENCES mangas(_id) ON DELETE CASCADE);
'''
UUID='123e4567-e89b-42d3-a456-426614174000'

def seeded():
    c=sqlite3.connect(':memory:')
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript(SCHEMA)
    c.executemany('INSERT INTO mangas(_id,source,url,title,memo) VALUES(?,?,?,?,?)', [
        (900,6969,'merged://900','Virtual',b'{}'), (101,11,'/a','A',b'{}'), (202,12,'/b','B',b'{}')])
    link(c,900,900,'merged://900',6969)
    link(c,900,101,'/a',11)
    link(c,900,202,'/b',12)
    c.commit()
    return c

def link(c,p,manga,url,source,info=0,merge_url=None):
    c.execute('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,'
      'download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(?,?,?,?,?,?,?,?,?,?)',
      (info,1,2,1,0,p,merge_url or f'merged://{p}',manga,url,source))

def codes(c): return [f['code'] for f in inspect_database(c)['findings']]

class MigrationAuditTests(unittest.TestCase):
    def setUp(self):
        self.c=seeded();self.addCleanup(self.c.close)
    def test_clean_legacy_parent_without_uuid_is_safe(self):
        report=inspect_database(self.c)
        self.assertTrue(report['safe_to_install_unique_indexes'])
        self.assertEqual(report['scanned']['merge_references'],3)
    def test_duplicate_pending_and_resolved_same_key_blocks_migration(self):
        link(self.c,900,None,'/a',11)
        self.assertIn('DUPLICATE_LINK_SOURCE_IDENTITY',codes(self.c))
    def test_duplicate_real_manga_id_blocks_migration_even_under_other_url(self):
        link(self.c,900,101,'/alias',99)
        self.assertIn('DUPLICATE_LINK_REAL_MANGA_ID',codes(self.c))
    def test_parent_legacy_uuid_without_ledger_needs_reconciliation(self):
        self.c.execute('UPDATE mangas SET memo=? WHERE _id=900',(json.dumps({MEMO_KEY:UUID}).encode(),))
        self.assertIn('UUID_WITHOUT_MATCHING_LEDGER',codes(self.c))
    def test_malformed_uuid_and_memo_are_blockers(self):
        self.c.execute('UPDATE mangas SET memo=? WHERE _id=900',(b'{broken-json',))
        self.assertIn('INVALID_VIRTUAL_MEMO',codes(self.c))
        self.c.execute('UPDATE mangas SET memo=? WHERE _id=900',(json.dumps({MEMO_KEY:'bad'}).encode(),))
        self.assertIn('INVALID_VIRTUAL_UUID',codes(self.c))
    def test_duplicate_uuid_across_virtual_parents_blocks_migration(self):
        memo=json.dumps({MEMO_KEY:UUID}).encode()
        self.c.execute('UPDATE mangas SET memo=? WHERE _id=900',(memo,))
        self.c.execute('INSERT INTO mangas VALUES(901,6969,"merged://901","Virtual 2",?)',(memo,))
        link(self.c,901,901,'merged://901',6969)
        self.assertIn('DUPLICATE_VIRTUAL_UUID',codes(self.c))
    def test_unknown_nonvirtual_parent_link_detected_even_if_fk_valid(self):
        link(self.c,101,202,'/b',12,merge_url='/a')
        self.assertIn('REFERENCE_PARENT_MISSING_OR_NONVIRTUAL',codes(self.c))
    def test_missing_root_detected(self):
        self.c.execute('DELETE FROM merged WHERE manga_source=6969')
        self.assertIn('VIRTUAL_ROOT_MISSING_OR_DUPLICATED',codes(self.c))
    def test_corrupt_root_reference_detected(self):
        self.c.execute('UPDATE merged SET info_manga=1 WHERE manga_source=6969')
        self.assertIn('INVALID_VIRTUAL_ROOT',codes(self.c))
    def test_wrong_parent_virtual_url_detected(self):
        self.c.execute("UPDATE merged SET merge_url='other' WHERE manga_source=11")
        self.assertIn('PARENT_URL_MISMATCH',codes(self.c))
    def test_reference_to_wrong_real_source_id_detected(self):
        self.c.execute('UPDATE merged SET manga_source=77 WHERE manga_source=11')
        self.assertIn('RESOLVED_CHILD_IDENTITY_AMBIGUOUS',codes(self.c))
    def test_duplicate_real_source_url_in_mangas_detected(self):
        self.c.execute('INSERT INTO mangas VALUES(303,11,"/a","Duplicate",?)',(b'{}',))
        self.assertIn('RESOLVED_CHILD_IDENTITY_AMBIGUOUS',codes(self.c))
    def test_deliberately_pending_link_is_not_auto_relinked(self):
        self.c.execute('UPDATE merged SET manga_id=NULL WHERE manga_source=11')
        self.assertTrue(inspect_database(self.c)['safe_to_install_unique_indexes'])
    def test_foreign_key_orphan_reported_if_old_database_has_broken_fk(self):
        self.c.execute('PRAGMA foreign_keys=OFF')
        link(self.c,900,999,'/lost',77)
        self.c.commit()
        self.assertIn('FOREIGN_KEY_VIOLATION',codes(self.c))
    def test_missing_required_tables_is_fail_closed(self):
        c=sqlite3.connect(':memory:');self.addCleanup(c.close)
        self.assertIn('REQUIRED_SCHEMA_MISSING',codes(c))
    def test_readonly_audit_leaves_file_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'live-copy.sqlite'
            dest=sqlite3.connect(path)
            self.c.backup(dest);dest.close()
            before=hashlib.sha256(path.read_bytes()).digest()
            self.assertTrue(inspect_file(path)['safe_to_install_unique_indexes'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(),before)
    def test_report_redacts_source_urls_titles_and_uuid_tokens(self):
        self.c.execute('UPDATE mangas SET url=? WHERE _id=101',('/?secretToken=abcdef',))
        report=json.dumps(inspect_database(self.c))
        self.assertNotIn('secretToken',report)
        self.assertNotIn('Virtual',report)
    def test_ledger_with_uuid_mem_match_allowed(self):
        self.c.execute('UPDATE mangas SET memo=? WHERE _id=900',(json.dumps({MEMO_KEY:UUID}).encode(),))
        self.c.execute('CREATE TABLE polaris_restore_ledger(archive_uuid TEXT PRIMARY KEY,parent_manga_id INTEGER UNIQUE,archive_digest TEXT NOT NULL,FOREIGN KEY(parent_manga_id) REFERENCES mangas(_id))')
        self.c.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(UUID,900,'abcd'))
        self.assertTrue(inspect_database(self.c)['safe_to_install_unique_indexes'])
    def test_ledger_parent_without_memo_detected(self):
        self.c.execute('CREATE TABLE polaris_restore_ledger(archive_uuid TEXT PRIMARY KEY,parent_manga_id INTEGER UNIQUE,archive_digest TEXT NOT NULL)')
        self.c.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?)',(UUID,900,'abcd'))
        self.assertIn('LEDGER_UUID_NOT_IN_PARENT_MEMO',codes(self.c))
    def test_readonly_cli_writes_only_explicit_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbpath=Path(tmp)/'db.sqlite';report=Path(tmp)/'report.json'
            dest=sqlite3.connect(dbpath);self.c.backup(dest);dest.close()
            before=hashlib.sha256(dbpath.read_bytes()).hexdigest()
            self.assertEqual(main([str(dbpath),'--report',str(report)]),0)
            self.assertTrue(report.exists())
            self.assertEqual(hashlib.sha256(dbpath.read_bytes()).hexdigest(),before)

if __name__=='__main__':unittest.main()
