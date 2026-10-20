"""Safe tests; no network or Git/Android process invoked."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SRC = Path(__file__).with_name('polaris_local.py')
spec = importlib.util.spec_from_file_location('polaris_local', SRC)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class LocalBuildTests(unittest.TestCase):
    def test_pinned_sha(self):
        self.assertEqual(len(p.PINNED), 40)
        self.assertEqual(p.PINNED, '0fb80c439ef816eeb50674f1b90af39918b176d8')

    def test_java_21(self):
        for v in ['openjdk version "21.0.8"', 'java version "21.0.1"', 'openjdk 21.0.5 2025-04-15']:
            self.assertTrue(p.java_is_21(v), v)

    def test_java_must_not_accept_17_or_22(self):
        for v in ['openjdk version "17.0.4"', 'openjdk version "22.0.2"', 'java version "1.8.0"']:
            self.assertFalse(p.java_is_21(v), v)

    def test_sdk_pins(self):
        self.assertIn('platforms/android-37', p.SDK_REQUIREMENTS)
        self.assertIn('ndk/28.2.13676358', p.SDK_REQUIREMENTS)
        self.assertIn('ndk/29.0.14206865', p.SDK_REQUIREMENTS)

    def test_evidence_new_dir_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dest = root/'existing'
            dest.mkdir()
            with self.assertRaisesRegex(RuntimeError, 'Não sobrescreverei'):
                p.choose_evidence_dir(root, dest)
            self.assertEqual(p.choose_evidence_dir(root, root/'free'), (root/'free').resolve())

    def test_shell_never_interpolates_user_paths(self):
        cmd = p.bash_prelude()
        self.assertIn('POLARIS_REPO', cmd)
        self.assertIn('POLARIS_EVIDENCE', cmd)
        self.assertIn('build_issue002.sh', cmd)
        self.assertNotIn('github.com', cmd)

    def test_root_layout(self):
        self.assertEqual(p.polaris_root(), SRC.resolve().parents[2])

    def test_check_argument_is_read_only(self):
        src = SRC.read_text()
        start = src.index('if args.action == "check":')
        end = src.index('if not shutil.which("git"):',start)
        self.assertNotIn('ensure_yomotsu(', src[start:end])
        self.assertNotIn('subprocess.run(', src[start:end])

if __name__=='__main__':
    unittest.main(verbosity=2)
