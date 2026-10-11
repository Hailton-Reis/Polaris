#!/usr/bin/env bash
set -euo pipefail

# Isolated JVM-only evidence for #11; not an Android/SQLDelight acceptance gate.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

kotlinc "$DIR/MergedBackupRestorePlanner.kt" "$DIR/MergedBackupRestorePlannerTest.kt" -include-runtime -d "$TEMP/merged-backup-tests.jar"
java -jar "$TEMP/merged-backup-tests.jar"
