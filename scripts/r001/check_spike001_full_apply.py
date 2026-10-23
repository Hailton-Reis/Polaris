#!/usr/bin/env python3
"""Fail-closed contract for *all* staged Spike-001 changes against pinned source files.

Compares a pristine pinned Yomotsu checkout to its patched copy, including
all 28 literal patch operations, 18 added files, and the replaced interactor.
This never claims an Android compile or reader runtime PASS.
"""
import argparse
import ast
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "spikes/spike001"
PATCHER = STAGE / "apply_spike001.py"

EXISTING = {
    "dm": "app/src/main/java/eu/kanade/domain/DomainModule.kt",
    "sm": "app/src/main/java/eu/kanade/tachiyomi/source/AndroidSourceManager.kt",
    "ms": "app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaScreen.kt",
    "lj": "app/src/main/java/eu/kanade/tachiyomi/data/library/LibraryUpdateJob.kt",
    "mj": "app/src/main/java/eu/kanade/tachiyomi/data/library/MetadataUpdateJob.kt",
    "vm": "app/src/main/java/eu/kanade/tachiyomi/ui/manga/MangaViewModel.kt",
}
REPLACEMENT = "domain/src/main/java/tachiyomi/domain/manga/interactor/GetMangaWithChapters.kt"
EXPECTED_OPS = {"dm": 8, "sm": 2, "ms": 10, "lj": 2, "mj": 2, "vm": 4}
EXPECTED_NEW_FILES = 18


class IntegrationContractError(Exception):
    pass


def operations(patcher=PATCHER):
    try:
        source = ast.parse(Path(patcher).read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise IntegrationContractError(f"Applicator is not parseable: {exc}") from exc
    result = defaultdict(list)
    # ast.walk preserves statement order for this straightforward patcher.
    for call in ast.walk(source):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            continue
        if call.func.id != "replace_once":
            continue
        if len(call.args) != 3 or not isinstance(call.args[0], ast.Name):
            raise IntegrationContractError("Non-literal/unknown replace_once invocation")
        name = call.args[0].id
        if name not in EXISTING:
            raise IntegrationContractError(f"Unknown patch target {name!r}")
        try:
            old, new = [ast.literal_eval(x) for x in call.args[1:]]
        except (TypeError, ValueError) as exc:
            raise IntegrationContractError(f"Dynamic edit for {name}") from exc
        if not isinstance(old, str) or not isinstance(new, str) or not old or not new or old == new:
            raise IntegrationContractError(f"Invalid literal replacement for {name}")
        result[name].append((old, new))
    if {k: len(v) for k, v in result.items()} != EXPECTED_OPS:
        raise IntegrationContractError(f"Unexpected integration edit footprint: {dict((k, len(v)) for k,v in result.items())}")
    return result


def verify(baseline, patched, stage=STAGE, patcher=PATCHER):
    baseline, patched, stage = map(Path, (baseline, patched, stage))
    changes = operations(patcher)
    for variable, relative in EXISTING.items():
        base_file = baseline / relative
        patched_file = patched / relative
        try:
            # Git on Windows can check out the upstream file with CRLF;
            # Path.read_text normalizes this to the same LF anchors used by
            # apply_spike001.replace_once. Patched output must still be
            # byte-exact and LF-only: never normalize the output being checked.
            source = base_file.read_text(encoding="utf-8")
            actual = patched_file.read_bytes().decode("utf-8")
        except OSError as exc:
            raise IntegrationContractError(f"Missing input {relative}: {exc}") from exc
        expected = source
        for i, (old, new) in enumerate(changes[variable], start=1):
            n = expected.count(old)
            if n != 1:
                raise IntegrationContractError(f"Pinned {relative} edit {i}: {n} old anchors (expected 1)")
            expected = expected.replace(old, new, 1)
        if actual != expected:
            if "\r\n" in actual:
                raise IntegrationContractError(
                    f"Patched {relative} contains Windows CRLF bytes; "
                    "the Spike-001 applicator must write canonical LF bytes"
                )
            raise IntegrationContractError(
                f"Patched {relative} differs from exact expected edits "
                f"(expected_chars={len(expected)}, actual_chars={len(actual)})"
            )

    # The replacement is deliberate, and must not leave the old file in place.
    replacement = stage / "REPLACEMENT_GetMangaWithChapters.kt"
    try:
        if (patched / REPLACEMENT).read_bytes() != replacement.read_bytes():
            raise IntegrationContractError("GetMangaWithChapters is not the staged replacement")
        original = (baseline / REPLACEMENT).read_bytes()
        if original == replacement.read_bytes():
            raise IntegrationContractError("Baseline already has patched interactor")
    except OSError as exc:
        raise IntegrationContractError(f"Missing GetMangaWithChapters source: {exc}") from exc

    staging = stage / "new-files"
    files = sorted(p for p in staging.rglob("*") if p.is_file())
    if len(files) != EXPECTED_NEW_FILES:
        raise IntegrationContractError(f"Unexpected new-file footprint: {len(files)} (expected {EXPECTED_NEW_FILES})")
    for source in files:
        relative = source.relative_to(staging)
        target = patched / relative
        if (baseline / relative).exists():
            raise IntegrationContractError(f"New-file {relative} collides with pinned upstream")
        try:
            if source.read_bytes() != target.read_bytes():
                raise IntegrationContractError(f"Added {relative} differs from staged version")
        except OSError as exc:
            raise IntegrationContractError(f"Missing staged file {relative}: {exc}") from exc
    return sum(map(len, changes.values())), len(files), len(EXISTING) + 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("patched", type=Path)
    args = p.parse_args()
    try:
        edits, added, modified = verify(args.baseline, args.patched)
    except IntegrationContractError as exc:
        print(f"SPIKE001_FULL_APPLY_CONTRACT_FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"SPIKE001_FULL_APPLY_CONTRACT_PASS edits={edits} added={added} replaced_or_modified={modified}; NOT_ANDROID_RUNTIME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
