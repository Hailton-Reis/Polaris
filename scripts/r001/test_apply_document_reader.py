import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from apply_document_reader import PIN, apply

SOURCE = os.environ.get('POLARIS_YOMOTSU_CHECKOUT')
PROJECT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(SOURCE, 'Set POLARIS_YOMOTSU_CHECKOUT to the pinned checkout')
class DocumentOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'android'
        subprocess.run(['git', '-C', SOURCE, 'worktree', 'add', '--detach', str(self.root), PIN],
                       check=True, capture_output=True)

    def tearDown(self):
        subprocess.run(['git', '-C', SOURCE, 'worktree', 'remove', '--force', str(self.root)],
                       check=True, capture_output=True)
        self.temp.cleanup()

    def prepare(self):
        for script in ['spikes/spike001/apply_spike001.py', 'scripts/r001/apply_debug_hook.py',
                       'scripts/r001/apply_reader_translation_ux.py']:
            subprocess.run([sys.executable, str(PROJECT / script), str(self.root)],
                           check=True, capture_output=True)

    def test_full_stack_application_and_idempotence(self):
        self.prepare()
        self.assertEqual(apply(self.root)['status'], 'APPLIED')
        subprocess.run(['git', '-C', str(self.root), 'add', '-N', '.'], check=True)
        first = subprocess.check_output(['git', '-C', str(self.root), 'diff', '--binary'])
        self.assertEqual(apply(self.root)['status'], 'ALREADY_APPLIED')
        self.assertEqual(subprocess.check_output(['git', '-C', str(self.root), 'diff', '--binary']), first)
        subprocess.run(['git', '-C', str(self.root), 'diff', '--check'], check=True)
        self.assertFalse((self.root / 'data/src/main/sqldelight/tachiyomi/migrations/15.sqm').exists())
        about = self.root / 'app/src/main/java/eu/kanade/presentation/more/settings/screen/about/AboutScreen.kt'
        self.assertIn('P20261104.2', about.read_text())
        self.assertTrue((self.root / 'app/src/main/java/eu/kanade/tachiyomi/ui/documents/DocumentOrganization.kt').exists())

    def test_drift_is_rejected_without_partial_application(self):
        self.prepare()
        path = self.root / 'source-local/src/main/kotlin/tachiyomi/source/local/io/Format.kt'
        text = path.read_text().replace('data class Epub', 'data class CustomEpub')
        path.write_text(text)
        with self.assertRaisesRegex(ValueError, 'source differs'):
            apply(self.root)
        self.assertEqual(path.read_text(), text)
        self.assertFalse((self.root / 'app/src/main/java/eu/kanade/tachiyomi/ui/documents/DocumentSearch.kt').exists())

    def test_crlf_stack(self):
        subprocess.run(['git', '-C', str(self.root), 'config', 'core.autocrlf', 'true'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'checkout-index', '--all', '--force'],
                       check=True, capture_output=True)
        self.prepare()
        self.assertEqual(apply(self.root)['status'], 'APPLIED')
        self.assertEqual(apply(self.root)['status'], 'ALREADY_APPLIED')

    def test_prerequisite_and_migration_gate(self):
        with self.assertRaisesRegex(ValueError, 'reader translation overlay'):
            apply(self.root)
        self.prepare()
        (self.root / 'data/src/main/sqldelight/tachiyomi/migrations/15.sqm').write_text('-- gate fixture\n')
        with self.assertRaisesRegex(ValueError, 'Migration15'):
            apply(self.root)
