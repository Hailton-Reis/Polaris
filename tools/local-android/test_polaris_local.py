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
        self.assertIn('platforms/android-37.0', p.SDK_REQUIREMENTS)
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

    def test_build_script_keeps_original_yomotsu_checkout_clean(self):
        source = SRC.resolve().parents[2] / 'scripts/r001/build_issue002.sh'
        script = source.read_text(encoding='utf-8')
        self.assertIn('baseline_source=$(realpath ', script)
        self.assertIn('baseline="$evidence/baseline-yomotsu"', script)
        self.assertIn('patched="$evidence/patched-yomotsu"', script)
        self.assertIn('test ! -e "$evidence"', script)
        self.assertIn('git -C "$baseline_source" worktree add --detach "$baseline" "$pinned"', script)
        self.assertIn('git -C "$baseline_source" worktree add --detach "$patched" "$pinned"', script)
        self.assertIn('test -z "$(git -C "$baseline_source" status --porcelain)"', script)
        self.assertNotIn('prepare_branding "$baseline_source"', script)
        self.assertLess(script.index('worktree add --detach "$baseline"'), script.index('prepare_branding "$baseline"'))

    def test_isolated_git_worktrees_do_not_modify_pinned_source(self):
        import shutil
        import subprocess
        if not shutil.which('git'):
            self.skipTest('git unavailable')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'pinned'
            source.mkdir()
            def git(*args):
                return subprocess.run(['git', *args], check=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True).stdout.strip()
            git('-C', str(source), 'init', '-q')
            (source/'source.txt').write_text('pinned', encoding='utf-8')
            git('-C', str(source), 'add', 'source.txt')
            git('-C', str(source), '-c', 'user.name=Polaris Test',
                '-c', 'user.email=polaris@example.invalid', 'commit', '-qm', 'test')
            sha = git('-C', str(source), 'rev-parse', 'HEAD')
            for index in (1, 2):
                evidence = root / f'evidence-{index}'
                evidence.mkdir()
                for variant in ('baseline-yomotsu', 'patched-yomotsu'):
                    workspace = evidence / variant
                    git('-C', str(source), 'worktree', 'add', '--detach', str(workspace), sha)
                    (workspace/'generated-icon.png').write_bytes(b'generated icon')
                self.assertEqual('', git('-C', str(source), 'status', '--porcelain'))
                self.assertEqual(sha, git('-C', str(source), 'rev-parse', 'HEAD'))

    def test_apk_integrity_manifest_and_pinned_checkout_final_gate(self):
        source = SRC.resolve().parents[2] / 'scripts/r001/build_issue002.sh'
        script = source.read_text(encoding='utf-8')
        self.assertIn('sha256sum baseline/*.apk spike001/*.apk > SHA256SUMS.txt', script)
        self.assertIn('test -s "$evidence/apks/SHA256SUMS.txt"', script)
        self.assertIn('test -z "$(git -C "$baseline_source" status --porcelain)"', script)
        self.assertLess(script.index('sha256sum baseline/*.apk'),
                        script.index("printf 'APK_BUILDS_PASS_NO_NEW_UNIT_REGRESSIONS"))

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
