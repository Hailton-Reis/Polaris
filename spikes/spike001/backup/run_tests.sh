#!/usr/bin/env bash
set -euo pipefail

# Isolated JVM-only evidence for #11; not an Android/SQLDelight acceptance gate.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

kotlinc "$DIR/MergedBackupRestorePlanner.kt" "$DIR/MergedBackupRestorePlannerTest.kt" \
  "$DIR/MergedBackupExportPlanner.kt" "$DIR/MergedBackupExportPlannerTest.kt" \
  -include-runtime -d "$TEMP/merged-backup-tests.jar"
java -cp "$TEMP/merged-backup-tests.jar" polaris.spike001.backup.MergedBackupRestorePlannerTestKt
java -cp "$TEMP/merged-backup-tests.jar" polaris.spike001.backup.MergedBackupExportPlannerTestKt
# Verify durable parent identities separately using pinned Yomotsu API-shaped stubs.
bash "$DIR/uuid-candidate/run_uuid_host.sh"
