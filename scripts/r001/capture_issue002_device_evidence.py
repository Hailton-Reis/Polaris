#!/usr/bin/env python3
"""Capture short, read-only Android evidence for Polaris issue #2 B01/B02/B03.

Capturing a screenshot/log is NOT a PASS. A human must verify source content,
real child IDs, list membership and post-removal integrity separately.
This intentionally avoids a whole logcat/device dump and collects no credentials.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PHASES = ("B01", "B02A", "B02B", "B03")


class CaptureError(Exception):
    pass


def adb_call(adb: str, serial: str | None, args: list[str], timeout: int = 20) -> bytes:
    command = [adb] + (["-s", serial] if serial else []) + args
    try:
        response = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CaptureError(f"ADB call failed or timed out: {args[0]}") from exc
    if response.returncode:
        raise CaptureError(f"ADB {args[0]} failed (exit={response.returncode}): "
                           + response.stderr.decode(errors="replace")[:500])
    return response.stdout


def capture(adb: str, serial: str | None, phase: str, out: Path, apk: Path,
            child_a: int, child_b: int, merge_id: int | None):
    if child_a <= 0 or child_b <= 0 or child_a == child_b:
        raise CaptureError("Provide two different positive REAL manga child IDs")
    if phase in ("B02A", "B02B", "B03") and (merge_id is None or merge_id <= 0):
        raise CaptureError("A positive merge ID is required for B02A/B02B/B03")
    if not apk.is_file():
        raise CaptureError(f"APK file not found: {apk}")
    if out.exists() and any(out.iterdir()):
        raise CaptureError(f"Evidence directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    if adb_call(adb, serial, ["get-state"]).strip() != b"device":
        raise CaptureError("ADB state is not device")
    properties = {}
    for key in ("ro.build.version.sdk", "ro.product.cpu.abi", "ro.build.fingerprint"):
        properties[key] = adb_call(adb, serial, ["shell", "getprop", key]).decode(errors="replace").strip()
    if not properties["ro.build.version.sdk"].isdigit():
        raise CaptureError("Invalid Android SDK property; device is not ready")
    png = adb_call(adb, serial, ["exec-out", "screencap", "-p"], timeout=30)
    if not png.startswith(PNG_MAGIC):
        raise CaptureError("Screenshot is not a valid PNG header")
    (out / "screen.png").write_bytes(png)
    log = adb_call(adb, serial, ["logcat", "-d", "-s", "PolarisSpike001:I", "AndroidRuntime:E", "*:S"])
    (out / "polaris-and-crashes.log").write_bytes(log)
    apk_hash = hashlib.sha256(apk.read_bytes()).hexdigest()
    evidence = {
        "project": "Polaris", "issue": 2, "phase": phase,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "device_serial": serial or "adb-default", "device": properties,
        "apk_sha256": apk_hash, "child_a_manga_id": child_a,
        "child_b_manga_id": child_b, "merged_manga_id": merge_id,
        "files": ["screen.png", "polaris-and-crashes.log"],
        "runtime_verdict": "CAPTURED_UNVERIFIED",
        "manual_checks_pending": {
            "B01": "Both real sources shown under one virtual manga",
            "B02A": "Chapter from child A opens and actually loads Source A pages",
            "B02B": "Chapter from child B opens and actually loads Source B pages",
            "B03": "After reference removal the virtual parent and child B remain usable",
        },
        "note": "Screen/log capture alone never certifies B01/B02/B03 or Android acceptance.",
    }
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=PHASES)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial", help="ADB serial if more than one device is connected")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--child-a", type=int, required=True)
    parser.add_argument("--child-b", type=int, required=True)
    parser.add_argument("--merge-id", type=int)
    args = parser.parse_args()
    try:
        result = capture(args.adb, args.serial, args.phase, args.out, args.apk,
                         args.child_a, args.child_b, args.merge_id)
        print(f"CAPTURED_UNVERIFIED {args.phase}: {args.out.resolve()}")
        print(f"Device API {result['device']['ro.build.version.sdk']}; APK {result['apk_sha256']}")
        return 0
    except (CaptureError, OSError) as exc:
        print(f"CAPTURE_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
