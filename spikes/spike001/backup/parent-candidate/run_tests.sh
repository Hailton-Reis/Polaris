#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP="$(mktemp -d)"; trap 'rm -rf "$TEMP"' EXIT
kotlinc "$DIR/PolarisParentSnapshotPartition.kt" "$DIR/ParentHostStubs.kt" "$DIR/SerializationStubs.kt" "$DIR/ProtoNumberStubs.kt" "$DIR/ParentPartitionTest.kt" -include-runtime -d "$TEMP/split.jar"
java -jar "$TEMP/split.jar"
