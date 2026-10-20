#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)";trap 'rm -rf "$TMP"' EXIT
bash "$HERE/run_bound_adapter_tests.sh" 2>&1 | tee "$TMP/bound.log"
bash "$HERE/../generated-adapter/run_host_contract.sh" 2>&1 | tee "$TMP/adapter.log"
bash "$HERE/run_all.sh" 2>&1 | tee "$TMP/gateway.log"
grep -qx 'POLARIS_V2_BOUND_RESTORE_BRIDGE_PASS 26' "$TMP/bound.log"
grep -qx 'POLARIS_GENERATED_QUERY_BRIDGE_PASS 76' "$TMP/adapter.log"
grep -qx 'POLARIS_V2_BOUND_ARCHIVE_GATE_PASS 58' "$TMP/gateway.log"
if grep -Eqi 'skipped=|^FAIL|^ERROR' "$TMP"/*.log; then exit 1; fi
printf 'POLARIS_V2_BOUND_INTEGRATION_PASS 160\n'
