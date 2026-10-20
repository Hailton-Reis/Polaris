#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ="$HERE/../parent-field-projection"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
kotlinc \
  "$PROJ/PolarisBackupMangaSqlProjection.kt" \
  "$PROJ/ProjectionHostBackup.kt" "$PROJ/ProjectionHostAdapter.kt" \
  "$PROJ/ProjectionHostJson.kt" "$PROJ/ProjectionHostStubs.kt" \
  "$HERE/ProjectionSqlBridgeFixture.kt" \
  -include-runtime -d "$TMP/bridge.jar"
java -jar "$TMP/bridge.jar" > "$TMP/projection.json"
export POLARIS_TYPED_PROJECTION_FIXTURE="$TMP/projection.json"
python3 -m unittest discover -s "$HERE" -p 'test_*.py' -v
