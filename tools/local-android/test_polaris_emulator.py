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


def ok(out=''):
    return subprocess.CompletedProcess([], 0, out, '')


def make_build(root, *, multi=False):
    target = root / 'PolarisLocal' / 'evidence' / 'issue002-20261023-190348'
    report = []
    for stage in ('baseline', 'spike001'):
        folder = target / 'apks' / stage
        folder.mkdir(parents=True)
        if multi:
            names = ['app-arm64-v8a-debug.apk', 'app-armeabi-v7a-debug.apk',
                     'app-x86-debug.apk', 'app-x86_64-debug.apk', 'app-universal-debug.apk']
        else:
            names = ['app-debug.apk']
        for name in names:
            apk = folder / name
            apk.write_bytes(f'{stage}-{name}'.encode())
            report.append(f'{hashlib.sha256(apk.read_bytes()).hexdigest()}  {stage}/{name}')
    (target / 'apks' / 'SHA256SUMS.txt').write_text('\n'.join(report) + '\n')
    (target / 'build-status.txt').write_text('APK_BUILDS_PASS_NO_NEW_UNIT_REGRESSIONS\n')
    return target


class EmulatorSafety(unittest.TestCase):
    def test_fhd_framebuffer_is_selected_at_startup_only_for_polaris(self):
        for stage in ('baseline', 'spike001'):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                avd = e.AVDS[stage]
                folder = root / 'emulador' / 'avd' / f'{avd}.avd'
                folder.mkdir(parents=True)
                with patch.object(e, 'ensure_avd', return_value=(avd, folder)), \
                        patch.object(e, 'executable', side_effect=lambda sdk, name: Path(name)), \
                        patch.object(e, 'find_device', return_value=None), \
                        patch.object(e.subprocess, 'Popen') as launch:
                    e.start_avd(root, root, stage)
                arguments = launch.call_args.args[0]
                if stage == 'spike001':
                    self.assertEqual(arguments[-2:], ['-skin', '1080x1920'])
                else:
                    self.assertNotIn('-skin', arguments)
                self.assertNotIn('-dpi-device', arguments)

    def test_existing_emulator_is_reused_without_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            avd = e.AVDS['spike001']
            with patch.object(e, 'ensure_avd', return_value=(avd, root)), \
                    patch.object(e, 'executable', side_effect=lambda sdk, name: Path(name)), \
                    patch.object(e, 'find_device', return_value='emulator-5554'), \
                    patch.object(e.subprocess, 'Popen') as launch:
                self.assertEqual(e.start_avd(root, root, 'spike001'), (avd, 'emulator-5554'))
                launch.assert_not_called()

    def test_auto_display_rejects_phone_and_unowned_targets_without_adb_writes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(e, 'run') as run:
            for serial in ('phone123', 'emulator-5554'):
                with self.assertRaises(e.EmulatorError):
                    e.prepare_reader_display(Path('adb'), serial, e.AVDS['spike001'], 'spike001', Path(tmp))
            run.assert_not_called()

    def test_auto_display_updates_only_owned_polaris_and_preserves_first_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            avd = e.AVDS['spike001']
            (root / 'emulador' / 'avd' / f'{avd}.avd').mkdir(parents=True)
            (root / 'emulador' / f'{avd}.owner.txt').write_text(avd + '\n')
            def response(args, **kwargs):
                if args[-2:] == ['wm', 'size']:
                    return ok('Physical size: 720x1280\n')
                if args[-2:] == ['wm', 'density']:
                    return ok('Physical density: 320\nOverride density: 360\n')
                return ok()
            with patch.object(e, 'find_device', return_value='emulator-5554'), \
                    patch.object(e, 'run', side_effect=response) as run:
                e.prepare_reader_display(Path('adb'), 'emulator-5554', avd, 'spike001', root)
                first = (root / 'emulador' / 'translation-display-backup.json').read_text()
                e.prepare_reader_display(Path('adb'), 'emulator-5554', avd, 'spike001', root)
                self.assertEqual((root / 'emulador' / 'translation-display-backup.json').read_text(), first)
                self.assertEqual(json.loads(first), {'size': 'reset', 'density': '360'})
                self.assertTrue(all(call.args[0][1:3] == ['-s', 'emulator-5554'] for call in run.call_args_list))
                self.assertIn(['wm', 'size', '1080x1920'], [call.args[0][-3:] for call in run.call_args_list])
                self.assertIn(['wm', 'density', '420'], [call.args[0][-3:] for call in run.call_args_list])
                run.reset_mock()
                e.prepare_reader_display(Path('adb'), 'phone123', e.AVDS['baseline'], 'baseline', root)
                run.assert_not_called()

    def test_no_consent(self):
        self.assertEqual(e.main(['duo', '--workspace', '/tmp']), 3)

    def test_untrusted_phone_never_selected(self):
        with patch.object(e, 'run', return_value=ok('List of devices attached\nABC123 device\n')):
            self.assertIsNone(e.find_device(Path('adb'), e.AVDS['baseline']))

    def test_identity_requires_exact_avd_name(self):
        def response(args, **kwargs):
            if args[-1] == 'devices':
                return ok('List of devices attached\nphone123 device\nemulator-5554 device\nemulator-5556 device\n')
            if 'emulator-5554' in args:
                return ok(e.AVDS['baseline'] + '\nOK\n')
            return ok(e.AVDS['spike001'] + '\nOK\n')
        with patch.object(e, 'run', side_effect=response):
            self.assertEqual(e.find_device(Path('adb'), e.AVDS['baseline']), 'emulator-5554')
            self.assertEqual(e.find_device(Path('adb'), e.AVDS['spike001']), 'emulator-5556')

    def test_multipart_apks_select_x86_64_and_verify_all_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = make_build(root, multi=True)
            selected, got = e.find_apks(root)
            self.assertEqual(got, target)
            for stage in ('baseline', 'spike001'):
                self.assertEqual(selected[stage].name, 'app-x86_64-debug.apk')
            other = target / 'apks' / 'baseline' / 'app-arm64-v8a-debug.apk'
            other.write_bytes(b'bad')
            with self.assertRaisesRegex(e.EmulatorError, 'Hash SHA-256'):
                e.find_apks(root)

    def test_single_universal_build_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_build(root)
            selected, _ = e.find_apks(root)
            self.assertEqual(selected['baseline'].name, 'app-debug.apk')

    def test_apk_selector_ambiguous_fails(self):
        with self.assertRaises(e.EmulatorError):
            e.select_x86_64_apk([Path('app-arm64-v8a.apk'), Path('app-x86.apk')], 'baseline')

    def test_manifest_traversal_rejected(self):
        self.assertIsNone(e.APK_RE.fullmatch('f' * 64 + '  ../evil.apk'))
        self.assertIsNone(e.APK_RE.fullmatch('f' * 64 + '  baseline/../../evil.apk'))

    def test_evidence_folder_missing_fails_without_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(e, 'sdk_location', side_effect=AssertionError('called')):
                self.assertEqual(e.main(['duo', '--workspace', tmp, '--consent']), 2)

    def test_two_independent_named_avds(self):
        self.assertNotEqual(e.AVDS['baseline'], e.AVDS['spike001'])
        self.assertIn('Yomotsu', e.AVDS['baseline'])
        self.assertIn('Spike001', e.AVDS['spike001'])

    def test_reject_preexisting_unowned_avd(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(e, 'executable', side_effect=lambda sdk, name: Path(name)):
                with patch.object(e, 'run', return_value=ok(e.AVDS['baseline'] + '\n')):
                    with self.assertRaisesRegex(e.EmulatorError, 'propriedade'):
                        e.ensure_avd(Path(tmp), Path(tmp), 'baseline')

    def test_preserves_avd_folders_and_uses_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            stage = 'baseline'
            avd = e.AVDS[stage]
            folder = work / 'emulador' / 'avd' / f'{avd}.avd'
            folder.mkdir(parents=True)
            (folder/'userdata-qemu.img').write_bytes(b'existing settings')
            (work/'emulador'/f'{avd}.owner.txt').write_text(avd + '\n')
            with patch.object(e, 'executable', side_effect=lambda sdk, name: Path(name)):
                with patch.object(e, 'run', return_value=ok(avd + '\n')):
                    got, p = e.ensure_avd(work, work, stage)
            self.assertEqual((got, p), (avd, folder))
            self.assertEqual((folder/'userdata-qemu.img').read_bytes(), b'existing settings')

    def test_install_refuses_physical_target(self):
        with patch.object(e, 'find_device', return_value=None):
            with self.assertRaises(e.EmulatorError):
                e.install_and_launch(Path('adb'), 'phone100', e.AVDS['baseline'],
                                     Path('test.apk'), 'baseline', Path('/tmp'), Path('/tmp'))

    def test_install_refuses_mismatched_stage(self):
        with patch.object(e, 'find_device', return_value='emulator-5554'):
            with self.assertRaises(e.EmulatorError):
                e.install_and_launch(Path('adb'), 'emulator-5554', e.AVDS['spike001'],
                                     Path('test.apk'), 'baseline', Path('/tmp'), Path('/tmp'))

    def test_launch_is_not_visual_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            apk = workspace/'apk.apk'
            apk.write_bytes(b'apk')
            def mock_run(args, **kwargs):
                if 'monkey' in args:
                    return ok('Events injected: 1\n')
                return ok('package:/data/app/base.apk\n')
            with patch.object(e, 'find_device', return_value='emulator-5554'):
                with patch.object(e, 'run', side_effect=mock_run):
                    report = e.install_and_launch(Path('adb'), 'emulator-5554',e.AVDS['baseline'],
                                                  apk, 'baseline', workspace, workspace)
            result = json.loads((report/'result.json').read_text())
            self.assertEqual(result['verdict'], 'INSTALLED_AND_LAUNCH_REQUESTED_NOT_VISUALLY_VERIFIED')
            self.assertEqual(result['stage'], 'baseline')
            self.assertNotIn('PASS', result['verdict'])

    def test_duo_launches_both_and_retains_comparison_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            make_build(work)
            reports = []
            prepared = []
            def write_report(_adb, _serial, avd, _apk, stage, _work, _build):
                self.assertIn(stage, prepared)
                report = work / 'relatorios' / stage
                report.mkdir(parents=True)
                reports.append((stage, avd))
                return report
            with patch.object(e, 'sdk_location', return_value=Path(tmp)):
                with patch.object(e, 'ensure_sdk_image'):
                    with patch.object(e, 'start_avd', side_effect=lambda w,s,stage:(e.AVDS[stage],None)) as start:
                        with patch.object(e, 'executable', side_effect=lambda sdk, name: Path(name)):
                            with patch.object(e, 'wait_for_boot', return_value='emulator-5554'):
                                with patch.object(e, 'install_and_launch', side_effect=write_report), \
                                        patch.object(e, 'prepare_reader_display',
                                                     side_effect=lambda adb, serial, avd, stage, workspace: prepared.append(stage)):
                                    self.assertEqual(e.main(['duo', '--workspace', tmp, '--consent']), 0)
            self.assertEqual(start.call_count, 2)
            self.assertEqual([t[0] for t in reports], ['baseline','spike001'])
            comp = work / 'relatorios' / 'spike001' / 'comparacao-fontes.json'
            data = json.loads(comp.read_text())
            self.assertTrue(all(x['result'] is None for x in data['test_items']))

    def test_no_destructive_avd_flags(self):
        src = SRC.read_text()
        self.assertNotIn("'-wipe-data'", src)
        self.assertNotIn("'uninstall'", src)
        self.assertNotIn("'-read-only'", src)
        self.assertIn("'install', '-r', '-t'", src)
        self.assertIn('userdata', src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
