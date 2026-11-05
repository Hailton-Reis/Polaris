#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
A="$HERE/../generated-adapter"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
kotlinc "$A/SqlDelightPolarisFreshParentAdapter.kt" \
  "$HERE/PolarisV2BoundFreshRestoreBridge.kt" \
  "$HERE/PolarisV2SnapshotAdmission.kt" "$HERE/PolarisV2DecodedEnvelopeGateway.kt" \
  "$A/host/PolarisDeferredFkTransaction.kt" "$A/host/PolarisBackupMangaSqlProjection.kt" \
  "$A/host/ProjectionHostBackup.kt" "$A/host/ProjectionHostAdapter.kt" \
  "$A/host/ProjectionHostJson.kt" "$A/host/ProjectionHostStubs.kt" \
  "$A/host/SqlDelightHostStubs.kt" "$A/host/QueryHostStubs.kt" \
  "$A/host/DatabaseHostStub.kt" "$A/host/DriverHostStub.kt" \
  "$A/host/BoundEnvelopeHostDtos.kt" "$A/host/DecoderParent.kt" "$A/host/DecodedEnvelope.kt" \
  "$HERE/host/BoundAdapterHostTest.kt" -include-runtime -d "$TMP/bound.jar"
java -jar "$TMP/bound.jar" | tee "$TMP/tests.log"
test "$(grep -cx 'POLARIS_V2_BOUND_RESTORE_BRIDGE_PASS 26' "$TMP/tests.log")" = 1
