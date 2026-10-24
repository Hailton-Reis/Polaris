import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SRC = Path(__file__).with_name('polaris_emulator.py')
spec = importlib.util.spec_from_file_location('polaris_emulator', SRC)
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def ok(output):
    return subprocess.CompletedProcess([], 0, output, '')


class EmulatorSafety(unittest.TestCase):
    def test_without_consent_cannot_run(self):
        self.assertEqual(e.main(['baseline', '--workspace', '/tmp']), 3)

    def test_find_device_rejects_physical_android(self):
        with patch.object(e, 'run', return_value=ok('List of devices attached\nABC123 device\n')):
            self.assertIsNone(e.find_device(Path('adb.exe')))

    def test_find_device_selects_only_named_polaris_avd(self):
        def stub(args, **kwargs):
            if args[-1] == 'devices':
                return ok('List of devices attached\nABC123 device\nemulator-5554 device\nemulator-5556 device\n')
            if 'emulator-5554' in args:
                return ok('Personal_Emulator\nOK\n')
            return ok(e.AVD + '\nOK\n')
        with patch.object(e, 'run', side_effect=stub):
            self.assertEqual(e.find_device(Path('adb.exe')), 'emulator-5556')

    def test_latest_complete_build_with_valid_apk_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            work = Path(d)
            root = work / 'PolarisLocal' / 'evidence' / 'issue002-20261023-190348'
            (root / 'apks' / 'baseline').mkdir(parents=True)
            (root / 'apks' / 'spike001').mkdir()
            old = root / 'apks' / 'baseline' / 'a.apk'
            new = root / 'apks' / 'spike001' / 'b.apk'
            old.write_bytes(b'baseline')
            new.write_bytes(b'patched')
            (root / 'build-status.txt').write_text('APK_BUILDS_PASS_NO_NEW_UNIT_REGRESSIONS\n')
            (root / 'apks' / 'SHA256SUMS.txt').write_text(
                hashlib.sha256(old.read_bytes()).hexdigest() + '  baseline/a.apk\n' +
                hashlib.sha256(new.read_bytes()).hexdigest() + '  spike001/b.apk\n'
            )
            found, build = e.find_apks(work)
            self.assertEqual(build, root)
            self.assertEqual(found['baseline'], old)
            self.assertEqual(found['spike001'], new)
            new.write_bytes(b'corrupted')
            with self.assertRaises(e.EmulatorError):
                e.find_apks(work)

    def test_manifest_path_traversal_is_rejected(self):
        self.assertIsNone(e.APK_RE.fullmatch('deadbeef' * 8 + '  ../foreign.apk'))
        self.assertIsNone(e.APK_RE.fullmatch('deadbeef' * 8 + '  baseline/../../evil.apk'))

    def test_install_refuses_if_our_named_emulator_disappears(self):
        with patch.object(e, 'find_device', return_value='emulator-5556'):
            with self.assertRaises(e.EmulatorError):
                e.install_and_launch(Path('adb.exe'), 'emulator-5554', Path('x.apk'),
                                     'baseline', Path('/tmp'), Path('/tmp'))

    def test_patched_install_refuses_before_baseline(self):
        with patch.object(e, 'find_device', return_value='emulator-5554'):
            with patch.object(e, 'run', return_value=ok('')) as runner:
                with self.assertRaisesRegex(e.EmulatorError, 'Baseline ainda nao instalada'):
                    e.install_and_launch(Path('adb.exe'), 'emulator-5554', Path('x.apk'),
                                         'spike001', Path('/tmp'), Path('/tmp'))
                self.assertFalse(any('install' in call.args[0] for call in runner.call_args_list))

    def test_launch_evidence_is_not_a_runtime_pass(self):
        with tempfile.TemporaryDirectory() as root:
            apk = Path(root) / 'test.apk'
            apk.write_bytes(b'apk')
            def fake(args, **kwargs):
                if 'monkey' in args:
                    return ok('Events injected: 1\n')
                return ok('package:/data/app/test/base.apk\n')
            with patch.object(e, 'find_device', return_value='emulator-5554'):
                with patch.object(e, 'run', side_effect=fake):
                    evidence = e.install_and_launch(Path('adb.exe'), 'emulator-5554', apk,
                                                    'baseline', Path(root), Path(root))
            payload = json.loads((evidence / 'result.json').read_text())
            self.assertEqual(payload['verdict'], 'INSTALLED_AND_LAUNCH_REQUESTED_NOT_VISUALLY_VERIFIED')
            self.assertNotIn('PASS', payload['verdict'])

    def test_never_issues_wipe_or_uninstall(self):
        code = SRC.read_text()
        self.assertNotIn('wipe-data', code)
        self.assertNotIn('uninstall', code)
        self.assertIn('find_device(adb)', code)
        self.assertIn('"-s", serial, "install"', code)


if __name__ == '__main__':
    unittest.main()
