#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="$(cd "$DIR/../.." && pwd)"
PROTO="$BACKUP/proto-candidate/BackupPolarisBundle.kt"
COORD="$BACKUP/restore-candidate/PolarisRestoreCoordinator.kt"
# The standalone evidence ZIP also carries exact copies of these pinned files.
if [[ ! -f "$PROTO" || ! -f "$COORD" ]]; then
  PROTO="$DIR/actual/BackupPolarisBundle.kt"
  COORD="$DIR/actual/PolarisRestoreCoordinator.kt"
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Real portable protobuf DTO and coordinator; host doubles only for Android DB,
# MangaRestorer, BackupManga/chapter and serialization annotation types.
kotlinc "$PROTO" "$COORD" "$DIR"/kotlin/*.kt "$DIR"/tests/*.kt \
    -include-runtime -d "$TMP/run.jar"
java -cp "$TMP/run.jar" polaris.spike001.backup.restore.yomotsu.HostPortTestKt
java -cp "$TMP/run.jar" polaris.spike001.backup.restore.yomotsu.HostSequenceTestKt
