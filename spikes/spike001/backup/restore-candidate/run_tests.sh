#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="$(cd "$HERE/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Compile only host-only DTO stubs and real coordinator; NOT Android or actual ProtoBuf.
kotlinc "$BACKUP/proto-candidate/BackupPolarisBundle.kt" \
  "$BACKUP/parent-candidate/PolarisParentSnapshotPartition.kt" \
  "$BACKUP/proto-candidate/host-tests/BackupStubs.kt" \
  "$BACKUP/proto-candidate/host-tests/SerializationStubs.kt" \
  "$BACKUP/proto-candidate/host-tests/ProtoStubs.kt" \
  "$HERE/PolarisRestoreCoordinator.kt" \
  "$HERE/host-tests/PolarisRestoreCoordinatorTest.kt" \
  -include-runtime -d "$TMP/restore-candidate.jar"
java -cp "$TMP/restore-candidate.jar" polaris.spike001.backup.restore.PolarisRestoreCoordinatorTestKt
