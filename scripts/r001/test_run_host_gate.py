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

    def test_parent_snapshot_split_requires_unique_23_case_marker(self):
        good = "POLARIS_PARENT_SPLIT_HOST_PASS 23\n"
        self.assertEqual(evaluate_gate("backup-parent-split", good, 0, 23)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-parent-split", good, 1, 23)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-parent-split", "", 0, 23)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-parent-split", good + good, 0, 23)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-parent-split", good.replace("23", "22"), 0, 23)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-parent-split", good.replace("23", "100"), 0, 23)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-parent-split", good + "ERROR", 1, 23)["status"], "NONZERO_EXIT")

    def test_unified_parent_kotlin_requires_unique_44_case_marker(self):
        good = "POLARIS_FULL_PARENT_UNIFIED_KOTLIN_PASS 44\n"
        gate = "backup-full-parent-unified-kotlin"
        self.assertEqual(evaluate_gate(gate, good, 0, 44)["status"], "PASS")
        self.assertEqual(evaluate_gate(gate, good, 1, 44)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate(gate, good.replace("44", "43"), 0, 44)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate(gate, good + good, 0, 44)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate(gate, "", 0, 44)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertTrue(any(n == gate and m == 44 for n, cmd, m in GATES))

    def test_spike001_layering_requires_49_sqlite_cases(self):
        gate = "backup-spike001-layering"
        good = "Ran 49 tests in 0.15s\n\nOK\n"
        self.assertEqual(evaluate_gate(gate, good, 0, 49)["status"], "PASS")
        self.assertEqual(evaluate_gate(gate, good, 1, 49)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate(gate, good.replace("49", "48"), 0, 49)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate(gate, good.replace("OK", "FAILED"), 0, 49)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertEqual(evaluate_gate(gate, "", 0, 49)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertTrue(any(n == gate and cases == 49 for n, cmd, cases in GATES))

    def test_pinned_schema_bridge_requires_49_sqlite_cases(self):
        gate = "backup-pinned-schema-bridge"
        good = "Ran 49 tests in 0.07s\n\nOK\n"
        self.assertEqual(evaluate_gate(gate, good, 0, 49)["status"], "PASS")
        self.assertEqual(evaluate_gate(gate, good, 1, 49)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate(gate, good.replace("49", "48"), 0, 49)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate(gate, good.replace("OK", "FAILED"), 0, 49)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertTrue(any(n == gate and minimum == 49 for n, command, minimum in GATES))

    def test_full_parent_sqlite_gate_requires_42_cases(self):
        gate = "backup-full-parent-sqlite"
        good = "Ran 42 tests in 0.04s\n\nOK\n"
        self.assertEqual(evaluate_gate(gate, good, 0, 42)["status"], "PASS")
        self.assertEqual(evaluate_gate(gate, good, 1, 42)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate(gate, good.replace("42", "41"), 0, 42)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate(gate, good + "Ran 42 tests in 0.05s\n", 0, 42)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate(gate, good.replace("OK", "FAILED"), 0, 42)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertTrue(any(n == gate and m == 42 for n, c, m in GATES))

    def test_parent_metadata_plan_requires_unique_28_case_marker(self):
        good = "POLARIS_PARENT_METADATA_RESTORE_PLAN_PASS 28\n"
        self.assertEqual(evaluate_gate("backup-parent-metadata-plan", good, 0, 28)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-parent-metadata-plan", good, 1, 28)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-parent-metadata-plan", "", 0, 28)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-parent-metadata-plan", good + good, 0, 28)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-parent-metadata-plan", good.replace("28", "27"), 0, 28)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertTrue(any(n == "backup-parent-metadata-plan" and m == 28 for n, c, m in GATES))


    def test_backup_portable_field_and_pending_model_require_all_five_suites(self):
        base = ("POLARIS_BACKUP_PROTO_MODEL_PASS 18\n"
                "POLARIS_BACKUP_BUNDLE_BUILDER_PASS 19\n"
                "POLARIS_PENDING_SNAPSHOT_MODEL_PASS 9\n"
                "POLARIS_BACKUP_FIELD_INTEROP_PASS 5\n"
                "POLARIS_PARENT_V2_HOST_PASS 26\n")
        self.assertEqual(evaluate_gate("backup-proto-contract", base, 0, 77)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-proto-contract", base, 1, 77)["status"], "NONZERO_EXIT")
        for item in base.splitlines(keepends=True):
            self.assertEqual(evaluate_gate("backup-proto-contract", base.replace(item, ""), 0, 77)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
            self.assertEqual(evaluate_gate("backup-proto-contract", base + item, 0, 77)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        for value, replacement in (("PASS 18", "PASS 17"), ("PASS 19", "PASS 18"),
                                   ("PASS 9", "PASS 8"), ("PASS 5", "PASS 4"), ("PASS 26", "PASS 25")):
            self.assertEqual(evaluate_gate("backup-proto-contract", base.replace(value, replacement), 0, 77)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-proto-contract",
                         base.replace("PASS 18", "PASS 100").replace("PASS 5", "PASS 4"),
                         0, 77)["status"], "INSUFFICIENT_TEST_COVERAGE")

    def test_sqldelight_port_kotlin_requires_real_models_and_both_suites(self):
        port = "POLARIS_SQLDELIGHT_PORT_PASS 25\n"
        real = "POLARIS_REAL_MODEL_END_TO_END_PASS 16\n"
        both = port + real
        self.assertEqual(evaluate_gate("backup-sqldelight-port", both, 0, 41)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", both, 1, 41)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", port, 0, 41)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", real, 0, 41)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", both + real, 0, 41)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", both + port, 0, 41)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", port.replace("25", "24") + real, 0, 41)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", port + real.replace("16", "15"), 0, 41)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-sqldelight-port", port.replace("25", "24") + real.replace("16", "100"), 0, 41)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertIsNone(extract_count("backup-sqldelight-port", "port-only test passes"))


    def test_yomotsu_gate_requires_three_independent_unique_stages(self):
        port = "POLARIS_YOMOTSU_SOURCE_RESTORE_PASS 23\n"
        sequence = "POLARIS_YOMOTSU_RESTORE_SEQUENCE_PASS 14\n"
        lifecycle = "POLARIS_BACKUP_RESTORER_LIFECYCLE_PASS 16\n"
        all_three = port + sequence + lifecycle
        self.assertEqual(evaluate_gate("backup-yomotsu-children", all_three, 0, 53)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-yomotsu-children", all_three, 1, 53)["status"], "NONZERO_EXIT")
        for omit in (port, sequence, lifecycle):
            self.assertEqual(evaluate_gate("backup-yomotsu-children", all_three.replace(omit, ""), 0, 53)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
            self.assertEqual(evaluate_gate("backup-yomotsu-children", all_three + omit, 0, 53)["status"], "MISSING_OR_INVALID_TEST_SUMMARY")
        for original, truncated in ((port, port.replace("23", "22")), (sequence, sequence.replace("14", "13")), (lifecycle, lifecycle.replace("16", "15"))):
            self.assertEqual(evaluate_gate("backup-yomotsu-children", all_three.replace(original, truncated), 0, 53)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-yomotsu-children", port.replace("23", "100") + sequence + lifecycle.replace("16", "15"), 0, 53)["status"], "INSUFFICIENT_TEST_COVERAGE")


    def test_reviewed_migration_rehearsal_requires_eighty_five_clean_cases(self):
        good = "Ran 85 tests in 0.09s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-migration-audit", good, 0, 85)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-migration-audit", good, 1, 85)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-migration-audit", good.replace("85 tests", "84 tests"), 0, 85)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-migration-audit", good.replace("OK", "FAILED"), 0, 85)["status"], "MISSING_UNITTEST_OK_MARKER")
        self.assertTrue(any("migration-audit" in item for n, cmd, m in GATES if n == "backup-migration-audit" for item in cmd))

    def test_sqldelight_sqlite_gate_requires_all_16_tests(self):
        good = "Ran 16 tests in 0.03s\n\nOK\n"
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good, 0, 16)["status"], "PASS")
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good, 1, 16)["status"], "NONZERO_EXIT")
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good.replace("16 tests", "15 tests"), 0, 16)["status"], "INSUFFICIENT_TEST_COVERAGE")
        self.assertEqual(evaluate_gate("backup-sqldelight-sqlite", good.replace("OK", "FAILED"), 0, 16)["status"], "MISSING_UNITTEST_OK_MARKER")

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
