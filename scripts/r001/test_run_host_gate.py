"""Fail-closed self-tests for the offline Polaris validation aggregator."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from run_host_gate import GATES, evaluate_gate, extract_count, run_all


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
        good = "PASS scenario\nSPIKE001_HOST_INVARIANTS_PASS (38 scenarios); NOT_ANDROID_RUNTIME\n"
        self.assertEqual(evaluate_gate("kotlin", good, 0, 38)["status"], "PASS")
        self.assertEqual(evaluate_gate("kotlin", good, 1, 38)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("kotlin", good.replace("38", "34"), 0, 38)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("kotlin", "SPIKE001_HOST_INVARIANTS_PASS (38 scenarios)\n", 0, 38)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_duplicate_test_marker_is_not_accepted(self):
        message = "Ran 72 tests in 0.1s\nRan 72 tests in 0.1s\nOK\n"
        self.assertEqual(evaluate_gate("python", message, 0, 72)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")


    def test_backup_kotlin_marker_requires_both_stages_and_clean_exit(self):
        restore = "MERGED_BACKUP_RESTORE_PLANNER_PASS 24\n"
        export = "MERGED_BACKUP_EXPORT_PLANNER_PASS 20\n"
        both = restore + export
        self.assertEqual(evaluate_gate("backup-kotlin", both, 0, 44)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-kotlin", both, 1, 44)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-kotlin", both.replace("PASS 20", "PASS 19"), 0, 44)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-kotlin", restore, 0, 44)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", export, 0, 44)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", both + export, 0, 44)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", both + restore, 0, 44)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_backup_kotlin_rejects_false_marker_and_missing_report(self):
        good = "MERGED_BACKUP_RESTORE_PLANNER_PASS 24\nMERGED_BACKUP_EXPORT_PLANNER_PASS 20\n"
        self.assertIsNone(extract_count("backup-kotlin", good.replace("EXPORT_PLANNER", "EXPORT_PLAN")))
        self.assertIsNone(extract_count("backup-kotlin", good.replace("PASS 24", "PASS 24 (host)")))
        self.assertIsNone(extract_count("backup-kotlin", ""))

    def test_backup_sqlite_requires_unittest_summary_and_ok(self):
        output = "Ran 17 tests in 0.1s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-sqlite", output, 0, 17)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-sqlite", output.replace("OK", "FAILED"), 0, 17)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertEqual(evaluate_gate("backup-sqlite", output, 1, 17)["status"], "NONZERO_EXIT")

    def test_backup_suites_are_mandatory_host_gates(self):
        gates = {name: (command, required) for name, command, required in GATES}
        self.assertEqual(gates["backup-sqlite"][1], 17)
        self.assertEqual(gates["backup-kotlin"][1], 44)
        self.assertIn("spikes/spike001/backup", " ".join(gates["backup-sqlite"][0]))
        self.assertIn("spikes/spike001/backup/run_tests.sh", gates["backup-kotlin"][0])

    def test_missing_checkout_does_not_emit_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty"
            root.mkdir()
            evidence = Path(tmp) / "evidence"
            with patch("run_host_gate.GATES", (("kotlin", ("does-not-exist-command",), 38),)):
                result = run_all(root, evidence)
            self.assertEqual(result, 1)
            report = json.loads((evidence / "host-gate-report.json").read_text())
            self.assertEqual(report["status"], "FAIL_OR_INCONCLUSIVE")
            self.assertEqual(report["scope"], "HOST_ONLY_NOT_ANDROID_RUNTIME")
            self.assertIsNone(report["gates"][0]["cases"])
            self.assertEqual(report["gates"][0]["exit_code"], 127)


if __name__ == "__main__":
    unittest.main()
