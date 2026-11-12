"""Exercise debug-only installation; no Android SDK required."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("apply_debug_hook.py")


class DebugHookInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.debug = self.repo / "app/src/debug/AndroidManifest.xml"
        self.debug.parent.mkdir(parents=True)
        self.debug.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
                              '  <application>\n'
                              '    </application>\n'
                              '</manifest>\n')
        self.release = self.repo / "app/src/main/AndroidManifest.xml"
        self.release.parent.mkdir(parents=True)
        self.release.write_text('<manifest><application/></manifest>\n')

    def run_installer(self):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.repo)],
                              capture_output=True, text=True)

    def test_debug_hook_is_only_in_debug_manifest(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ISSUE002_DEBUG_HOOK_APPLIED", result.stdout)
        data = self.debug.read_text()
        self.assertIn('android:name="eu.kanade.tachiyomi.polaris.Spike001DebugActivity"', data)
        self.assertIn('android:permission="android.permission.DUMP"', data)
        self.assertIn('android:exported="true"', data)
        self.assertEqual(self.release.read_text(), '<manifest><application/></manifest>\n')
        source = self.repo / "app/src/debug/java/eu/kanade/tachiyomi/polaris/Spike001DebugActivity.kt"
        self.assertTrue(source.exists())

    def test_second_install_fails_without_duplicate_or_overwrite(self):
        self.assertEqual(self.run_installer().returncode, 0)
        first = self.debug.read_text()
        again = self.run_installer()
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual(self.debug.read_text(), first)

    def test_unrecognized_manifest_fails_closed(self):
        initial = '<manifest><application /></manifest>'
        self.debug.write_text(initial)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.debug.read_text(), initial)

    def test_refuses_to_replace_existing_debug_source(self):
        src = self.repo / "app/src/debug/java/eu/kanade/tachiyomi/polaris/Spike001DebugActivity.kt"
        src.parent.mkdir(parents=True)
        src.write_text("user changes")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(src.read_text(), "user changes")
        self.assertNotIn("Spike001DebugActivity", self.debug.read_text())


if __name__ == "__main__": unittest.main()
