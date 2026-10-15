#!/usr/bin/env python3
"""Run Polaris R001 offline gates with fail-closed machine-readable evidence.

This is a host-only check. It never proves an Android APK or B01-B05 runtime.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

GATES = (
    ("python", (sys.executable, "-m", "unittest", "discover", "-s", "scripts/r001", "-p", "test_*.py", "-q"), 72),
    ("sqlite", (sys.executable, "-m", "unittest", "discover", "-s", "spikes/spike001/host-sqlite", "-p", "test_*.py", "-q"), 36),
    ("kotlin", ("bash", "scripts/r001/test_spike001_host.sh"), 38),
    ("backup-sqlite", (sys.executable, "-m", "unittest", "discover", "-s", "spikes/spike001/backup", "-p", "test_*.py", "-q"), 17),
    ("backup-kotlin", ("bash", "spikes/spike001/backup/run_tests.sh"), 59),
)


def extract_count(name: str, output: str):
    if name == "backup-kotlin":
        # All three Kotlin suites must pass. Missing, repeated or spoofed
        # success markers must never turn a partial run into PASS.
        required_markers = (
            r"(?m)^MERGED_BACKUP_RESTORE_PLANNER_PASS (\d+)$",
            r"(?m)^MERGED_BACKUP_EXPORT_PLANNER_PASS (\d+)$",
            r"(?m)^POLARIS_PERSISTED_MERGE_UUID_PASS (\d+)$",
        )
        matches = [re.findall(regex, output) for regex in required_markers]
        return sum(int(values[0]) for values in matches) if all(len(values) == 1 for values in matches) else None
    regex = (r"SPIKE001_HOST_INVARIANTS_PASS \((\d+) scenarios\); NOT_ANDROID_RUNTIME"
             if name == "kotlin" else r"Ran (\d+) tests? in ")
    hits = re.findall(regex, output)
    return int(hits[-1]) if len(hits) == 1 else None

def evaluate_gate(name: str, output: str, returncode: int, minimum: int):
    count = extract_count(name, output)
    passed = returncode == 0 and count is not None and count >= minimum
    if name not in {"kotlin", "backup-kotlin"}:
        passed = passed and bool(re.search(r"(?m)^OK(?:\s|$)", output))
    reason = ("PASS" if passed else
              "MISSING_OR_INVALID_TEST_SUMMARY" if count is None else
              "NONZERO_EXIT" if returncode != 0 else
              "INSUFFICIENT_TEST_COVERAGE" if count < minimum else
              "MISSING_UNITTEST_OK_MARKER")
    return {"status": reason, "cases": count, "required": minimum, "exit_code": returncode}


def run_all(root: Path, report_dir: Path):
    report_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, cmd, required in GATES:
        try:
            done = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, check=False)
            output, exitcode = done.stdout, done.returncode
        except (OSError, ValueError) as exc:
            output, exitcode = str(exc), 127
        (report_dir / f"{name}.log").write_text(output, encoding="utf-8")
        result = evaluate_gate(name, output, exitcode, required)
        result.update({"gate": name, "command": list(cmd), "log": f"{name}.log"})
        entries.append(result)
        print(f"{name}: {result['status']} ({result['cases']}/{required})")
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    all_pass = all(e["status"] == "PASS" for e in entries)
    report = {"schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "repo_commit": head, "scope": "HOST_ONLY_NOT_ANDROID_RUNTIME",
              "status": "PASS" if all_pass else "FAIL_OR_INCONCLUSIVE",
              "gates": entries}
    (report_dir / "host-gate-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if all_pass else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--evidence-dir", type=Path, required=True)
    args = p.parse_args()
    return run_all(args.root.resolve(), args.evidence_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
