#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)";trap 'rm -rf "$TMP"' EXIT
kotlinc "$HERE/SqlDelightPolarisFreshParentAdapter.kt" \
  "$HERE/host/PolarisDeferredFkTransaction.kt" \
  "$HERE/host/PolarisBackupMangaSqlProjection.kt" \
  "$HERE/host/ProjectionHostBackup.kt" "$HERE/host/ProjectionHostAdapter.kt" \
  "$HERE/host/ProjectionHostJson.kt" "$HERE/host/ProjectionHostStubs.kt" \
  "$HERE/host/SqlDelightHostStubs.kt" "$HERE/host/QueryHostStubs.kt" \
  "$HERE/host/DatabaseHostStub.kt" "$HERE/host/DriverHostStub.kt" \
  "$HERE/host/AdapterHostTest.kt" -include-runtime -d "$TMP/adapter-host.jar"
java -jar "$TMP/adapter-host.jar"
