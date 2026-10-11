"""Fail-closed self-tests for the offline Polaris validation aggregator."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from run_host_gate import evaluate_gate, extract_count, run_all


class HostGateParserTests(unittest.TestCase):
    def test_python_success(self):
        x = evaluate_gate("python", "Ran 72 tests in 0.3s\n\nOK\n", 0, 72)
        self.assertEqual((x["status"], x["cases"]), ("PASS", 72))

    def test_python_regressions(self):
        self.assertEqual(evaluate_gate("python", "Ran 72 tests in 0.3s\nFAILED", 1, 72)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("python", "Ran 72 tests in 0.3s\nFAILED", 0, 72)["status"], "MISSING_UNITTEST_OK_MARKER")

    def test_missing_summary_does_not_look_like_empty_green_suite(self):
        self.assertIsNone(extract_count("python", "Ran no tests"))
        self.assertEqual(evaluate_gate("python", "OK", 0, 72)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_too_few_test_cases_fails_closed(self):
        self.assertEqual(evaluate_gate("python", "Ran 44 tests in 0.1s\nOK\n", 0, 72)["status"], "INSUFFICIENT_TEST_COVERAGE")

    def test_kotlin_marker_must_match_exactly(self):
        good = "PASS scenario\nSPIKE001_HOST_INVARIANTS_PASS (34 scenarios); NOT_ANDROID_RUNTIME\n"
        self.assertEqual(evaluate_gate("kotlin", good, 0, 34)["status"], "PASS")
        self.assertEqual(evaluate_gate("kotlin", good, 1, 34)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("kotlin", good.replace("34", "30"), 0, 34)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("kotlin", "SPIKE001_HOST_INVARIANTS_PASS (34 scenarios)\n", 0, 34)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_duplicate_test_marker_is_not_accepted(self):
        message = "Ran 72 tests in 0.1s\nRan 72 tests in 0.1s\nOK\n"
        self.assertEqual(evaluate_gate("python", message, 0, 72)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_missing_checkout_does_not_emit_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty"
            root.mkdir()
            evidence = Path(tmp) / "evidence"
            with patch("run_host_gate.GATES", (("kotlin", ("does-not-exist-command",), 34),)):
                result = run_all(root, evidence)
            self.assertEqual(result, 1)
            report = json.loads((evidence / "host-gate-report.json").read_text())
            self.assertEqual(report["status"], "FAIL_OR_INCONCLUSIVE")
            self.assertEqual(report["scope"], "HOST_ONLY_NOT_ANDROID_RUNTIME")
            self.assertIsNone(report["gates"][0]["cases"])
            self.assertEqual(report["gates"][0]["exit_code"], 127)


if __name__ == "__main__":
    unittest.main()
