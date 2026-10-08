#!/usr/bin/env bash
set -euo pipefail
# Compiles the ACTUAL staged Kotlin domain sources, not a rewritten approximation.
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
compiler=$(command -v kotlinc)
kotlin_home=${KOTLIN_HOME:-$(cd "$(dirname "$(readlink -f "$compiler")")/.." && pwd)}
coroutines="$kotlin_home/lib/kotlinx-coroutines-core-jvm.jar"
test -f "$coroutines" || { echo "Missing Kotlin coroutines JAR in $kotlin_home/lib" >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
kotlinc \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/chapter/interactor/GetMergedChaptersByMangaId.kt" \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/manga/interactor/CreateMergedManga.kt" \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/manga/interactor/DeleteMergedManga.kt" \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/manga/model/MergedMangaReference.kt" \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/source/model/InternalSourceIds.kt" \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/manga/refresh/MergedRefreshTargets.kt" \
  "$root/spikes/spike001/new-files/domain/src/main/java/tachiyomi/domain/manga/refresh/MergedRefreshCoordinator.kt" \
  "$root"/spikes/spike001/host-tests/*.kt \
  -cp "$coroutines" -include-runtime -d "$tmp/invariants.jar"
java -cp "$tmp/invariants.jar:$coroutines" polaris.spike001.host.Spike001HostTestKt
