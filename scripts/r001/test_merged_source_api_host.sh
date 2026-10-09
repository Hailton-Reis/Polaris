#!/usr/bin/env bash
set -euo pipefail
# Compile production Polaris MergedSource with the exact pinned Yomotsu Source
# interface. No Android SDK, device, Gradle, or network is needed.
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
upstream=$(realpath "${1:?Usage: bash scripts/r001/test_merged_source_api_host.sh /path/to/pinned-yomotsu}")
pinned=0fb80c439ef816eeb50674f1b90af39918b176d8
test "$(git -C "$upstream" rev-parse HEAD)" = "$pinned" || {
  echo "Source API test requires pinned Yomotsu $pinned" >&2
  exit 2
}
source_api="$upstream/source-api/src/main/kotlin/eu/kanade/tachiyomi/source/Source.kt"
merged="$root/spikes/spike001/new-files/app/src/main/java/eu/kanade/tachiyomi/source/MergedSource.kt"
virtual_id="$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/source/model/InternalSourceIds.kt"
test -f "$source_api" && test -f "$merged" && test -f "$virtual_id"
compiler=$(command -v kotlinc)
kotlin_home=${KOTLIN_HOME:-$(cd "$(dirname "$(readlink -f "$compiler")")/.." && pwd)}
coroutines="$kotlin_home/lib/kotlinx-coroutines-core-jvm.jar"
test -f "$coroutines" || { echo "Missing Kotlin coroutines JAR in $kotlin_home/lib" >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
kotlinc "$source_api" "$merged" "$virtual_id" \
  "$root/spikes/spike001/host-source-api/SourceModelStubs.kt" \
  "$root/spikes/spike001/host-source-api/RxStub.kt" \
  "$root/spikes/spike001/host-source-api/MergedSourceHostTest.kt" \
  -cp "$coroutines" -include-runtime -d "$tmp/merged-source-api.jar"
java -cp "$tmp/merged-source-api.jar:$coroutines" polaris.spike001.source.host.MergedSourceHostTestKt
