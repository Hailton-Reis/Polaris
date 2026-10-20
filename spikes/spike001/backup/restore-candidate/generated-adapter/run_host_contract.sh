#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 -m unittest discover -s "$HERE/tests" -p 'test_generated_query_contract.py' -v 2>&1 | tee "$TMP/query_contract.log"
if ! grep -Eq '^Ran 30 tests in ' "$TMP/query_contract.log" || ! grep -qx 'OK' "$TMP/query_contract.log"; then echo 'CONTRACT_INCOMPLETE' >&2; exit 1; fi
bash "$HERE/run_tests.sh" 2>&1 | tee "$TMP/kotlin_host.log"
if [ "$(grep -cx 'POLARIS_FRESH_PARENT_ADAPTER_HOST_PASS 38' "$TMP/kotlin_host.log")" != 1 ]; then echo 'KOTLIN_INCOMPLETE' >&2;exit 1;fi
if grep -Eqi 'skipped=|^FAIL|^ERROR' "$TMP/query_contract.log" "$TMP/kotlin_host.log"; then echo 'FAKE_GREEN_BLOCKED' >&2;exit 1;fi
printf 'POLARIS_GENERATED_QUERY_BRIDGE_PASS 68\n'
