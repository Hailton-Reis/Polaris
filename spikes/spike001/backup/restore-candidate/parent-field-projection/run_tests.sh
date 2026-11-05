#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
kotlinc "$root/PolarisBackupMangaSqlProjection.kt" "$root/ProjectionTest.kt" "$root/ProjectionHostBackup.kt" "$root/ProjectionHostAdapter.kt" "$root/ProjectionHostJson.kt" "$root/ProjectionHostStubs.kt" -include-runtime -d "$work/test.jar"
java -jar "$work/test.jar"
