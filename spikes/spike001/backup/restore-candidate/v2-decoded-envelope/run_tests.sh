#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
kotlinc "$HERE/PolarisV2SnapshotAdmission.kt" "$HERE/host/AdmissionHostTest.kt" -include-runtime -d "$TMP/admission.jar"
java -jar "$TMP/admission.jar" | tee "$TMP/test.log"
grep -qx 'POLARIS_V2_BOUND_SNAPSHOT_HOST_PASS 20' "$TMP/test.log"
