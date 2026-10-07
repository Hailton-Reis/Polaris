# Issue #2 — Work execution log

Date: 2026-10-07. Status: **baseline and Spike-001 builds passed; issue #2 runtime not passed**. Migration 15 remains unapplied.

## Verified source state

- Read `FINAL_HANDOFF_BEFORE_WORK.md`, `WORK_HANDOFF_PROMPT.md`, the ordered handoff references, Draft PR #1, issues #2–#7 and integration comments on #3/#5/#6.
- Polaris input head: `9380177b57e6511d436d5e47cdb2216410f22e7a`, branch `r001/multisource-foundation`.
- Cloned `kiritsuguxs/yomotsu` and detached at `0fb80c439ef816eeb50674f1b90af39918b176d8`.
- Original Yomotsu tracked source remains unmodified. A separate worktree was used for Spike-001 preflight and the actual patched Android build; both trees received the upstream generated branding assets.

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

Added `scripts/r001/build_issue002.sh`, `scripts/r001/check_issue002_sql.py` and `.github/workflows/issue002-android-build.yml`:

1. Require the exact clean baseline commit.
2. Build its debug APK before applying any Polaris patch.
3. Create a separate worktree and apply only Spike-001, including migration 14.
4. Capture a complete diff, generate SQLDelight, verify migrations, build the patched debug APK and run Android unit-test tasks.
5. Save logs and APKs as workflow artifacts, including failure logs.

Shell syntax and workflow YAML parsing passed locally. Workflow/build execution results must be inspected before treating this gate as green. `BUILD_GATE_PASS` is deliberately distinct from Android runtime PASS.

The SQL preflight is reproducible with:

```bash
python3 scripts/r001/check_issue002_sql.py /path/to/pinned-yomotsu
```

## Further local recovery and CI evidence

- Prepared Temurin JDK 21.0.12.1+1 with `javac`, Android platform 37.0, build tools 36.0.0/37.0.0, platform tools, both pinned NDKs and CMake 3.22.1.
- A proxy-aware Gradle retry using the original Java 17 runtime reached configuration but failed because that runtime lacked `JAVA_COMPILER`.
- The full JDK21 retry reached `:build-logic:compileKotlin` but initially lacked the environment CA certificates. Using the system trust store (`-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts`) resolved that TLS problem without disabling certificate validation.
- Build logic then compiled. One retry encountered incomplete NDK installation (`CXX1101`, missing `source.properties`); installation subsequently finished and the build was restarted with both NDKs verified.
- `adb devices` reports no connected devices. `/dev/kvm` is unavailable.
- Commit `ca6869339630eaed50381fa5dee94a296366d435` published the first CI gate. Runs [37649303100](https://github.com/Hailton-Reis/Polaris/actions/runs/37649303100) and [37649299513](https://github.com/Hailton-Reis/Polaris/actions/runs/37649299513) failed before executing any job steps (`steps: []`). This is **not an Android compilation result**. The existing Domain spikes job also failed before steps. The API exposed no runner failure reason; do not infer billing, dependency or application failures from this.
- Diagnostic logs/excerpts are under `docs/r001/evidence/issue002-2026-10-07/`. Repeated stack traces are explicitly omitted in the larger excerpts.
- The original baseline generated SQLDelight interfaces and compiled the domain/data/app Kotlin modules, but resource linking then failed: `mipmap/ic_launcher_foreground` was missing. The pinned upstream CI explicitly generates these PNG assets from `branding/yomotsu-icon.png.b64`; the build script now performs that same preparation for both trees. This changes generated resource inputs, not upstream application code or Spike policies.
- A subsequent incremental retry reported duplicate declarations of existing inline properties/functions in `BuildConfig.kt` and `FileExtensions.kt`. Source inspection found one declaration of each. A clean, non-incremental baseline build was started to distinguish stale compilation state from a real source problem. Do not treat this as a Polaris incompatibility.
- The clean non-incremental build eliminated those duplicate-declaration errors and reached APK packaging. One ARM64 intermediate resource ZIP was truncated (8,936,405 bytes, no EOCD); the other four ABI resource ZIPs were valid (14,726,382 bytes). Removing only the corrupt generated intermediate and rebuilding with cache disabled regenerated it successfully.
- **Original baseline build: PASS**, `BUILD SUCCESSFUL in 1m 51s`. Command used the exact Gradle 9.6.1 distribution, prepared upstream branding, JDK21/system trust store/SDK, `-Pkotlin.incremental=false`, `--no-build-cache`, `--max-workers=1` and a 3 GiB Gradle heap. `git diff --exit-code` confirms no tracked upstream code changes.
- Baseline ARM64 APK signature verified (v2, one signer). SHA-256: `6f1ebd8e444097307ff9f44efd32d2fcd8c51f34379b9b71ee24100a749cffc2`.
- Added a debug-only creation/removal activity under `integration/r001/debug/`, installed through `scripts/r001/apply_debug_hook.py`. It calls the existing Spike-001 interactors and temporarily selects the existing no-dedupe mode for the test work, so both child lists are visible. No Spike source or domain policy was changed. Device commands and evidence requirements are in `ISSUE002_DEVICE_RUNBOOK.md`.
- Started the real patched gate: `:data:generateDebugDatabaseInterface verifySqlDelightMigration :app:assembleDebug` with the same recovered toolchain/non-incremental settings.
- The patched domain/data/app and debug hook compiled against the real Android APIs. The first full patched attempt reached packaging and produced a signed ARM64 APK, but failed on a truncated x86 intermediate ZIP (8,936,458 bytes versus 14,726,434 bytes for valid sibling ZIPs). A targeted regeneration was started, as for the baseline. This is not evidence of a domain/API incompatibility, and no domain redesign was made.
- The migration verifier completed for both debug and release (`verifyDebugDatabaseMigration`, `verifyReleaseDatabaseMigration`). Regenerated resource ZIPs were all valid and byte-identical (SHA-256 `1a42153988cc61dad149ae22ff7ea8fe2c3e6c049c3d1f6424e9513e8870dd6b`). The packaging retry then hit stale APK metadata (`app-metadata.properties` already present). Preserved the generated debug APK outputs and `app/build/intermediates/incremental/packageDebug` in a temporary diagnostic directory and restarted the gate, keeping all sources/resources intact. No upstream code or Spike policy was altered for this recovery.

- **Spike-001 build: PASS**, `BUILD SUCCESSFUL in 1m 41s`, including SQLDelight generation and debug/release migration verification. The original Spike-001 and debug-only adapter compile against the pinned Yomotsu/Android APIs. No migration 15 or redesign of Spikes 001–024 was applied.
- Final patched ARM64 APK signature verified (v2, one signer). SHA-256: `87bb88a1a676caa78fafc3c022ac45a30b8bcc65673c7e4352f3942ec3d21666`.
- Successful build logs and the complete applied source diff are committed under `evidence/issue002-2026-10-07/`.

- First unit-test run: 45 domain tests passed; 13 failed during MockK initialization because Byte Buddy could not self-attach to the test JVM. Data/app tasks did not run after domain failure. This run is not a green unit gate. A retry preloads the cached Byte Buddy agent through a temporary Gradle init script, without changing project sources.

- Agent-preloaded retry: **domain 58/58 PASS**, data `testDebugUnitTest` has no test sources, app **336/370 PASS; 34 failures**. Failures include upstream novel speech expectations, translation detection expectations/mocks, Android JSONObject stubs and missing NetworkHelper test DI. They do not directly exercise merged-work code; the original pinned baseline reproduces the same 34 failing test cases out of 370 with the identical agent-preloaded setup (comparison JSON committed). No additional failing cases were introduced by Spike-001 in this run. The complete unit gate is **not green**. Summaries/excerpts preserve diagnostics without megabyte bitmap array dumps.

## Emulator continuation

The user requested software emulation. A pinned baseline x86_64 APK installed and launched into the onboarding UI on Android 12/API31 without Polaris changes. A01 is **PASS for this emulator configuration**. Both real extension APKs installed; trusting them and fetching real child manga/chapters remain pending. B01/B02/B03 are not passed. Details, environment limitations and screenshots are in `ISSUE002_EMULATOR_RUN.md`.

## Still required

- A01 now passed on the software API31/x86_64 emulator; see `ISSUE002_EMULATOR_RUN.md` and its raw evidence. ARM64 reader/native translation remains unverified.
- Two installed compatible real source extensions and populated child manga chapters.
- Run the compiled debug creation/removal hook on the actual device.
- Runtime B01/B02/B03 with actual child/source IDs, sources, APK/device versions, logs and screenshots.

The PR must remain draft and issue #2 must remain open. Issues #3/#5/#4/#6/#7 cannot be reported as integrated while this gate is pending.
