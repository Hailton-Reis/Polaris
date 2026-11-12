import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from compare_android_unit_tests import ReportError
from verify_android_build_completion import verify


class CombinedBuildCompletionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for module, total in (('domain', 58), ('app', 370)):
            report = self.root / module / 'build/test-results/testDebugUnitTest/TEST-cases.xml'
            report.parent.mkdir(parents=True)
            suite = ET.Element('testsuite')
            for index in range(total):
                case = ET.SubElement(suite, 'testcase', classname=module + '.Example', name=str(index))
                if module == 'app' and index < 34:
                    ET.SubElement(case, 'failure', message='preexisting upstream failure')
            ET.ElementTree(suite).write(report)
        self.output = self.root / 'app/build/outputs/apk/debug'
        self.output.mkdir(parents=True)
        self.metadata = self.output / 'output-metadata.json'
        self.metadata.write_text(json.dumps({'variantName': 'debug', 'elements': [
            {'outputFile': 'app-x86_64-debug.apk'}, {'outputFile': 'app-universal-debug.apk'},
        ]}))
        for name in ('app-x86_64-debug.apk', 'app-universal-debug.apk'):
            (self.output / name).write_bytes(b'test artifact; not an actual Android APK')
        self.log = self.root / 'gradle.log'
        self.log.write_text('> Task :app:testDebugUnitTest FAILED\n> Task :app:assembleDebug\nBUILD FAILED\n')

    def test_completed_assembly_accepts_only_classified_unit_failures(self):
        result = verify(self.root, self.log, 1)
        self.assertEqual('ASSEMBLY_AND_UNIT_REPORTS_COMPLETE', result['status'])
        self.assertEqual(428, result['unit_tests'])

    def test_compiler_or_packaging_failure_is_never_a_test_only_failure(self):
        with self.log.open('a') as log:
            log.write('> Task :app:packageDebug FAILED\n')
        with self.assertRaisesRegex(ReportError, 'non-unit-test'):
            verify(self.root, self.log, 1)

    def test_an_old_apk_cannot_substitute_for_an_uncompleted_assemble_task(self):
        self.log.write_text('> Task :app:testDebugUnitTest FAILED\n> Task :app:assembleDebug SKIPPED\nBUILD FAILED\n')
        with self.assertRaisesRegex(ReportError, 'did not complete'):
            verify(self.root, self.log, 1)

    def test_every_apk_declared_in_metadata_must_exist(self):
        (self.output / 'app-universal-debug.apk').unlink()
        with self.assertRaisesRegex(ReportError, 'Missing/empty APK'):
            verify(self.root, self.log, 1)

    def test_partial_test_reports_are_rejected_even_with_apks(self):
        report = self.root / 'app/build/test-results/testDebugUnitTest/TEST-cases.xml'
        tree = ET.parse(report)
        tree.getroot().remove(tree.getroot()[-1])
        tree.write(report)
        with self.assertRaisesRegex(ReportError, 'minimum 370'):
            verify(self.root, self.log, 1)

    def test_invalid_metadata_or_output_paths_are_rejected(self):
        for content in ('not json', json.dumps({'variantName': 'debug', 'elements': [{'outputFile': '../bad.apk'}]})):
            with self.subTest(content=content):
                self.metadata.write_text(content)
                with self.assertRaises(ReportError):
                    verify(self.root, self.log, 1)

    def test_daemon_crash_cannot_be_misclassified_by_stale_reports(self):
        self.log.write_text('Daemon disappeared unexpectedly\nBUILD FAILED\n')
        with self.assertRaisesRegex(ReportError, 'unidentified'):
            verify(self.root, self.log, 1)


if __name__ == '__main__':
    unittest.main()
