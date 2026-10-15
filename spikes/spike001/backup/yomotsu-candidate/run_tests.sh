#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP="$ROOT/spike001/backup"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Host-only pinned Yomotsu API-shaped contracts, not Android or real Kotlin ProtoBuf.
# Compile the actual staged DTO, planners, UUID store and candidate exporter.
# The eight explicit stubs are NEVER part of production builds.
kotlinc \
  "$BACKUP/MergedBackupRestorePlanner.kt" \
  "$BACKUP/MergedBackupExportPlanner.kt" \
  "$BACKUP/proto-candidate/BackupPolarisBundle.kt" \
  "$BACKUP/proto-candidate/BackupPolarisBundleBuilder.kt" \
  "$BACKUP/uuid-candidate/YomotsuMergedWorkUuidStore.kt" \
  "$BACKUP/yomotsu-candidate/PolarisYomotsuBackupExporter.kt" \
  "$BACKUP/yomotsu-candidate/host-tests/"*.kt \
  -include-runtime -d "$TMP/polaris-yomotsu-export-host.jar"
java -cp "$TMP/polaris-yomotsu-export-host.jar" \
  polaris.spike001.backup.yomotsu.YomotsuBackupExporterTestKt
