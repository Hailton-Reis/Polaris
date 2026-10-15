#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Test the real UUID store source against host-only Yomotsu API and JSON stubs.
# NOT the Android repository, Android Gradle or real kotlinx.serialization JSON.
kotlinc "$HERE/YomotsuMergedWorkUuidStore.kt" \
  "$HERE/host-tests/JsonStubs.kt" \
  "$HERE/host-tests/MangaStub.kt" \
  "$HERE/host-tests/RepositoryStub.kt" \
  "$HERE/host-tests/YomotsuMergedWorkUuidStoreTest.kt" \
  -include-runtime -d "$TMP/merge-uuid-host.jar"
java -cp "$TMP/merge-uuid-host.jar" polaris.spike001.backup.uuid.YomotsuMergedWorkUuidStoreTestKt
