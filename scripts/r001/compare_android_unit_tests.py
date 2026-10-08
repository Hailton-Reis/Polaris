#!/usr/bin/env python3
"""Compare Android JUnit XML against the unmodified pinned Yomotsu baseline.

A zero exit code means NO NEW failures or skips. It does NOT mean all tests pass,
that the Android runtime was tested, or that a failed Gradle build can be ignored.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


class ReportError(Exception):
    pass


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
        raise ReportError(f"No executed testDebugUnitTest JUnit XML test cases under {root}")
    return cases


def compare(baseline: dict, patched: dict) -> dict:
    missing = sorted(set(baseline) - set(patched))
    regressions = sorted(
        (key, baseline.get(key, "new"), state)
        for key, state in patched.items()
        if (state == "failed" and baseline.get(key) != "failed")
        or (state == "skipped" and baseline.get(key) != "skipped")
    )
    baseline_counts = Counter(baseline.values())
    patched_counts = Counter(patched.values())
    existing_failures = sorted(key for key, status in patched.items() if status == "failed" and baseline.get(key) == "failed")
    return {
        "status": "NO_NEW_UNIT_REGRESSIONS" if not missing and not regressions else "REGRESSION_DETECTED",
        "baseline": {"total": len(baseline), **{status: baseline_counts[status] for status in ("passed", "failed", "skipped")}},
        "patched": {"total": len(patched), **{status: patched_counts[status] for status in ("passed", "failed", "skipped")}},
        "preexisting_failures_still_present": len(existing_failures),
        "missing_baseline_tests": [list(key) for key in missing],
        "new_failures_or_skips": [list((*key, old, new)) for key, old, new in regressions],
        "android_runtime_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("patched", type=Path)
    parser.add_argument("--output", type=Path, help="Write machine-readable comparison")
    parser.add_argument("--baseline-exit", type=int, default=0)
    parser.add_argument("--patched-exit", type=int, default=0)
    args = parser.parse_args()
    try:
        original = collect(args.baseline)
        modified = collect(args.patched)
        result = compare(original, modified)
        result["gradle_exit_codes"] = {"baseline": args.baseline_exit, "patched": args.patched_exit}
        for which, exit_code, cases in (("baseline", args.baseline_exit, original), ("patched", args.patched_exit, modified)):
            # Nonzero Gradle status is permissible only if the JUnit results actually
            # contain failing tests. Otherwise a build/infrastructure error may be hidden.
            if exit_code != 0 and "failed" not in cases.values():
                raise ReportError(f"{which} Gradle exited {exit_code} but JUnit has no failing tests")
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
