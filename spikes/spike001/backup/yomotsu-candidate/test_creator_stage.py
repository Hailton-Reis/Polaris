import tempfile
from pathlib import Path
import unittest
from apply_backup_creator_candidate import PINNED_BLOB, git_blob_sha, render, stage

HERE = Path(__file__).resolve().parent


class PinnedYomotsuCreatorStageTests(unittest.TestCase):
    def setUp(self):
        self.pinned = HERE / "BackupCreator.pinned.kt"
        self.staged = HERE / "BackupCreator.staged.kt"

    def test_pinned_yomotsu_creator_blob_is_exact(self):
        self.assertEqual(git_blob_sha(self.pinned.read_bytes()), PINNED_BLOB)

    def test_staged_creator_is_byte_reproducible(self):
        self.assertEqual(render(self.pinned.read_bytes()).encode(), self.staged.read_bytes())

    def test_no_preexisting_top_level_107_changes_accidentally(self):
        # The generator is BackupCreator-only; Backup.kt is staged independently.
        self.assertNotIn("@ProtoNumber", self.staged.read_text())

    def test_real_source_supplements_are_included_in_backup_sources(self):
        content = self.staged.read_text()
        self.assertIn("backupSources(backupManga + polarisBundle?.supplementalManga.orEmpty())", content)

    def test_real_manga_options_are_forwarded_unchanged(self):
        content = self.staged.read_text()
        self.assertIn("polarisBackupExporter.collect(selectedManga, backupManga, options)", content)
        self.assertIn("val backupManga = backupMangas(selectedManga, options)", content)

    def test_previous_auto_backups_remain_until_success(self):
        content = self.staged.read_text()
        creation = content.split("file = if (isAutoBackup) {", 1)[1].split("} else {", 1)[0]
        self.assertNotIn(".listFiles", creation)
        self.assertIn(".drop(MAX_AUTO_BACKUPS)", content)
        self.assertNotIn(".drop(MAX_AUTO_BACKUPS - 1)", content)
        self.assertGreater(content.index(".drop(MAX_AUTO_BACKUPS)"),
                           content.index("BackupFileValidator(context).validate(fileUri)"))

    def test_multisource_validation_must_not_be_swallowed(self):
        content = self.staged.read_text()
        block = content.split("if (polarisBundle != null) {", 1)[1].split("} else {", 1)[0]
        self.assertIn("BackupFileValidator(context).validate(fileUri)", block)
        self.assertNotIn("runCatching", block)

    def test_original_file_drift_is_a_hard_error(self):
        with self.assertRaises(ValueError):
            render(self.pinned.read_bytes() + b"// different upstream\n")

    def test_stage_never_overwrites_files(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "BackupCreator.kt"
            stage(self.pinned, target)
            self.assertEqual(target.read_bytes(), self.staged.read_bytes())
            with self.assertRaises(FileExistsError):
                stage(self.pinned, target)

    def test_cannot_stage_into_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                stage(self.pinned, Path(d) / "absent" / "BackupCreator.kt")


if __name__ == "__main__":
    unittest.main()
