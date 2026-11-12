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
java -jar "$TMP/bridge.jar" 103 > "$TMP/projection.json"
java -jar "$TMP/bridge.jar" 203 > "$TMP/projection-203.json"
export POLARIS_TYPED_PROJECTION_FIXTURE="$TMP/projection.json"
export POLARIS_TYPED_PROJECTION_FIXTURE_203="$TMP/projection-203.json"
export POLARIS_KOTLIN_BRIDGE_JAR="$TMP/bridge.jar"
python3 -m unittest discover -s "$HERE" -p 'test_*.py' -v
