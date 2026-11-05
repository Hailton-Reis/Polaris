#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)";trap 'rm -rf "$TMP"' EXIT
bash "$HERE/run_tests.sh" | tee "$TMP/host.log"
bash "$HERE/run_gateway_tests.sh" | tee "$TMP/gateway.log"
python3 -m unittest discover -s "$HERE/tests" -p 'test_*.py' -v 2>&1 | tee "$TMP/wire.log"
grep -qx 'POLARIS_V2_BOUND_SNAPSHOT_HOST_PASS 20' "$TMP/host.log"
grep -qx 'POLARIS_V2_DECODED_ENVELOPE_HOST_PASS 22' "$TMP/gateway.log"
grep -Eq '^Ran 16 tests in ' "$TMP/wire.log"
grep -qx 'OK' "$TMP/wire.log"
if grep -Eqi '^FAIL|^ERROR|skipped=' "$TMP"/*.log;then exit 1;fi
printf 'POLARIS_V2_BOUND_ARCHIVE_GATE_PASS 58\n'
