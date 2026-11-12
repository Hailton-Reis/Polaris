#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)";trap 'rm -rf "$TMP"' EXIT
kotlinc "$HERE/SqlDelightPolarisFreshParentAdapter.kt" \
  "$HERE/../v2-decoded-envelope/PolarisV2SnapshotAdmission.kt" \
  "$HERE/../v2-decoded-envelope/PolarisV2DecodedEnvelopeGateway.kt" \
  "$HERE/../v2-decoded-envelope/PolarisV2BoundFreshRestoreBridge.kt" \
  "$HERE/host/PolarisDeferredFkTransaction.kt" \
  "$HERE/host/PolarisBackupMangaSqlProjection.kt" \
  "$HERE/host/ProjectionHostBackup.kt" "$HERE/host/ProjectionHostAdapter.kt" \
  "$HERE/host/ProjectionHostJson.kt" "$HERE/host/ProjectionHostStubs.kt" \
  "$HERE/host/SqlDelightHostStubs.kt" "$HERE/host/QueryHostStubs.kt" \
  "$HERE/host/DatabaseHostStub.kt" "$HERE/host/DriverHostStub.kt" \
  "$HERE/host/BoundEnvelopeHostDtos.kt" \
  "$HERE/host/DecoderParent.kt" "$HERE/host/DecodedEnvelope.kt" \
  "$HERE/host/AdapterHostTest.kt" -include-runtime -d "$TMP/adapter-host.jar"
java -jar "$TMP/adapter-host.jar"
