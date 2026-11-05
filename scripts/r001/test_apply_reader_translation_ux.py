import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from apply_reader_translation_ux import PIN, apply

SOURCE = os.environ.get('POLARIS_YOMOTSU_CHECKOUT')


@unittest.skipUnless(SOURCE, 'Set POLARIS_YOMOTSU_CHECKOUT to the pinned checkout')
class ReaderOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'android'
        subprocess.run(['git', '-C', SOURCE, 'worktree', 'add', '--detach', str(self.root), PIN],
                       check=True, capture_output=True)

    def tearDown(self):
        subprocess.run(['git', '-C', SOURCE, 'worktree', 'remove', '--force', str(self.root)],
                       check=True, capture_output=True)
        self.temp.cleanup()

    def test_applies_and_repeated_application_is_read_only(self):
        self.assertEqual(apply(self.root)['status'], 'APPLIED')
        first = subprocess.check_output(['git', '-C', str(self.root), 'diff'])
        self.assertEqual(apply(self.root)['status'], 'ALREADY_APPLIED')
        self.assertEqual(subprocess.check_output(['git', '-C', str(self.root), 'diff']), first)

    def test_rejects_drift_without_overwriting_it(self):
        path = self.root / 'app/src/main/java/eu/kanade/translation/presentation/TranslationTextFit.kt'
        changed = path.read_text().replace('val wholeWords =', 'val customWords =')
        path.write_text(changed)
        with self.assertRaisesRegex(ValueError, 'source differs'):
            apply(self.root)
        self.assertEqual(path.read_text(), changed)
        self.assertFalse((self.root / 'app/src/main/java/eu/kanade/translation/PendingDownloadTranslations.kt').exists())

    def test_accepts_a_crlf_checkout_without_disabling_source_checks(self):
        subprocess.run(['git', '-C', str(self.root), 'config', 'core.autocrlf', 'true'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'checkout-index', '--all', '--force'],
                       check=True, capture_output=True)
        self.assertEqual(apply(self.root)['status'], 'APPLIED')
        self.assertEqual(apply(self.root)['status'], 'ALREADY_APPLIED')

    def test_does_not_cross_migration_gate(self):
        migration = self.root / 'data/src/main/sqldelight/tachiyomi/migrations/15.sqm'
        migration.write_text('-- test gate fixture\n')
        with self.assertRaisesRegex(ValueError, 'Migration15'):
            apply(self.root)
