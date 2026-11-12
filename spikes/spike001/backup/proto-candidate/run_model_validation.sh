#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Lightweight host Kotlin syntax/validation gate only; annotations and
# BackupManga are test doubles. This is NOT real kotlinx.protobuf serialization.
kotlinc "$HERE/BackupPolarisBundle.kt" \
  "$HERE/../parent-candidate/PolarisParentSnapshotPartition.kt" \
  "$HERE/../parent-candidate/PolarisParentBundleAssembler.kt" \
  "$HERE/../restore-candidate/PolarisRestoreCoordinator.kt" \
  "$HERE/../restore-candidate/android-bridge/Backup.staged.kt" \
  "$HERE/BackupPolarisBundleBuilder.kt" \
  "$HERE/../MergedBackupRestorePlanner.kt" \
  "$HERE/../MergedBackupExportPlanner.kt" \
  "$HERE/host-tests/BackupStubs.kt" \
  "$HERE/host-tests/SerializationStubs.kt" \
  "$HERE/host-tests/ProtoStubs.kt" \
  "$HERE/host-tests/BackupPolarisBundleContractTest.kt" \
  "$HERE/../parent-candidate/ParentBundleV2Test.kt" \
  "$HERE/host-tests/BackupPolarisPendingSnapshotTest.kt" \
  "$HERE/host-tests/BackupPolarisInteropTest.kt" \
  "$HERE/host-tests/BackupPolarisBundleBuilderTest.kt" \
  -include-runtime -d "$TMP/contract.jar"
java -cp "$TMP/contract.jar" eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundleContractTestKt
java -cp "$TMP/contract.jar" polaris.spike001.backup.BackupPolarisBundleBuilderTestKt
java -cp "$TMP/contract.jar" eu.kanade.tachiyomi.data.backup.models.BackupPolarisPendingSnapshotTestKt
java -cp "$TMP/contract.jar" eu.kanade.tachiyomi.data.backup.models.BackupPolarisInteropTestKt
java -cp "$TMP/contract.jar" polaris.spike001.backup.parent.ParentBundleV2TestKt
