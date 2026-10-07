#!/usr/bin/env bash
set -euo pipefail

# Build the original pinned tree first; never apply migration 15 here.
polaris_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
baseline=$(realpath "${1:?Usage: build_issue002.sh BASELINE_CHECKOUT EVIDENCE_DIR}")
evidence=$(realpath -m "${2:?Missing evidence directory}")
pinned=0fb80c439ef816eeb50674f1b90af39918b176d8
mkdir -p "$evidence"
test "$(git -C "$baseline" rev-parse HEAD)" = "$pinned"
test -z "$(git -C "$baseline" status --porcelain)"
patched="$evidence/patched-yomotsu"
test ! -e "$patched"

{
    git -C "$baseline" rev-parse HEAD
    java -version
    printf 'Android SDK: %s\n' "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-unset}}"
} > "$evidence/environment.txt" 2>&1

run_gradle() {
    local tree=$1 log=$2
    shift 2
    (cd "$tree" && ./gradlew "$@" --no-daemon --console=plain --stacktrace) 2>&1 | tee "$evidence/$log"
}

run_gradle "$baseline" baseline-build.log :app:assembleDebug
git -C "$baseline" worktree add --detach "$patched" "$pinned"
python3 "$polaris_root/spikes/spike001/apply_spike001.py" "$patched" 2>&1 | tee "$evidence/apply-spike001.log"
# Intent-to-add includes all staged new files in the reviewable diff.
git -C "$patched" add -N .
git -C "$patched" diff --binary > "$evidence/spike001.patch"
git -C "$patched" diff --check 2>&1 | tee "$evidence/diff-check.log"
test ! -e "$patched/data/src/main/sqldelight/tachiyomi/migrations/15.sqm"
run_gradle "$patched" patched-build.log :data:generateDebugDatabaseInterface verifySqlDelightMigration :app:assembleDebug
run_gradle "$patched" patched-unit-tests.log :domain:testDebugUnitTest :data:testDebugUnitTest :app:testDebugUnitTest
mkdir -p "$evidence/apks/baseline" "$evidence/apks/spike001"
cp "$baseline"/app/build/outputs/apk/debug/*.apk "$evidence/apks/baseline/"
cp "$patched"/app/build/outputs/apk/debug/*.apk "$evidence/apks/spike001/"
printf 'BUILD_GATE_PASS\nRuntime A01/B01/B02/B03 still require device evidence.\n' | tee "$evidence/build-status.txt"
