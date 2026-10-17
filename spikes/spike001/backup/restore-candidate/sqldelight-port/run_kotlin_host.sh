#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="$(cd "$DIR/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Compile the actual committed portable protobuf data-model and real
# PolarisRestoreCoordinator.kt, NOT tests/HostModel.kt.
# Only the Android SQLDelight database, serializer annotations and BackupManga
# are host stubs; codegen/ProtoBuf runtime remains a separate Android gate.
kotlinc \
  "$BACKUP/proto-candidate/host-tests/BackupStubs.kt" \
  "$BACKUP/proto-candidate/host-tests/SerializationStubs.kt" \
  "$BACKUP/proto-candidate/host-tests/ProtoStubs.kt" \
  "$BACKUP/proto-candidate/BackupPolarisBundle.kt" \
  "$BACKUP/restore-candidate/PolarisRestoreCoordinator.kt" \
  "$DIR/kotlin-candidate/PolarisRestoreDigest.kt" \
  "$DIR/kotlin-candidate/SqlDelightPolarisAtomicVirtualWorkPort.kt" \
  "$DIR/tests/HostAsync.kt" \
  "$DIR/tests/HostDatabase.kt" \
  "$DIR/tests/HostJson.kt" \
  "$DIR/tests/SqlDelightPolarisAtomicPortTest.kt" \
  "$DIR/tests/RealModelIntegrationTest.kt" \
  -include-runtime -d "$TMP/real-port-integration.jar"
java -cp "$TMP/real-port-integration.jar" \
  polaris.spike001.backup.restore.sqldelight.SqlDelightPolarisAtomicPortTestKt
java -cp "$TMP/real-port-integration.jar" \
  polaris.spike001.backup.restore.sqldelight.RealModelIntegrationTestKt
