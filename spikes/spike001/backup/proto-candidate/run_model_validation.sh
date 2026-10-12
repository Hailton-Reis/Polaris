#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Lightweight host Kotlin syntax/validation gate only; annotations and
# BackupManga are test doubles. This is NOT real kotlinx.protobuf serialization.
kotlinc "$HERE/BackupPolarisBundle.kt" \
  "$HERE/host-tests/BackupStubs.kt" \
  "$HERE/host-tests/SerializationStubs.kt" \
  "$HERE/host-tests/ProtoStubs.kt" \
  "$HERE/host-tests/BackupPolarisBundleContractTest.kt" \
  -include-runtime -d "$TMP/contract.jar"
java -cp "$TMP/contract.jar" eu.kanade.tachiyomi.data.backup.models.BackupPolarisBundleContractTestKt
