# Issue #2 — Work execution log

Date: 2026-10-07. Status: **not passed**. Migration 15 remains unapplied.

## Verified source state

- Read `FINAL_HANDOFF_BEFORE_WORK.md`, `WORK_HANDOFF_PROMPT.md`, the ordered handoff references, Draft PR #1, issues #2–#7 and integration comments on #3/#5/#6.
- Polaris input head: `9380177b57e6511d436d5e47cdb2216410f22e7a`, branch `r001/multisource-foundation`.
- Cloned `kiritsuguxs/yomotsu` and detached at `0fb80c439ef816eeb50674f1b90af39918b176d8`.
- Original Yomotsu checkout remains unmodified. A separate disposable worktree was used for patch preflight only.

## Local preflight

Commands:

```bash
git clone https://github.com/kiritsuguxs/yomotsu.git Yomotsu
git -C Yomotsu checkout --detach 0fb80c439ef816eeb50674f1b90af39918b176d8
git -C Yomotsu worktree add --detach ../Yomotsu-spike001 0fb80c439ef816eeb50674f1b90af39918b176d8
python3 Polaris/spikes/spike001/apply_spike001.py Yomotsu-spike001
git -C Yomotsu-spike001 add -N .
git -C Yomotsu-spike001 diff --check
```

Patch anchors: **PASS against the full pinned upstream tree**. Diff whitespace check: **PASS**. The patch retains real child IDs; `MangaScreen.kt:309–314` routes to `ReaderActivity.newIntent(context, chapter.mangaId, chapter.id)`.

Executed migration 14 against host SQLite 3.53.1 with foreign keys enabled and the baseline `mangas` table (SQLDelight type annotations removed for SQLite execution). Removing one child reference preserved the parent and remaining child. Deleting a real child manga set its reference `manga_id` to null without deleting the virtual parent. `PRAGMA foreign_key_check` returned no violations. These are host SQL checks, **not B01/B02/B03 Android runtime evidence**.

No incompatibility justifying changes to Spikes 001–024 has been demonstrated. No domain policy changes were made.

## Build tooling

Initial `./gradlew :app:assembleDebug --console=plain` stopped before compilation with `java.net.SocketException: Network is unreachable` while fetching Gradle 9.6.1.

Downloaded the exact Gradle distribution and Android command-line tools through the execution environment's HTTP proxy. Java-based downloads require explicit proxy settings; proxy ports are per-command and must be read from that command's environment. An earlier retry with a stale proxy port failed to resolve the Kotlin 2.4.10 plugin and is not evidence that this dependency is unavailable.

The initial host had Java 17, no Android SDK, no adb/emulator and no `/dev/kvm`. Upstream CI requests Java 21; Android compile SDK is 37, target SDK 36, NDK 29.0.14206865, with dbnet-native overriding NDK to 28.2.13676358 and CMake 3.22.1.

## Reproducible build gate

Added `scripts/r001/build_issue002.sh` and `.github/workflows/issue002-android-build.yml`:

1. Require the exact clean baseline commit.
2. Build its debug APK before applying any Polaris patch.
3. Create a separate worktree and apply only Spike-001, including migration 14.
4. Capture a complete diff, generate SQLDelight, verify migrations, build the patched debug APK and run Android unit-test tasks.
5. Save logs and APKs as workflow artifacts, including failure logs.

Shell syntax and workflow YAML parsing passed locally. Workflow/build execution results must be inspected before treating this gate as green. `BUILD_GATE_PASS` is deliberately distinct from Android runtime PASS.

## Still required

- Successful original and patched builds and SQLDelight generation.
- A launched baseline APK (A01).
- Two installed compatible real source extensions and populated child manga chapters.
- A debug/instrumentation creation hook calling `CreateMergedManga` after compilation succeeds.
- Runtime B01/B02/B03 with actual child/source IDs, sources, APK/device versions, logs and screenshots.

The PR must remain draft and issue #2 must remain open. Issues #3/#5/#4/#6/#7 cannot be reported as integrated while this gate is pending.
