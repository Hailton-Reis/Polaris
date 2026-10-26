"""Host-side tests for non-destructive pre-configuration Android smoke checks."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import polaris_smoke as smoke


def ok(out=''):
    return subprocess.CompletedProcess([], 0, out, '')


class NoConfigurationSmoke(unittest.TestCase):
    def adb_fake(self, args, **_kwargs):
        args=[str(x) for x in args]
        if 'getprop' in args:
            return ok('1\n' if 'sys.boot_completed' in args else '35\n')
        if 'pm' in args:
            return ok('package:/data/app/example/base.apk\n')
        if 'pidof' in args:
            return ok('2048\n')
        if 'window' in args:
            return ok('mCurrentFocus=Window{ad u0 app.mihon.tachiyomiat.dev/.MainActivity}\n')
        if 'activities' in args:
            return ok('topResumedActivity=ActivityRecord{app.mihon.tachiyomiat.dev/.MainActivity}\n')
        if 'logcat' in args:
            return ok('')
        raise AssertionError('Unexpected read-only ADB request: '+str(args))

    def test_no_consent_refuses_all_device_access(self):
        with patch.object(smoke.emulator, 'sdk_location', side_effect=AssertionError('accessed')):
            self.assertEqual(smoke.main(['--workspace','/tmp']), 3)

    def test_two_avds_same_package_but_independent_names(self):
        self.assertNotEqual(smoke.emulator.AVDS['baseline'], smoke.emulator.AVDS['spike001'])
        self.assertEqual(smoke.STAGES,('baseline','spike001'))

    def test_successful_headless_smoke_only_observes_no_sources(self):
        with tempfile.TemporaryDirectory() as work:
            with patch.object(smoke.emulator,'sdk_location',return_value=Path(work)):
                with patch.object(smoke.emulator,'executable',return_value=Path('adb')):
                    with patch.object(smoke.emulator,'find_device',side_effect=['emulator-5554','emulator-5556']):
                        with patch.object(smoke.emulator,'run',side_effect=self.adb_fake) as called:
                            status=smoke.main(['--workspace',work,'--consent','--no-screenshots'])
            self.assertEqual(status,0)
            report=next((Path(work)/'relatorios').glob('smoke-*/report.json'))
            info=json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(info['B01_B05'],'PENDING_MANUAL_SOURCE_SETUP')
            self.assertEqual(info['writes_to_android'],'NONE')
            self.assertEqual([d['verdict'] for d in info['devices']],
                             ['DIAGNOSTIC_OBSERVED_B01_B05_PENDING']*2)
            commands=[' '.join(map(str,c.args[0])) for c in called.call_args_list]
            prohibited=[' install ',' uninstall ',' input tap',' pm clear',' force-stop', ' -wipe-data',' logcat -c']
            for command in commands:
                for pattern in prohibited:
                    self.assertNotIn(pattern,command)
            self.assertTrue((report.parent/'report.html').is_file())

    def test_missing_avd_reports_failure_not_false_success(self):
        with tempfile.TemporaryDirectory() as work:
            with patch.object(smoke.emulator,'find_device',return_value=None):
                result=smoke.check_stage(Path('adb'),'baseline',Path(work),capture=False)
        self.assertEqual(result['verdict'],'DEVICE_NOT_FOUND')
        self.assertFalse(result['checks']['avd_connected'])

    def test_missing_app_process_does_not_pass(self):
        def stub(args,**kwargs):
            if 'pidof' in [str(x) for x in args]:
                return subprocess.CompletedProcess([],1,'','')
            return self.adb_fake(args,**kwargs)
        with tempfile.TemporaryDirectory() as work:
            with patch.object(smoke.emulator,'find_device',return_value='emulator-5554'):
                with patch.object(smoke.emulator,'run',side_effect=stub):
                    result=smoke.check_stage(Path('adb'),'baseline',Path(work),capture=False)
        self.assertEqual(result['verdict'],'DIAGNOSTIC_FAILED_B01_B05_PENDING')
        self.assertFalse(result['checks']['app_process_running'])

    def test_missing_foreground_does_not_pass(self):
        def stub(args,**kwargs):
            if 'dumpsys' in [str(x) for x in args]:
                return ok('mCurrentFocus=Window{other.app/.MainActivity}')
            return self.adb_fake(args,**kwargs)
        with tempfile.TemporaryDirectory() as work:
            with patch.object(smoke.emulator,'find_device',return_value='emulator-5554'):
                with patch.object(smoke.emulator,'run',side_effect=stub):
                    result=smoke.check_stage(Path('adb'),'baseline',Path(work),capture=False)
        self.assertFalse(result['checks']['app_in_foreground'])
        self.assertEqual(result['verdict'],'DIAGNOSTIC_FAILED_B01_B05_PENDING')

    def test_png_capture_binary_and_invalid_capture_rejected(self):
        png=smoke.PNG_SIGNATURE+b'fake pixels'*4
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'baseline.png'
            with patch.object(smoke.subprocess,'run',return_value=subprocess.CompletedProcess([],0,png,b'')):
                smoke.screenshot(Path('adb'),'emulator-5554',out)
            self.assertEqual(out.read_bytes(),png)
            with patch.object(smoke.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'not png',b'')):
                with self.assertRaises(smoke.SmokeError):
                    smoke.screenshot(Path('adb'),'emulator-5554',out)

    def test_screenshot_error_is_warning_and_preserves_observability(self):
        with tempfile.TemporaryDirectory() as work:
            with patch.object(smoke.emulator,'find_device',return_value='emulator-5554'):
                with patch.object(smoke.emulator,'run',side_effect=self.adb_fake):
                    with patch.object(smoke,'screenshot',side_effect=smoke.SmokeError('no PNG')):
                        result=smoke.check_stage(Path('adb'),'baseline',Path(work))
        self.assertEqual(result['verdict'],'DIAGNOSTIC_OBSERVED_B01_B05_PENDING')
        self.assertFalse(result['checks']['screenshot_captured'])
        self.assertIn('no PNG',result['warnings'])

    def test_crash_log_is_advisory_not_automatic_runtime_failure(self):
        def stub(args,**kwargs):
            if 'logcat' in [str(x) for x in args]:
                return ok('FATAL EXCEPTION: main\nProcess: app.mihon.tachiyomiat.dev')
            return self.adb_fake(args,**kwargs)
        with tempfile.TemporaryDirectory() as work:
            with patch.object(smoke.emulator,'find_device',return_value='emulator-5554'):
                with patch.object(smoke.emulator,'run',side_effect=stub):
                    result=smoke.check_stage(Path('adb'),'baseline',Path(work),capture=False)
        self.assertTrue(result['checks']['android_runtime_crash_seen_in_recent_logs'])
        self.assertTrue(result['warnings'])

    def test_foreground_matching_requires_actual_focus(self):
        pkg='app.mihon.tachiyomiat.dev'
        self.assertTrue(smoke.foreground_matches(pkg,'mCurrentFocus=Window{'+pkg+'/.Home}', ''))
        self.assertFalse(smoke.foreground_matches(pkg,'Window{'+pkg+'/.Home}', ''))
        self.assertFalse(smoke.foreground_matches(pkg,'mCurrentFocus=Window{foreign/.Home}', ''))

    def test_html_escapes_dynamic_log_content_no_remote_resources(self):
        payload={'devices':[{'stage':'<img onerror=alert(1)>','avd':'A&V','verdict':'PENDING',
                             'checks':{'ok':False},'warnings':['<script>bad</script>'],
                             'screenshot':None}]}
        rendered=smoke.report_html(payload)
        self.assertNotIn('<script>',rendered)
        self.assertIn('&lt;script&gt;',rendered)
        self.assertNotIn('http://',rendered)

    def test_code_does_not_tap_clear_or_install(self):
        source=Path(smoke.__file__).read_text(encoding='utf-8')
        for dangerous in ('pm clear','input tap',' -S ', 'logcat -c',' install -r','uninstall','wipe-data'):
            self.assertNotIn(dangerous,source)


if __name__=='__main__':
    unittest.main(verbosity=2)
