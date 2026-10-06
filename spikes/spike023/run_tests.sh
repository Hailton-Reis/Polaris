#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/build"
kotlinc $(find "$ROOT/src/main/kotlin" "$ROOT/src/test/kotlin" -name '*.kt' | sort) -include-runtime -d "$ROOT/build/tests.jar"
java -jar "$ROOT/build/tests.jar"
