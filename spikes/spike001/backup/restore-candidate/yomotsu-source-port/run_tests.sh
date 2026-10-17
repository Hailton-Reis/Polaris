#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
kotlinc "$DIR"/actual/*.kt "$DIR"/kotlin/*.kt "$DIR"/tests/*.kt -include-runtime -d "$TMP/run.jar"
java -cp "$TMP/run.jar" polaris.spike001.backup.restore.yomotsu.HostPortTestKt
java -cp "$TMP/run.jar" polaris.spike001.backup.restore.yomotsu.HostSequenceTestKt
