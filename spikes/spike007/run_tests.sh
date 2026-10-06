#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/build"
rm -rf "$OUT"
mkdir -p "$OUT"
kotlinc   $(find "$ROOT/../spike002/src/main/kotlin" -name '*.kt' | sort)   $(find "$ROOT/../spike006/src/main/kotlin" -name '*.kt' | sort)   $(find "$ROOT/src/main/kotlin" -name '*.kt' | sort)   $(find "$ROOT/src/test/kotlin" -name '*.kt' | sort)   -include-runtime -d "$OUT/tests.jar"
java -jar "$OUT/tests.jar"
