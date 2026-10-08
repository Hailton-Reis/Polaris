#!/usr/bin/env python3
"""Offline regression checks for issue #2 JUnit XML comparison."""
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
import json
from xml.sax.saxutils import escape

from compare_android_unit_tests import ReportError, collect, compare


def fixture(root, cases):
    path = root / "app/build/test-results/testDebugUnitTest/TEST-Reader.xml"
    path.parent.mkdir(parents=True, exist_ok=True)
    tests = []
    for name, state in cases.items():
        marker = "<failure message='expected'/>" if state == "failed" else "<skipped/>" if state == "skipped" else ""
        tests.append(f'<testcase classname="Reader" name="{escape(name)}">{marker}</testcase>')
    path.write_text("<testsuite>" + "".join(tests) + "</testsuite>")


class JunitComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.baseline = Path(self.tmp.name) / "baseline"
        self.patched = Path(self.tmp.name) / "patched"

    def compare_fixture(self, base, modified):
        fixture(self.baseline, base)
        fixture(self.patched, modified)
        return compare(collect(self.baseline), collect(self.patched))

    def test_identical_upstream_failures_are_not_regressions(self):
        result = self.compare_fixture({"works": "passed", "known-fail": "failed"},
                                      {"works": "passed", "known-fail": "failed"})
        self.assertEqual(result["status"], "NO_NEW_UNIT_REGRESSIONS")
        self.assertEqual(result["preexisting_failures_still_present"], 1)
        self.assertFalse(result["android_runtime_verified"])

    def test_new_test_failure_is_regression(self):
        result = self.compare_fixture({"works": "passed"}, {"works": "passed", "added": "failed"})
        self.assertEqual(result["status"], "REGRESSION_DETECTED")
        self.assertEqual(len(result["new_failures_or_skips"]), 1)

    def test_previously_passing_test_now_fails(self):
        result = self.compare_fixture({"works": "passed"}, {"works": "failed"})
        self.assertEqual(result["status"], "REGRESSION_DETECTED")

    def test_new_skip_does_not_mask_failure(self):
        result = self.compare_fixture({"works": "passed", "known": "failed"},
                                      {"works": "skipped", "known": "skipped"})
        self.assertEqual(result["status"], "REGRESSION_DETECTED")
        self.assertEqual(len(result["new_failures_or_skips"]), 2)

    def test_removed_baseline_test_is_regression(self):
        result = self.compare_fixture({"works": "passed", "disappeared": "failed"},
                                      {"works": "passed"})
        self.assertEqual(result["status"], "REGRESSION_DETECTED")
        self.assertEqual(len(result["missing_baseline_tests"]), 1)

    def test_fixed_upstream_failure_is_allowed(self):
        result = self.compare_fixture({"known": "failed"}, {"known": "passed"})
        self.assertEqual(result["status"], "NO_NEW_UNIT_REGRESSIONS")

    def test_missing_reports_cannot_be_called_pass(self):
        self.baseline.mkdir()
        with self.assertRaises(ReportError):
            collect(self.baseline)

    def test_cli_preserves_preexisting_failure_disclaimer(self):
        fixture(self.baseline, {"working": "passed", "known": "failed"})
        fixture(self.patched, {"working": "passed", "known": "failed"})
        evidence = Path(self.tmp.name) / "comparison.json"
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("compare_android_unit_tests.py")),
                                 str(self.baseline), str(self.patched),
                                 "--baseline-exit", "1", "--patched-exit", "1", "--output", str(evidence)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not all-tests-green", result.stdout)
        self.assertEqual(json.loads(evidence.read_text())["preexisting_failures_still_present"], 1)

    def test_cli_rejects_gradle_nonzero_without_failed_tests(self):
        fixture(self.baseline, {"working": "passed"})
        fixture(self.patched, {"working": "passed"})
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("compare_android_unit_tests.py")),
                                 str(self.baseline), str(self.patched), "--patched-exit", "1"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("INCONCLUSIVE", result.stderr)

    def test_malformed_xml_cannot_be_called_pass(self):
        fixture(self.baseline, {"works": "passed"})
        path = next(self.baseline.rglob("TEST-*.xml"))
        path.write_text("<testsuite><testcase>")
        with self.assertRaises(ReportError):
            collect(self.baseline)


if __name__ == "__main__":
    unittest.main()
