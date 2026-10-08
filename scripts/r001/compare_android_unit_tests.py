#!/usr/bin/env python3
"""Compare complete Android JUnit results with the pinned unmodified baseline.

NO_NEW_UNIT_REGRESSIONS is not equivalent to all-tests-green or device PASS.
Fail closed on absent/truncated report coverage and non-test Gradle failures.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


class ReportError(Exception):
    pass


FAILED_TASK = re.compile(r"^\s*> Task (:\S+) FAILED\s*$", re.MULTILINE)
ALLOWED_FAILED_TASKS = {
    ":domain:testDebugUnitTest", ":data:testDebugUnitTest", ":app:testDebugUnitTest",
}


def collect(root: Path) -> dict[tuple[str, str, str], str]:
    if not root.is_dir():
        raise ReportError(f"Missing checkout directory: {root}")
    cases: dict[tuple[str, str, str], str] = {}
    reports = 0
    for report in root.rglob("TEST-*.xml"):
        relative = report.relative_to(root).parts
        if "build" not in relative:
            continue
        index = relative.index("build")
        if relative[index + 1:index + 3] != ("test-results", "testDebugUnitTest"):
            continue
        module = "/".join(relative[:index])
        if not module:
            raise ReportError(f"Cannot identify module for {report}")
        try:
            xml_root = ET.parse(report).getroot()
        except (ET.ParseError, OSError) as exc:
            raise ReportError(f"Invalid XML report {report}: {exc}") from exc
        if xml_root.tag not in ("testsuite", "testsuites"):
            raise ReportError(f"Unexpected XML root in {report}: {xml_root.tag}")
        reports += 1
        for node in xml_root.iter("testcase"):
            classname, name = node.get("classname"), node.get("name")
            if not classname or not name:
                raise ReportError(f"Test case lacks classname/name in {report}")
            key = (module, classname, name)
            if key in cases:
                raise ReportError(f"Duplicate test case {key} in {report}")
            if node.find("failure") is not None or node.find("error") is not None:
                state = "failed"
            elif node.find("skipped") is not None:
                state = "skipped"
            else:
                state = "passed"
            cases[key] = state
    if reports == 0 or not cases:
        raise ReportError(f"No executed testDebugUnitTest JUnit XML cases under {root}")
    return cases


def check_coverage(cases: dict, minima: dict[str, int], side: str):
    observed = Counter(module for module, _, _ in cases)
    for module, required in minima.items():
        if observed[module] < required:
            raise ReportError(
                f"{side} has {observed[module]} tests for {module}; minimum {required}. "
                "Report may be missing/incomplete or execution aborted."
            )


def check_gradle(log_path: Path | None, exit_code: int, cases: dict, side: str):
    if log_path is None:
        if exit_code:
            raise ReportError(f"{side} nonzero Gradle exit requires --{side}-log for failure classification")
        return
    if not log_path.is_file():
        raise ReportError(f"{side} Gradle log missing: {log_path}")
    log = log_path.read_text(errors="replace")
    if "BUILD FAILED" in log and exit_code == 0:
        raise ReportError(f"{side} Gradle log says BUILD FAILED but exit code is zero")
    if "BUILD SUCCESSFUL" in log and exit_code != 0:
        raise ReportError(f"{side} Gradle log says BUILD SUCCESSFUL but exit code is {exit_code}")
    if exit_code == 0:
        if "BUILD SUCCESSFUL" not in log:
            raise ReportError(f"{side} Gradle log lacks BUILD SUCCESSFUL")
        return
    failed_tasks = set(FAILED_TASK.findall(log))
    if not failed_tasks or not failed_tasks.issubset(ALLOWED_FAILED_TASKS):
        raise ReportError(f"{side} has non-unit-test or unidentified Gradle failure: {sorted(failed_tasks)}")
    failed_modules = {task.split(":")[1] for task in failed_tasks}
    if any(not any(key[0] == module and status == "failed" for key, status in cases.items())
           for module in failed_modules):
        raise ReportError(f"{side} has failed test tasks without matching failed JUnit cases")
    if "BUILD FAILED" not in log:
        raise ReportError(f"{side} nonzero Gradle exit lacks BUILD FAILED")


def compare(baseline: dict, patched: dict) -> dict:
    missing = sorted(set(baseline) - set(patched))
    regressions = sorted(
        (key, baseline.get(key, "new"), state)
        for key, state in patched.items()
        if (state == "failed" and baseline.get(key) != "failed")
        or (state == "skipped" and baseline.get(key) != "skipped")
    )
    counts = lambda cases: {"total": len(cases), **{s: Counter(cases.values())[s] for s in ("passed", "failed", "skipped")}}
    existing = [key for key, state in patched.items() if state == "failed" and baseline.get(key) == "failed"]
    return {
        "status": "NO_NEW_UNIT_REGRESSIONS" if not missing and not regressions else "REGRESSION_DETECTED",
        "baseline": counts(baseline), "patched": counts(patched),
        "preexisting_failures_still_present": len(existing),
        "missing_baseline_tests": [list(k) for k in missing],
        "new_failures_or_skips": [list((*key, old, new)) for key, old, new in regressions],
        "android_runtime_verified": False,
    }


def parse_minimum(value: str) -> tuple[str, int]:
    try:
        module, count = value.split("=", 1)
        count = int(count)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", module) or count < 1:
            raise ValueError
        return module, count
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected MODULE=POSITIVE_INTEGER") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("patched", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline-exit", type=int, default=0)
    parser.add_argument("--patched-exit", type=int, default=0)
    parser.add_argument("--baseline-log", type=Path)
    parser.add_argument("--patched-log", type=Path)
    parser.add_argument("--min-module", action="append", default=[], type=parse_minimum)
    args = parser.parse_args()
    try:
        original = collect(args.baseline)
        modified = collect(args.patched)
        minima = dict(args.min_module)
        check_coverage(original, minima, "baseline")
        check_coverage(modified, minima, "patched")
        check_gradle(args.baseline_log, args.baseline_exit, original, "baseline")
        check_gradle(args.patched_log, args.patched_exit, modified, "patched")
        result = compare(original, modified)
        result["gradle_exit_codes"] = {"baseline": args.baseline_exit, "patched": args.patched_exit}
        result["required_module_coverage"] = minima
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
        for label in ("baseline", "patched"):
            print(f"{label}: {result[label]}")
        print(f"Preexisting failures still present: {result['preexisting_failures_still_present']}")
        if result["status"] != "NO_NEW_UNIT_REGRESSIONS":
            print("UNIT_REGRESSION_DETECTED", file=sys.stderr)
            for name in ("missing_baseline_tests", "new_failures_or_skips"):
                for entry in result[name]:
                    print(f"{name}: {entry}", file=sys.stderr)
            return 1
        print("NO_NEW_UNIT_REGRESSIONS_PASS (not all-tests-green; not Android runtime acceptance)")
        return 0
    except ReportError as exc:
        print(f"UNIT_COMPARISON_INCONCLUSIVE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
