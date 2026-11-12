#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)";trap 'rm -rf "$TMP"' EXIT
kotlinc "$HERE/PolarisV2SnapshotAdmission.kt" "$HERE/PolarisV2DecodedEnvelopeGateway.kt" \
  "$HERE/host/DecoderDtos.kt" "$HERE/host/DecoderParent.kt" "$HERE/host/DecodedEnvelope.kt" \
  "$HERE/host/GatewayTest.kt" -include-runtime -d "$TMP/gateway.jar"
java -jar "$TMP/gateway.jar" | tee "$TMP/gateway.log"
grep -qx 'POLARIS_V2_DECODED_ENVELOPE_HOST_PASS 22' "$TMP/gateway.log"
