"""Offline tests for the exact pinned Yomotsu virtual refresh patch checker."""
from pathlib import Path
import tempfile
import unittest

from check_spike001_refresh_patch import PatchContractError, check_patch, vm_operations


class VirtualRefreshPatchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = Path(__file__).resolve().parents[2] / "spikes/spike001/apply_spike001.py"
        cls.operations = vm_operations(cls.script)
        # The fixture is the exact set of pinned-version patch anchors, in order.
        # The full pinned Yomotsu source is also checked by the real build script.
        cls.baseline = "\n".join(old for old, _ in cls.operations)
        cls.patched = cls.baseline
        for old, new in cls.operations:
            cls.patched = cls.patched.replace(old, new, 1)

    def test_vm_patch_operations_are_literal_and_complete(self):
        self.assertEqual(len(self.operations), 4)

    def test_baseline_matches_all_four_anchors(self):
        check_patch(self.baseline, self.operations, "baseline")

    def test_patched_has_required_virtual_child_refresh(self):
        check_patch(self.patched, self.operations, "patched")

    def test_baseline_missing_anchor_fails_closed(self):
        text = self.baseline.replace(self.operations[0][0], "", 1)
        with self.assertRaises(PatchContractError):
            check_patch(text, self.operations, "baseline")

    def test_patched_missing_source_specific_refresh_fails_closed(self):
        changed = self.patched.replace("manga = child,", "manga = state.manga,", 1)
        with self.assertRaises(PatchContractError):
            check_patch(changed, self.operations, "patched")

    def test_patched_coordinator_import_is_required(self):
        mutated = self.patched.replace(
            "import tachiyomi.domain.manga.refresh.MergedRefreshCoordinator",
            "import tachiyomi.domain.manga.refresh.MissingCoordinator",
            1,
        )
        with self.assertRaises(PatchContractError):
            check_patch(mutated, self.operations, "patched")

    def test_patched_coordinator_call_cannot_be_omitted(self):
        mutated = self.patched.replace("MergedRefreshCoordinator.refresh(", "fakeRefresh(", 1)
        with self.assertRaises(PatchContractError):
            check_patch(mutated, self.operations, "patched")

    def test_patched_retains_existing_nonvirtual_refresh(self):
        mutated = self.patched.replace("source = state.source,", "source = state.manga,", 1)
        with self.assertRaises(PatchContractError):
            check_patch(mutated, self.operations, "patched")

    def test_patched_double_insertion_is_rejected(self):
        changed = self.patched + self.operations[-1][1]
        with self.assertRaises(PatchContractError):
            check_patch(changed, self.operations, "patched")

    def test_wrong_number_of_vm_patch_operations_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "apply.py"
            p.write_text("def apply(vm):\n    replace_once(vm, 'x', 'y')\n")
            with self.assertRaises(PatchContractError):
                vm_operations(p)


if __name__ == "__main__":
    unittest.main()
