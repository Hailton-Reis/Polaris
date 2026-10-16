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
        uuid = "POLARIS_PERSISTED_MERGE_UUID_PASS 21\n"
        both = restore + export + uuid
        self.assertEqual(evaluate_gate("backup-kotlin", both, 0, 65)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-kotlin", both, 1, 65)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-kotlin", both.replace("PASS 20", "PASS 19"), 0, 65)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-kotlin", restore, 0, 65)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", export, 0, 65)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", uuid, 0, 65)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", both + export, 0, 65)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", both + uuid, 0, 65)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-kotlin", both + restore, 0, 65)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_backup_kotlin_rejects_false_marker_and_missing_report(self):
        good = "MERGED_BACKUP_RESTORE_PLANNER_PASS 24\nMERGED_BACKUP_EXPORT_PLANNER_PASS 20\nPOLARIS_PERSISTED_MERGE_UUID_PASS 21\n"
        self.assertIsNone(extract_count("backup-kotlin", good.replace("EXPORT_PLANNER", "EXPORT_PLAN")))
        self.assertIsNone(extract_count("backup-kotlin", good.replace("PASS 24", "PASS 24 (host)")))
        self.assertIsNone(extract_count("backup-kotlin", ""))

    def test_uuid_backup_gate_requires_third_unique_marker(self):
        good = "MERGED_BACKUP_RESTORE_PLANNER_PASS 24\nMERGED_BACKUP_EXPORT_PLANNER_PASS 20\nPOLARIS_PERSISTED_MERGE_UUID_PASS 21\n"
        self.assertEqual(evaluate_gate("backup-kotlin", good, 0, 65)["status"], "PASS")
        self.assertIsNone(extract_count("backup-kotlin", good.replace("POLARIS_PERSISTED_MERGE_UUID_PASS 21\n", "")))
        self.assertIsNone(extract_count("backup-kotlin", good + "POLARIS_PERSISTED_MERGE_UUID_PASS 21\n"))

    def test_yomotsu_backup_adapter_requires_exact_success_marker(self):
        complete = "EXPORT_ADAPTER_PASS 12: scenario\nPOLARIS_YOMOTSU_EXPORT_ADAPTER_PASS 12\n"
        self.assertEqual(evaluate_gate("backup-adapter", complete, 0, 12)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-adapter", complete, 1, 12)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-adapter", complete.replace("PASS 12\n", "PASS 11\n"), 0, 12)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-adapter", complete + "POLARIS_YOMOTSU_EXPORT_ADAPTER_PASS 12\n", 0, 12)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-adapter", "EXPORT_ADAPTER_PASS 12\n", 0, 12)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_sqldelight_port_kotlin_requires_unique_19_case_marker(self):
        good = "SQLDELIGHT_PORT_PASS 19 done\nPOLARIS_SQLDELIGHT_PORT_PASS 19\n"
        self.assertEqual(evaluate_gate("backup-sqldelight-port", good, 0, 19)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", good, 1, 19)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", good.replace("PASS 19\n", "PASS 18\n"), 0, 19)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", good + "POLARIS_SQLDELIGHT_PORT_PASS 19\n", 0, 19)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertIsNone(extract_count("backup-sqldelight-port", "only PASS tests"))

    def test_reviewed_migration_rehearsal_requires_eighty_five_clean_cases(self):
        good = "Ran 85 tests in 0.09s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-migration-audit", good, 0, 85)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-migration-audit", good, 1, 85)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-migration-audit", good.replace("85 tests", "84 tests"), 0, 85)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-migration-audit", good.replace("OK", "FAILED"), 0, 85)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertTrue(any("migration-audit" in item for n, cmd, m in GATES if n == "backup-migration-audit" for item in cmd))

    def test_sqldelight_sqlite_gate_requires_all_10_tests(self):
        good = "Ran 10 tests in 0.03s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good, 0, 10)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good, 1, 10)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good.replace("10 tests", "9 tests"), 0, 10)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good.replace("OK", "FAILED"), 0, 10)["status"], "MISSING_UNITTEST_OK_MARKER")

    def test_atomic_sqlite_restore_requires_all_31_checks(self):
        good = "Ran 31 tests in 0.02s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-atomic-sqlite", good, 0, 31)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-atomic-sqlite", good, 1, 31)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-atomic-sqlite", good.replace("31 tests", "29 tests"), 0, 31)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-atomic-sqlite", good.replace("OK", "FAILED"), 0, 31)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertTrue(any("atomic-sqlite" in item for item in next(c for n,c,m in GATES if n == "backup-atomic-sqlite")))

    def test_child_first_restore_requires_exact_marker_and_success(self):
        ok = "RESTORE_COORDINATOR_PASS 20 final\nPOLARIS_YOMOTSU_RESTORE_COORDINATOR_PASS 20\n"
        self.assertEqual(evaluate_gate("backup-restore", ok, 0, 20)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-restore", ok, 1, 20)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-restore", ok.replace("COORDINATOR_PASS 20\n", "COORDINATOR_PASS 19\n"), 0, 20)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-restore", ok + "POLARIS_YOMOTSU_RESTORE_COORDINATOR_PASS 20\n", 0, 20)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-restore", "RESTORE_COORDINATOR_PASS 20 final\n", 0, 20)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")

    def test_backup_sqlite_requires_unittest_summary_and_ok(self):
        output = "Ran 17 tests in 0.1s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-sqlite", output, 0, 17)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-sqlite", output.replace("OK", "FAILED"), 0, 17)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertEqual(evaluate_gate("backup-sqlite", output, 1, 17)["status"], "NONZERO_EXIT")

    def test_backup_suites_are_mandatory_host_gates(self):
        gates = {name: (command, required) for name, command, required in GATES}
        self.assertEqual(gates["backup-sqlite"][1], 17)
        self.assertEqual(gates["backup-kotlin"][1], 65)
        self.assertEqual(gates["backup-adapter"][1], 12)
        self.assertEqual(gates["backup-restore"][1], 20)
        self.assertIn("yomotsu-candidate/run_tests.sh", gates["backup-adapter"][0][1])
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
