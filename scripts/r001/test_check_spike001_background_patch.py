"""Offline regression tests for the virtual-work automatic update exclusions."""
from pathlib import Path
import unittest

from check_spike001_background_patch import (
    BackgroundPatchContractError, check_job, job_operations,
)


class BackgroundPatchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Path(__file__).resolve().parents[2] / "spikes/spike001/apply_spike001.py"
        cls.operations = job_operations(app)
        cls.fixtures = {}
        for job, changes in cls.operations.items():
            baseline = "\n".join(old for old, _ in changes)
            patched = baseline
            for old, new in changes:
                patched = patched.replace(old, new, 1)
            cls.fixtures[job] = (baseline, patched)

    def test_exactly_two_literal_edits_per_job(self):
        self.assertEqual({key: len(val) for key, val in self.operations.items()}, {"lj": 2, "mj": 2})

    def test_original_library_worker_is_patchable(self):
        check_job(self.fixtures["lj"][0], self.operations["lj"], "baseline", "lj")

    def test_original_metadata_worker_is_patchable(self):
        check_job(self.fixtures["mj"][0], self.operations["mj"], "baseline", "mj")

    def test_patched_library_worker_is_safe(self):
        check_job(self.fixtures["lj"][1], self.operations["lj"], "patched", "lj")

    def test_patched_metadata_worker_is_safe(self):
        check_job(self.fixtures["mj"][1], self.operations["mj"], "patched", "mj")

    def test_missing_virtual_source_filter_is_rejected(self):
        patched = self.fixtures["lj"][1].replace("it.manga.source != MERGED_SOURCE_ID", "true", 1)
        with self.assertRaises(BackgroundPatchContractError):
            check_job(patched, self.operations["lj"], "patched", "lj")

    def test_repeated_library_filter_is_rejected(self):
        patched = self.fixtures["lj"][1] + "\n.filter { it.manga.source != MERGED_SOURCE_ID }"
        with self.assertRaises(BackgroundPatchContractError):
            check_job(patched, self.operations["lj"], "patched", "lj")

    def test_original_source_cannot_be_reported_as_patched(self):
        for name in ("lj", "mj"):
            with self.subTest(job=name), self.assertRaises(BackgroundPatchContractError):
                check_job(self.fixtures[name][0], self.operations[name], "patched", name)


if __name__ == "__main__":
    unittest.main()
