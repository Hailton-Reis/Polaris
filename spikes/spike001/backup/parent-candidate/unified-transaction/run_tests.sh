#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="$HERE/../.."
PROTO="$BACKUP/proto-candidate"
PARENT="$BACKUP/parent-candidate"
RESTORE="$BACKUP/restore-candidate"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Compile ACTUAL staged Kotlin DTO and coordinator with host-only BackupManga,
# serialization annotation doubles. This is NOT Android or SQLDelight.
kotlinc \
  "$PROTO/BackupPolarisBundle.kt" \
  "$PARENT/PolarisParentSnapshotPartition.kt" \
  "$PARENT/PolarisParentMetadataRestorePlan.kt" \
  "$RESTORE/PolarisRestoreCoordinator.kt" \
  "$PROTO/host-tests/BackupStubs.kt" \
  "$PROTO/host-tests/SerializationStubs.kt" \
  "$PROTO/host-tests/ProtoStubs.kt" \
  "$HERE/PolarisFullParentTransactionCoordinator.kt" \
  "$HERE/PolarisFullParentTransactionCoordinatorTest.kt" \
  -include-runtime -d "$TMP/full-parent-tx.jar"
java -cp "$TMP/full-parent-tx.jar" polaris.spike001.backup.parent.PolarisFullParentTransactionCoordinatorTestKt