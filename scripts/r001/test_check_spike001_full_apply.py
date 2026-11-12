"""Regression tests for the *entire* Spike-001 applicator vs a synthetic pinned fixture.

The production check also runs on the real pinned Yomotsu checkout in CI.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from check_spike001_full_apply import (
    EXPECTED_NEW_FILES,
    EXPECTED_OPS,
    EXISTING,
    REPLACEMENT,
    STAGE,
    IntegrationContractError,
    operations,
    verify,
)


class FullApplicationContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / "upstream"
        self.out = self.root / "patched"
        self.stage = self.root / "stage"
        shutil.copytree(STAGE, self.stage)
        edits = operations(self.stage / "apply_spike001.py")
        for name, path in EXISTING.items():
            lines = list(dict.fromkeys(old for old, _ in edits[name]))
            target = self.base / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(lines) + "\n")
        target = self.base / REPLACEMENT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("package synthetic.upstream\n")
        (self.base / "settings.gradle.kts").write_text("// pinned Kotlin baseline subset\n")
        shutil.copytree(self.base, self.out)
        p = subprocess.run([sys.executable, str(self.stage / "apply_spike001.py"), str(self.out)],
                           capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"Synthetic upstream did not accept real patcher: {p.stderr}")

    def assertValid(self):
        return verify(self.base, self.out, stage=self.stage, patcher=self.stage / "apply_spike001.py")

    def test_complete_patch_applies_all_28_edits_and_18_new_files(self):
        self.assertEqual(self.assertValid(), (28, EXPECTED_NEW_FILES, 7))

    def test_all_literal_patch_replacements_are_free_of_trailing_whitespace(self):
        # Git diff --check must reject whitespace errors, not be bypassed.
        # Regression: MangaViewModel.kt:339 had an inserted whitespace-only line.
        edits = operations(self.stage / "apply_spike001.py")
        for name, changes in edits.items():
            for change_index, (_old, replacement) in enumerate(changes, start=1):
                for line_index, line in enumerate(replacement.splitlines(), start=1):
                    self.assertEqual(
                        line, line.rstrip(),
                        f"{name} replacement {change_index} line {line_index} "
                        "introduces trailing whitespace",
                    )

    def test_expected_patch_footprint_is_explicit(self):
        self.assertEqual({k: len(v) for k, v in operations(self.stage / "apply_spike001.py").items()}, EXPECTED_OPS)

    def test_win32_crlf_baseline_is_normalized_for_exact_patch_contract(self):
        # Git autocrlf can produce CRLF in a pristine pinned Windows worktree.
        # The patcher reads it as LF and writes canonical LF output.
        base_file = self.base / EXISTING["dm"]
        base_file.write_bytes(base_file.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(self.assertValid(), (28, EXPECTED_NEW_FILES, 7))

    def test_win32_crlf_patched_file_is_rejected(self):
        # Do not weaken the contract by accepting noncanonical patched bytes.
        patched_file = self.out / EXISTING["dm"]
        patched_file.write_bytes(patched_file.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(IntegrationContractError, "Windows CRLF"):
            self.assertValid()

    def test_replace_once_always_writes_lf_without_host_newline_translation(self):
        import runpy
        from unittest.mock import patch
        replace_once = runpy.run_path(
            str(self.stage / "apply_spike001.py"),
            run_name="polaris_test_patcher"
        )["replace_once"]
        path = self.root / "original_CRLF.kt"
        path.write_bytes(b"before\r\nANCHOR\r\nafter\r\n")
        # A Win32-style Path.write_text would translate LF to CRLF.
        # Forbid that API to ensure deterministic binary writes are used.
        with patch.object(Path, "write_text", side_effect=AssertionError("OS-dependent newline writer")):
            replace_once(path, "ANCHOR\n", "REPLACED\n")
        self.assertEqual(path.read_bytes(), b"before\nREPLACED\nafter\n")

    def test_modified_domain_registration_fails(self):
        p = self.out / EXISTING["dm"]
        p.write_text(p.read_text().replace("GetMergedReferencesById(get())", "GetMergedReferencesById()"))
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_removed_source_manager_registration_fails(self):
        p = self.out / EXISTING["sm"]
        p.write_text(p.read_text().replace("MERGED_SOURCE_ID to MergedSource(),", ""))
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_reader_routing_drift_fails(self):
        p = self.out / EXISTING["ms"]
        p.write_text(p.read_text().replace("readerSource is INovelSource", "source is INovelSource"))
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_missing_migration_fails(self):
        p = self.out / "data/src/main/sqldelight/tachiyomi/migrations/14.sqm"
        p.unlink()
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_stale_sql_query_fails(self):
        p = self.out / "data/src/main/sqldelight/tachiyomi/data/merged.sq"
        p.write_text(p.read_text() + "\n--stale query")
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_unpatched_original_get_manga_with_chapters_fails(self):
        shutil.copy2(self.base / REPLACEMENT, self.out / REPLACEMENT)
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_baseline_collision_rejected(self):
        collision = self.base / "domain/src/main/java/tachiyomi/domain/manga/model/MergedMangaReference.kt"
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text("old version")
        with self.assertRaises(IntegrationContractError):
            self.assertValid()

    def test_missing_baseline_edit_anchor_rejected(self):
        p = self.base / EXISTING["lj"]
        p.write_text(p.read_text().replace("mangaToUpdate = listToUpdate", "mangaToUpdate = candidates"))
        with self.assertRaises(IntegrationContractError):
            self.assertValid()


if __name__ == "__main__":
    unittest.main()
