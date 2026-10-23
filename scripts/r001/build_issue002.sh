#!/usr/bin/env bash
set -euo pipefail

# Build the original pinned tree first; never apply migration 15 here.
polaris_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
# The pinned Yomotsu checkout must remain byte-for-byte clean across builds.
# Both build variants are disposable, uniquely named worktrees in the evidence directory.
baseline_source=$(realpath "${1:?Usage: build_issue002.sh BASELINE_CHECKOUT EVIDENCE_DIR}")
evidence=$(realpath -m "${2:?Missing evidence directory}")
pinned=0fb80c439ef816eeb50674f1b90af39918b176d8
test "$(git -C "$baseline_source" rev-parse HEAD)" = "$pinned"
test -z "$(git -C "$baseline_source" status --porcelain)"
test ! -e "$evidence"
mkdir -p "$evidence"
baseline="$evidence/baseline-yomotsu"
patched="$evidence/patched-yomotsu"
test ! -e "$baseline"
test ! -e "$patched"
git -C "$baseline_source" worktree add --detach "$baseline" "$pinned"
test "$(git -C "$baseline" rev-parse HEAD)" = "$pinned"

{
    git -C "$baseline" rev-parse HEAD
    java -version
    printf 'Android SDK: %s\n' "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-unset}}"
} > "$evidence/environment.txt" 2>&1
python3 "$polaris_root/scripts/r001/check_issue002_sql.py" "$baseline" | tee "$evidence/sql-preflight.log"
python3 -m unittest discover -s "$polaris_root/spikes/spike001/host-sqlite" -p 'test_*.py' -v 2>&1 | tee "$evidence/sqlite-contract-tests.log"
python3 "$polaris_root/scripts/r001/check_spike001_refresh_patch.py" "$baseline" --mode baseline | tee "$evidence/vm-refresh-baseline-preflight.log"
python3 "$polaris_root/scripts/r001/check_spike001_background_patch.py" "$baseline" --mode baseline | tee "$evidence/background-update-baseline-preflight.log"

run_gradle() {
    local tree=$1 log=$2
    shift 2
    (cd "$tree" && ./gradlew "$@" -Pkotlin.incremental=false --no-build-cache --no-daemon --console=plain --stacktrace \
        --max-workers=1 '-Dorg.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=1g -Dfile.encoding=UTF-8') 2>&1 | tee "$evidence/$log"
}

# Match the pinned upstream build workflow's required generated branding assets.
prepare_branding() {
    local tree=$1 density
    base64 --decode "$tree/branding/yomotsu-icon.png.b64" > "$evidence/yomotsu-icon.png"
    for density in mdpi hdpi xhdpi xxhdpi xxxhdpi; do
        mkdir -p "$tree/app/src/main/res/mipmap-$density"
        cp "$evidence/yomotsu-icon.png" "$tree/app/src/main/res/mipmap-$density/ic_launcher.png"
        cp "$evidence/yomotsu-icon.png" "$tree/app/src/main/res/mipmap-$density/ic_launcher_foreground.png"
    done
}

# Branding changes are confined to an evidence worktree, never the pinned checkout.
prepare_branding "$baseline"
test -z "$(git -C "$baseline_source" status --porcelain)"
run_gradle "$baseline" baseline-build.log :app:assembleDebug
# Compare unmodified-upstream tests with patched tests; upstream failures are
# not a Polaris regression, but newly failing, skipped or missing tests are.
# --continue lets unrelated module tasks produce their JUnit reports.
unit_test_tasks=(:domain:testDebugUnitTest :data:testDebugUnitTest :app:testDebugUnitTest)
baseline_test_exit=0
run_gradle "$baseline" baseline-unit-tests.log --continue "${unit_test_tasks[@]}" || baseline_test_exit=$?
mkdir -p "$evidence/apks/baseline"
cp "$baseline"/app/build/outputs/apk/debug/*.apk "$evidence/apks/baseline/"
git -C "$baseline_source" worktree add --detach "$patched" "$pinned"
python3 "$polaris_root/spikes/spike001/apply_spike001.py" "$patched" 2>&1 | tee "$evidence/apply-spike001.log"
python3 "$polaris_root/scripts/r001/check_spike001_refresh_patch.py" "$patched" --mode patched | tee "$evidence/vm-refresh-patched-preflight.log"
python3 "$polaris_root/scripts/r001/check_spike001_background_patch.py" "$patched" --mode patched | tee "$evidence/background-update-patched-preflight.log"
python3 "$polaris_root/scripts/r001/check_spike001_full_apply.py" "$baseline" "$patched" | tee "$evidence/full-apply-contract.log"
python3 "$polaris_root/scripts/r001/apply_debug_hook.py" "$patched" | tee "$evidence/apply-debug-hook.log"
# Intent-to-add includes all staged new files in the reviewable diff.
git -C "$patched" add -N .
git -C "$patched" diff --binary > "$evidence/spike001.patch"
git -C "$patched" diff --check 2>&1 | tee "$evidence/diff-check.log"
test ! -e "$patched/data/src/main/sqldelight/tachiyomi/migrations/15.sqm"
prepare_branding "$patched"
run_gradle "$patched" patched-build.log :data:generateDebugDatabaseInterface verifySqlDelightMigration :app:assembleDebug
mkdir -p "$evidence/apks/spike001"
cp "$patched"/app/build/outputs/apk/debug/*.apk "$evidence/apks/spike001/"
patched_test_exit=0
run_gradle "$patched" patched-unit-tests.log --continue "${unit_test_tasks[@]}" || patched_test_exit=$?
python3 "$polaris_root/scripts/r001/compare_android_unit_tests.py" "$baseline" "$patched" \
    --baseline-exit "$baseline_test_exit" --patched-exit "$patched_test_exit" \
    --baseline-log "$evidence/baseline-unit-tests.log" \
    --patched-log "$evidence/patched-unit-tests.log" \
    --min-module domain=58 --min-module app=370 \
    --output "$evidence/unit-test-comparison.json" | tee "$evidence/unit-test-comparison.log"
printf 'APK_BUILDS_PASS_NO_NEW_UNIT_REGRESSIONS\nExisting upstream unit failures may remain; see comparison JSON.\nRuntime A01/B01/B02/B03 still require device evidence.\n' | tee "$evidence/build-status.txt"
