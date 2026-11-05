"""Offline tests of the Android-unit JUnit comparison gate."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.sax.saxutils import escape

from compare_android_unit_tests import ReportError, check_coverage, check_gradle, collect, compare


def fixture(root, cases, module="app"):
    report = root / module / "build/test-results/testDebugUnitTest/TEST-Reader.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    tests = []
    for name, state in cases.items():
        marker = "<failure message='expected'/>" if state == "failed" else "<skipped/>" if state == "skipped" else ""
        tests.append(f'<testcase classname="Reader" name="{escape(name)}">{marker}</testcase>')
    report.write_text("<testsuite>" + "".join(tests) + "</testsuite>")


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

    def cli(self, *args):
        return subprocess.run([sys.executable, str(Path(__file__).with_name("compare_android_unit_tests.py")),
                               str(self.baseline), str(self.patched), *args], capture_output=True, text=True)

    def test_identical_upstream_failures_are_not_regressions(self):
        result = self.compare_fixture({"works": "passed", "known": "failed"}, {"works": "passed", "known": "failed"})
        self.assertEqual(result["status"], "NO_NEW_UNIT_REGRESSIONS")
        self.assertEqual(result["preexisting_failures_still_present"], 1)
        self.assertFalse(result["android_runtime_verified"])

    def test_new_failure_rejected(self):
        self.assertEqual(self.compare_fixture({"works": "passed"}, {"works": "passed", "added": "failed"})["status"], "REGRESSION_DETECTED")

    def test_previously_passing_test_fails(self):
        self.assertEqual(self.compare_fixture({"works": "passed"}, {"works": "failed"})["status"], "REGRESSION_DETECTED")

    def test_new_skip_does_not_mask_failure(self):
        result = self.compare_fixture({"works": "passed", "known": "failed"}, {"works": "skipped", "known": "skipped"})
        self.assertEqual(len(result["new_failures_or_skips"]), 2)

    def test_missing_baseline_case_rejected(self):
        self.assertEqual(self.compare_fixture({"works": "passed", "old": "failed"}, {"works": "passed"})["status"], "REGRESSION_DETECTED")

    def test_fixed_upstream_failure_allowed(self):
        self.assertEqual(self.compare_fixture({"known": "failed"}, {"known": "passed"})["status"], "NO_NEW_UNIT_REGRESSIONS")

    def test_missing_reports_fail_closed(self):
        self.baseline.mkdir()
        with self.assertRaises(ReportError): collect(self.baseline)

    def test_invalid_xml_fail_closed(self):
        fixture(self.baseline, {"works": "passed"})
        next(self.baseline.rglob("TEST-*.xml")).write_text("<testsuite>")
        with self.assertRaises(ReportError): collect(self.baseline)

    def test_coverage_floor_detects_partial_baseline(self):
        fixture(self.baseline, {"one": "passed"})
        with self.assertRaises(ReportError): check_coverage(collect(self.baseline), {"app": 2}, "baseline")

    def test_coverage_floor_detects_missing_module(self):
        fixture(self.baseline, {"one": "passed"})
        with self.assertRaises(ReportError): check_coverage(collect(self.baseline), {"domain": 1}, "baseline")

    def test_gradle_success_requires_success_marker(self):
        fixture(self.baseline, {"one": "passed"})
        logfile = Path(self.tmp.name) / "log.txt"
        logfile.write_text("Build starting\n")
        with self.assertRaises(ReportError): check_gradle(logfile, 0, collect(self.baseline), "baseline")

    def test_gradle_infrastructure_failure_does_not_pass_with_known_test_failure(self):
        fixture(self.baseline, {"old_failure": "failed"})
        logfile = Path(self.tmp.name) / "log.txt"
        logfile.write_text("> Task :app:compileDebugKotlin FAILED\nBUILD FAILED\n")
        with self.assertRaises(ReportError): check_gradle(logfile, 1, collect(self.baseline), "baseline")

    def test_gradle_known_test_only_failure_allowed(self):
        fixture(self.baseline, {"old_failure": "failed"})
        logfile = Path(self.tmp.name) / "log.txt"
        logfile.write_text("> Task :app:testDebugUnitTest FAILED\nBUILD FAILED\n")
        check_gradle(logfile, 1, collect(self.baseline), "baseline")

    def test_gradle_unit_failure_without_report_rejected(self):
        fixture(self.baseline, {"old_failure": "passed"})
        logfile = Path(self.tmp.name) / "log.txt"
        logfile.write_text("> Task :app:testDebugUnitTest FAILED\nBUILD FAILED\n")
        with self.assertRaises(ReportError): check_gradle(logfile, 1, collect(self.baseline), "baseline")

    def test_cli_preexisting_failure_disclaimer_and_json(self):
        fixture(self.baseline, {"known": "failed"})
        fixture(self.patched, {"known": "failed"})
        a = Path(self.tmp.name) / "a.log"
        b = Path(self.tmp.name) / "b.log"
        a.write_text("> Task :app:testDebugUnitTest FAILED\nBUILD FAILED\n")
        b.write_text("> Task :app:testDebugUnitTest FAILED\nBUILD FAILED\n")
        outfile = Path(self.tmp.name) / "result.json"
        r = self.cli("--baseline-exit", "1", "--patched-exit", "1", "--baseline-log", str(a),
                     "--patched-log", str(b), "--min-module", "app=1", "--output", str(outfile))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("not all-tests-green", r.stdout)
        self.assertEqual(json.loads(outfile.read_text())["preexisting_failures_still_present"], 1)

    def test_cli_rejects_nonzero_exit_without_log(self):
        fixture(self.baseline, {"old": "failed"})
        fixture(self.patched, {"old": "failed"})
        result = self.cli("--patched-exit", "1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("INCONCLUSIVE", result.stderr)


if __name__ == "__main__": unittest.main()
