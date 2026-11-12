#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO="$HERE/../proto-candidate"
RESTORE="$HERE/../restore-candidate"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
# Deliberately host-only; these DTO/annotation doubles are NOT real ProtoBuf.
kotlinc \
  "$PROTO/BackupPolarisBundle.kt" \
  "$HERE/PolarisParentSnapshotPartition.kt" \
  "$HERE/PolarisParentMetadataRestorePlan.kt" \
  "$PROTO/host-tests/BackupStubs.kt" \
  "$PROTO/host-tests/SerializationStubs.kt" \
  "$PROTO/host-tests/ProtoStubs.kt" \
  "$HERE/ParentRestorePlanTest.kt" \
  -include-runtime -d "$TMP/restore-plan.jar"
java -cp "$TMP/restore-plan.jar" polaris.spike001.backup.parent.ParentRestorePlanTestKt