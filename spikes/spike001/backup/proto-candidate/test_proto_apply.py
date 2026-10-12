import tempfile
from pathlib import Path
import unittest
from apply_backup_proto_candidate import stage, blob_sha, PINNED_BACKUP_GIT_BLOB

HERE = Path(__file__).resolve().parent

class ApplyBackupProtoCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old = self.root / 'Backup.kt'
        self.old.write_bytes((HERE / 'Backup.pinned.kt').read_bytes())
        self.model = HERE / 'BackupPolarisBundle.kt'
        self.output = self.root / 'output'

    def test_exact_pinned_blob_is_verified(self):
        self.assertEqual(blob_sha(self.old.read_bytes()), PINNED_BACKUP_GIT_BLOB)

    def test_produces_extra_field_and_new_model_in_separate_output(self):
        a,b = stage(self.old, self.model, self.output)
        self.assertIn('@ProtoNumber(107) var polaris: BackupPolarisBundle? = null', a.read_text())
        self.assertEqual(b.read_bytes(), self.model.read_bytes())
        self.assertEqual(blob_sha(self.old.read_bytes()),PINNED_BACKUP_GIT_BLOB)

    def test_original_six_proto_numbers_unchanged(self):
        a,_ = stage(self.old, self.model, self.output)
        import re
        self.assertEqual([int(x) for x in re.findall(r'(?m)^\s*@ProtoNumber\((\d+)\) (?:val|var)', a.read_text())], [1,2,101,104,105,106,107])

    def test_wrong_upstream_blob_fails_without_creating_output(self):
        self.old.write_text(self.old.read_text()+'// unrelated change\n')
        with self.assertRaises(ValueError): stage(self.old, self.model, self.output)
        self.assertFalse(self.output.exists())

    def test_repeated_stage_never_overwrites_output(self):
        stage(self.old, self.model, self.output)
        with self.assertRaises(FileExistsError): stage(self.old, self.model, self.output)

    def test_modified_or_missing_model_fails_before_mutation(self):
        broken = self.root / 'bad.kt';broken.write_text('data class BackupPolarisBundle()')
        with self.assertRaises(ValueError): stage(self.old, broken, self.output)
        self.assertFalse(self.output.exists())

    def test_source_can_include_signed_negative_source_ids(self):
        self.assertIn('sourceId: Long', self.model.read_text())
        self.assertNotIn('sourceId: UInt',self.model.read_text())

if __name__ == '__main__': unittest.main()
