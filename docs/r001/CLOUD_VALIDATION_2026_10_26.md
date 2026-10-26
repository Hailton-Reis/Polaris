# Polaris — cloud validation checkpoint (2026-10-26)

## Evidence status
This checkpoint transcribes results observed in tool outputs during the current session.
The execution environment became unavailable before B01–B05 could be completed.
Raw files were under /workspace/scratch/polaris-cloud-e7d774c; their continued availability has NOT been verified after the interruption. This document does not replace those raw logs or screenshots.
Tested Polaris revision: e7d774c from r001/multisource-foundation. Pinned Yomotsu: 0fb80c439ef816eeb50674f1b90af39918b176d8.

## Verified results
- 216 Python cases PASS: 107 tooling, 37 production-SQL SQLite host, 39 Android helper, 33 Windows-launcher source contracts. These ran on Linux, not native Windows.
- Actual staged Spike-001 Kotlin: 38 host scenarios PASS.
- Domain suites: 21/22 PASS after a local syntax fix in Spike-004. Spike-005 remains failing.
- Backup host gates: 22/23 PASS after a local audit-fixture fix. Candidate backup exporter remains failing.
- Original Yomotsu :app:assembleDebug: PASS in 19m06s.
- Spike-001: SQLDelight interface generation and debug/release migration verification PASS; complete APK build PASS in 7m56s.
- Five APKs per variant: arm64-v8a, armeabi-v7a, x86, x86_64 and universal.
- Baseline and patched each ran 428 unit cases: 394 PASS, 34 FAIL, 0 SKIP. The existing comparator matched test identities and found NO_NEW_UNIT_REGRESSIONS: no new failures, skips or missing baseline tests. This is NOT all-tests-green.
- All ten copied APKs passed sha256sum -c against the generated manifest.
- x86_64 APK signatures verified. Baseline SHA256: 7a00a0da2610f0ec5ee7b3076255bfcce3c9bcc8b998f4cdff12b2909206be31.
- Patched x86_64 SHA256: e4c8cbca2762b1d394477348232225ce0a013a3064f93291a2908076aa7fe644.

## Actual Android observations
Effective cloud quota was 2 CPUs and 8 GiB RAM, without KVM. SDK, NDKs, CMake, JDK21 and Gradle were provisioned.
A dedicated Google APIs API31 x86_64 AVD booted using software CPU/GPU.
First cold boot took about 15 minutes; later boots about 6 minutes.
A01 PASS: original baseline APK installed, real Welcome onboarding rendered, storage /storage/emulated/0/Polaris was selected using Android SAF and granted by its permission dialog, installation/background permissions were configured, onboarding completed and the actual Library screen rendered.
A02: build PASS; patched installation/launch NOT YET VERIFIED.
B01/B02A/B02B/B03/B04: PENDING. B05 novel fixture: NOT RUN.
Never infer reader PASS from APK generation, install, an intent, splash or a debug hook.

## Supplied extension repository
Candidate supplied by user: https://raw.githubusercontent.com/Awerkori/extensoes/repo/index.pb (Project Nox).
The actual pinned Yomotsu protobuf model and mapper decoded the gzip catalog in a host harness (only Android annotation and output DTO stubbed): 1459 extensions, 2418 source entries, 182 Portuguese entries. Legacy JSON differs: 1483 extensions, 184 Portuguese entries.
APIs listed are 1.4/1.6, supported by the pinned loader.
MangaDex 1.6.0 and MangaKatana 1.6.1 APK cryptographic signatures verified and matched the catalog certificate fingerprint:
144f44e865cbfae6bde110489ef7ec142f0b1681f627a093a218650e21db5dad.
Both packages installed in the test Android.
Actual original Yomotsu successfully added Project Nox through its supported mihon://extension-store link and displayed the store. Thus registration/HTTPS/catalog parsing worked inside Android.
Installed extensions were still shown UNTRUSTED. Trust dialog for MangaDex was opened, but the driver session ended as the Trust action was attempted; that action returned ADB 255. Trust completion is NOT established.
No actual chapter read or combined work has been verified.

Cloud HTTPS uses the configured environment proxy CA. Its public CA was imported into the owned Android user certificate store. Original Yomotsu already trusts system AND user certificates; no APK network-security configuration was changed and TLS checks remained enabled.
User CA path: /data/misc/user/0/cacerts-added/d91e660a.0.
A preliminary adb remount requested a reboot and was not used for CA installation.

## Local fixes and remaining failures
Local branch was codex/cloud-validation-2026-10-26 in /workspace/Polaris-cloud-tests.
These local changes are NOT asserted to be pushed or preserved after the environment outage:
1. Spike-004: four regex string lines in CanonicalChapterResolver.kt and ChapterLabelParser.kt used unsupported Kotlin escapes. Converted them to raw triple-quoted regex strings, preserving intended patterns; existing chapter suite passed.
2. Audit test test_plan_legacy_reconciliation.py used optional SQLite UPDATE ... LIMIT syntax. Replaced its UPDATE with selection by _id=(SELECT _id FROM merged WHERE manga_source=11 ORDER BY _id LIMIT 1). All 85 audit cases passed after this fixture-only change. No production SQL/migration changed.

Unresolved:
- SourceHealthTrackerTestMain.kt:35 expects HEALTHY after a challenge then one success. Implementation returns DEGRADED at lifetime success ratio 1/2, while usable. Frozen policy was not changed.
- Candidate Yomotsu backup exporter passes legacy virtual parents in ordinary snapshots; newer BackupPolarisBundle.validateSnapshotCoverage rejects this. Its host suite aborts. Backup v2 remains blocked.

## Interruptions and exact resume
A parallel Gradle/emulator attempt hit cgroup OOM (oom_kill=1), killing QEMU during baseline install. Installation succeeded when retried after all build/test JVMs exited.
A later interactive driver reached its configured 3600-second deadline. It stopped QEMU; shutdown returned -11. No additional OOM was observed then.
Before environment loss, a new session with max-seconds=10800 was launched against the SAME persistent AVD, last observed boot_completed=false at elapsed 113 seconds.
AVD: Polaris_Cloud_API31_20261026.
SDK: /workspace/polaris-cloud-tools/sdk.
ANDROID_AVD_HOME: /workspace/polaris-cloud-tools/avd.
ANDROID_USER_HOME: /workspace/polaris-cloud-tools/android-user.
Build evidence/APKs: /workspace/scratch/polaris-cloud-e7d774c/android-build.
UI captures and action journal: /workspace/scratch/polaris-cloud-e7d774c/ui.
Runtime summary: /workspace/scratch/polaris-cloud-e7d774c/runtime-results.json.
Do not assume these files survived; inspect before recreating anything. Preserve existing user data/worktrees.

1. Recover the environment and inspect files, AVD/process state and raw logs.
2. Resume one emulator without concurrent Gradle. Verify actual current boot and user-unlocked state.
3. Launch baseline; verify saved storage, repository and installed extension state. Complete trust for the two verified Nox packages through the existing UI.
4. Enable Portuguese (Brazil) and English source languages. This preference change was considered but NOT executed before interruption.
5. Populate the same real work from two sources using actual extension networking; do not seed fake manga/chapter records.
6. Install the already-built patched x86_64 APK, verify its installed hash/launch and follow ISSUE002_DEVICE_RUNBOOK.md for real merged list, real child reader A/B and reference removal.
7. Capture actual source IDs, manga/chapter IDs, screenshots, logs and APK hashes before marking B01–B04 PASS.

Fixture candidates, HOST observations only:
MangaDex One Piece UUID a1c7c817-4e59-43b7-9365-09675a149a6f had 62 pt-br internal chapters. Chapter 6674bc28-5a0e-4318-a4b4-1ea48bfe9db1 (62) returned 19 page filenames from at-home metadata; observed image host cmdxd98sb0x3yprd.mangadex.network. English feed sample returned at-home 404; prefer the verified Portuguese candidate.
MangaKatana ordinary search found https://mangakatana.com/manga/one-piece.49.
An API metadata response is not reader proof.
Use the existing source-network-only emulator profile; permit CDN hosts only after actual verified source responses.

Migration 15 was not applied. No PR was promoted or issue closed. R001 is NOT complete; later ranking/matching/translation Android integrations remain outside the current Spike-001 runtime proof.
