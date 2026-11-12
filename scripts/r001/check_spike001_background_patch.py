#!/usr/bin/env python3
"""Verify Spike-001 leaves Yomotsu automatic updaters on real sources only.

This validates exact source patch anchors, not Android execution.
"""
import argparse
import ast
from pathlib import Path
import sys


class BackgroundPatchContractError(Exception):
    pass


JOB_PATHS = {
    "lj": "app/src/main/java/eu/kanade/tachiyomi/data/library/LibraryUpdateJob.kt",
    "mj": "app/src/main/java/eu/kanade/tachiyomi/data/library/MetadataUpdateJob.kt",
}


def job_operations(applicator: Path) -> dict[str, list[tuple[str, str]]]:
    try:
        tree = ast.parse(applicator.read_text())
    except (OSError, SyntaxError) as e:
        raise BackgroundPatchContractError(f"Cannot parse applicator: {e}") from e
    found: dict[str, list[tuple[str, str]]] = {name: [] for name in JOB_PATHS}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "replace_once" or len(node.args) != 3:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Name) or first.id not in JOB_PATHS:
            continue
        try:
            old, new = (ast.literal_eval(arg) for arg in node.args[1:])
        except (TypeError, ValueError) as e:
            raise BackgroundPatchContractError("Dynamic background patch anchor") from e
        if not isinstance(old, str) or not isinstance(new, str) or not old or not new:
            raise BackgroundPatchContractError("Background patch needs literal nonempty strings")
        found[first.id].append((old, new))
    for name, edits in found.items():
        if len(edits) != 2:
            raise BackgroundPatchContractError(f"Expected 2 {name} updates, got {len(edits)}")
    return found


def check_job(text: str, edits: list[tuple[str, str]], mode: str, job: str) -> None:
    if job not in JOB_PATHS:
        raise BackgroundPatchContractError(f"Unknown job: {job}")
    if mode == "baseline":
        patched = text
        for idx, (old, new) in enumerate(edits, 1):
            count = patched.count(old)
            if count != 1:
                raise BackgroundPatchContractError(f"{job} baseline anchor {idx}: {count} matches")
            patched = patched.replace(old, new, 1)
    elif mode == "patched":
        patched = text
        original = text
        for idx in range(len(edits) - 1, -1, -1):
            old, new = edits[idx]
            count = original.count(new)
            if count != 1:
                raise BackgroundPatchContractError(f"{job} reverse block {idx+1}: {count} matches")
            original = original.replace(new, old, 1)
        regenerated = original
        for idx, (old, new) in enumerate(edits, 1):
            count = regenerated.count(old)
            if count != 1:
                raise BackgroundPatchContractError(f"{job} reconstructed anchor {idx}: {count} matches")
            regenerated = regenerated.replace(old, new, 1)
        if regenerated != text:
            raise BackgroundPatchContractError(f"{job} patched text not reconstructible")
    else:
        raise BackgroundPatchContractError(f"Unknown mode: {mode}")

    if "import tachiyomi.domain.source.model.MERGED_SOURCE_ID" not in patched:
        raise BackgroundPatchContractError(f"{job} missing virtual source import")
    if job == "lj":
        expected = ("mangaToUpdate = listToUpdate\n"
                    "            .filter { it.manga.source != MERGED_SOURCE_ID }\n"
                    "            .filter {")
    else:
        expected = ("mangaToUpdate = getLibraryManga.await()\n"
                    "            .filter { it.manga.source != MERGED_SOURCE_ID }")
    if patched.count(expected) != 1:
        raise BackgroundPatchContractError(f"{job} lacks one safe virtual-source queue filter")
    if patched.count("it.manga.source != MERGED_SOURCE_ID") != 1:
        raise BackgroundPatchContractError(f"{job} virtual exclusion must occur exactly once")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--mode", choices=["baseline", "patched"], required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        all_ops = job_operations(root / "spikes/spike001/apply_spike001.py")
        for name, path in JOB_PATHS.items():
            check_job((args.checkout / path).read_text(), all_ops[name], args.mode, name)
    except (OSError, BackgroundPatchContractError) as exc:
        print(f"POLARIS_BACKGROUND_REFRESH_PATCH_FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"POLARIS_BACKGROUND_REFRESH_PATCH_PASS mode={args.mode}; NOT_ANDROID_RUNTIME")
    return 0


if __name__ == "__main__":
    sys.exit(main())
