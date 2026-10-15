"""Guard isolated backup test compilation against accidental Gradle drift.

Static preflight only: passing this does not prove Gradle/Android execution.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
BACKUP_GRADLE = ROOT / "spikes" / "backup-lab" / "build.gradle.kts"
DOMAIN_GRADLE = ROOT / "spikes" / "domain-lab" / "build.gradle.kts"
CI = ROOT / ".github" / "workflows" / "domain-spikes.yml"


class BackupLabStructureTests(unittest.TestCase):
    def test_all_five_backup_source_roots_are_compiled(self):
        text = BACKUP_GRADLE.read_text(encoding="utf-8")
        for path in [
            "../spike001/backup",
            "../spike001/backup/proto-candidate",
            "../spike001/backup/proto-candidate/host-tests",
            "../spike001/backup/uuid-candidate",
            "../spike001/backup/uuid-candidate/host-tests",
        ]:
            with self.subTest(path=path):
                self.assertIn(f'"{path}"', text)
                self.assertTrue((BACKUP_GRADLE.parent / path).is_dir())

    def test_every_executable_main_is_registered_in_backup_lab(self):
        text = BACKUP_GRADLE.read_text(encoding="utf-8")
        for klass in [
            "MergedBackupRestorePlannerTestKt",
            "MergedBackupExportPlannerTestKt",
            "BackupPolarisBundleContractTestKt",
            "BackupPolarisBundleBuilderTestKt",
            "YomotsuMergedWorkUuidStoreTestKt",
        ]:
            with self.subTest(main=klass):
                self.assertIn(klass, text)
        self.assertIn("tasks.register(\"checkBackup\")", text)

    def test_domain_lab_does_not_reference_uncompiled_backup_classes(self):
        text = DOMAIN_GRADLE.read_text(encoding="utf-8")
        self.assertNotIn('"../spike001/backup"', text)
        for name in [
            "spike001Backup",
            "spike001BackupExport",
            "spike001ProtoModel",
            "spike001ProtoBuilder",
            "spike001UuidStore",
        ]:
            with self.subTest(task=name):
                self.assertNotIn(name, text)

    def test_workflow_runs_backup_lab_and_watches_its_changes(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn("gradle -p spikes/backup-lab checkBackup", text)
        self.assertEqual(text.count('"spikes/backup-lab/**"'), 2)

    def test_backup_lab_does_not_use_stub_source_as_production_main(self):
        text = BACKUP_GRADLE.read_text(encoding="utf-8")
        self.assertIn("sourceSets {\n    test {", text)
        self.assertNotIn("    main {\n        kotlin.srcDirs", text)


if __name__ == "__main__":
    unittest.main()
