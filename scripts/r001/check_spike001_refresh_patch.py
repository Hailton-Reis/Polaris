#!/usr/bin/env python3
"""Validate actual pinned MangaViewModel patch anchors before/after Spike-001.

This only checks patch wiring. Android Gradle/Reader runtime remain separate gates.
"""
import argparse
import ast
from pathlib import Path
import sys


class PatchContractError(Exception):
    pass


def vm_operations(applicator: Path) -> list[tuple[str, str]]:
    try:
        tree = ast.parse(applicator.read_text())
    except (OSError, SyntaxError) as exc:
        raise PatchContractError(f"Invalid Spike-001 applicator: {exc}") from exc
    operations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "replace_once":
            continue
        if len(node.args) != 3 or not isinstance(node.args[0], ast.Name) or node.args[0].id != "vm":
            continue
        try:
            old, replacement = (ast.literal_eval(arg) for arg in node.args[1:])
        except (ValueError, TypeError) as exc:
            raise PatchContractError("VM patch contains a dynamic expression") from exc
        if not isinstance(old, str) or not isinstance(replacement, str) or not old or not replacement:
            raise PatchContractError("VM patch must use nonempty constant string replacements")
        operations.append((old, replacement))
    if len(operations) != 4:
        raise PatchContractError(f"Expected exactly four VM patch operations; found {len(operations)}")
    return operations


def check_patch(vm_text: str, operations: list[tuple[str, str]], mode: str) -> None:
    current = vm_text
    if mode == "baseline":
        for index, (old, new) in enumerate(operations, 1):
            occurrences = current.count(old)
            if occurrences != 1:
                raise PatchContractError(f"Baseline replacement {index} matched {occurrences}, expected exactly one")
            current = current.replace(old, new, 1)
    elif mode == "patched":
        for index, (_, new) in enumerate(operations, 1):
            occurrences = current.count(new)
            if occurrences != 1:
                raise PatchContractError(f"Patched replacement {index} matched {occurrences}, expected exactly one")
    else:
        raise ValueError(f"Unknown mode: {mode}")
    for required in (
        "if (state.source is MergedSource)",
        "MergedRefreshCoordinator.refresh(",
        "val child = mangaRepository.getMangaById(childId)",
        "updateMangaFromRemote(\n                                manga = child,",
        "onFailure = { childId, error ->",
        "no automatic downloads are scheduled from this virtual screen.",
    ):
        if required not in current:
            raise PatchContractError(f"Missing virtual refresh wiring: {required}")
    if "import tachiyomi.domain.manga.refresh.MergedRefreshCoordinator" not in current:
        raise PatchContractError("Merged refresh coordinator is not imported")
    if "import tachiyomi.domain.source.model.MERGED_SOURCE_ID" not in current:
        raise PatchContractError("Virtual source identity not imported")
    if "source = state.source,\n                        manga = state.manga" not in current:
        raise PatchContractError("Original nonvirtual refresh branch was changed unexpectedly")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--mode", choices=("baseline", "patched"), required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    source = args.checkout / "app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaViewModel.kt"
    try:
        check_patch(source.read_text(), vm_operations(repo / "spikes/spike001/apply_spike001.py"), args.mode)
    except (OSError, PatchContractError) as exc:
        print(f"SPIKE001_VM_PATCH_CONTRACT_FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"SPIKE001_VM_PATCH_CONTRACT_PASS mode={args.mode}; NOT_ANDROID_RUNTIME")
    return 0


if __name__ == "__main__":
    sys.exit(main())
