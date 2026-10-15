#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Compiles exact Kotlin adapter source with HOST-ONLY faux SQLDelight types.
# Does NOT execute generated SQLDelight or Yomotsu Android dependencies.
kotlinc "$DIR"/kotlin-candidate/*.kt "$DIR"/tests/*.kt -include-runtime -d "$TMP/port.jar"
java -cp "$TMP/port.jar" polaris.spike001.backup.restore.sqldelight.SqlDelightPolarisAtomicPortTestKt
