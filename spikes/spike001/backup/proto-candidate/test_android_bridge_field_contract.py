"""Fail-closed host check: staged exporter, Backup and restorer share ProtoBuf field #107.

Static shape checks, NOT genuine Kotlin/ProtoBuf code generation.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / 'restore-candidate/android-bridge/Backup.staged.kt'
RESTORER = ROOT / 'restore-candidate/android-bridge/BackupRestorer.staged.kt'
CREATOR = ROOT / 'yomotsu-candidate/BackupCreator.staged.kt'
PROTO_PATCHER = ROOT / 'proto-candidate/apply_backup_proto_candidate.py'


class StagedBackupField107Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backup = BACKUP.read_text()
        cls.restorer = RESTORER.read_text()
        cls.creator = CREATOR.read_text()
        cls.patcher = PROTO_PATCHER.read_text()

    def test_optional_field_is_unique_number_107_named_polaris(self):
        fields = re.findall(r'@ProtoNumber\(107\)\s+(?:val|var)\s+(\w+):\s+BackupPolarisBundle\?\s*=\s*null', self.backup)
        self.assertEqual(fields, ['polaris'])
        self.assertEqual(self.backup.count('@ProtoNumber(107)'), 1)

    def test_backup_creator_constructor_uses_existing_named_argument(self):
        self.assertRegex(self.creator, r'(?m)^\s+polaris\s*=\s*polarisBundle\s*,')
        self.assertNotRegex(self.creator, r'(?m)^\s+polarisBundle\s*=\s*polarisBundle')

    def test_backup_restorer_uses_the_same_property(self):
        self.assertRegex(self.restorer, r'\bval\s+polarisBundle\s*=\s*backup\.polaris\b')
        self.assertNotIn('backup.polarisBundle', self.restorer)

    def test_original_pinned_proto_patcher_uses_identical_name_and_tag(self):
        self.assertIn('@ProtoNumber(107) var polaris: BackupPolarisBundle? = null', self.patcher)

    def test_restorer_must_preflight_before_stock_jobs(self):
        self.assertIn('polarisLifecycle.restoreAfterDecodedPreflight(', self.restorer)
        self.assertIn('runStockYomotsuJobs()', self.restorer)
        self.assertIn('check(!options.libraryEntries || polarisBundle == null)', self.restorer)

    def test_legacy_archive_has_null_default(self):
        self.assertRegex(self.backup, r'polaris:\s*BackupPolarisBundle\?\s*=\s*null')


if __name__ == '__main__':
    unittest.main()
