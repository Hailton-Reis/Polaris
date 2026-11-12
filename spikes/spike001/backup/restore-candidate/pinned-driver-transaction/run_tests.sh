#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
kotlinc "$HERE/SqlDelightHostStubs.kt" "$HERE/DatabaseHostStub.kt" "$HERE/PolarisDeferredFkTransaction.kt" "$HERE/PolarisDeferredFkTransactionTest.kt" -include-runtime -d "$TMP/guard-tests.jar"
java -jar "$TMP/guard-tests.jar"
