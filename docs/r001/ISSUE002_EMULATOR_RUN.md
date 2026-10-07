# Issue #2 — software emulator execution

Date: 2026-10-07. Current gate: **A01 PASS (API31/x86_64); B01/B02/B03 pending**.

## What actually ran

- Android Emulator 37.2.12 (build 16428233), software CPU (`-accel off`), software graphics, headless 480×800, 2 GiB guest RAM. Host has no `/dev/kvm`.
- First image: Google APIs Android 11/API30/x86_64. Its system-server watchdog killed Android during baseline installation (`Broken pipe`); this occurred before Yomotsu could open. The app was not established as the cause.
- Second image: Google APIs Android 12/API31/x86_64, with advertised ARM64 native-bridge support. Applied `ro.hw_timeout_multiplier=10` through rooted ADB and restarted Android services. The emulator's non-qemu `-prop` option was ignored; the run verifies the actual value through `getprop`.
- Google Play Services, Photos, Contacts Sync and Maps were disabled **in this disposable test image** to reduce unrelated background work. These are test conditions; no translation/ML Kit acceptance is claimed.
- Added the execution environment's public CA certificates to the guest user CA store. Yomotsu's existing network security configuration already trusts user certificates. Configured Android's explicit HTTP proxy through the emulator gateway because guest UDP DNS was unavailable. The host proxy port is session-specific and must be refreshed after restart.
- ARM64 streamed install exceeded the 420-second host timeout. The immediate package query was empty. Later x86 replacement logs indicate a previous app code path existed, consistent with a late completion of the earlier install; **no successful ARM64 UI launch was recorded**.
- x86_64 baseline: compressed ADB push followed by local `pm install --abi x86_64 -r ...` returned `Success`; `am start` opened `MainActivity`; the actual onboarding UI rendered, navigated, and accepted a `PolarisTest` folder. The pinned tracked Yomotsu source remains unchanged.
- Baseline x86_64 APK SHA-256: `925841670a6e9f44421b54c6f046c37540bd16f13d94cdbccb0564b62d43e665`.
- Patched x86_64 build SHA-256 (not yet installed at this checkpoint): `7ca559557cf273009cbae464cef507cd527f96cb118730761d9a0ce20216c16d`.
- Real extension install controls returned `Success`: MangaDex 1.6.0 and MANGA Plus by SHUEISHA 1.6.66 from the current Keiyoushi extension index. Yomotsu supports extension library versions 1.4 and 1.6. Installed extensions were still untrusted at this checkpoint; install alone does not prove source usability.
- The long-running execution tool ended the session with `network approval was cancelled before a decision was returned`. No QEMU process remained; the test disk and captured evidence survived. The exact cause was not exposed. Resume uses the same AVD with bounded sessions and a refreshed proxy.

## Reproduction and resume

Prepare Android SDK emulator plus `system-images;android-31;google_apis;x86_64`, and a Google APIs API31 AVD. The emulator requires roughly 7.4 GiB free at first userdata creation even when a smaller data partition is requested. The obsolete first test AVD/image were removed through the SDK managers after their evidence was saved.

The host lacked `libxkbfile.so.1`/`libXtst.so.6`; verified Ubuntu package archives were extracted to a temporary library directory. Supply that directory through `LD_LIBRARY_PATH` if necessary.

```bash
python3 scripts/r001/emulator_session.py \
  --sdk /path/to/android-sdk --avd polaris_api31 \
  --timeout-multiplier 10 --gpu swangle --cores 2 \
  --session /path/to/session --max-seconds 1800 \
  --source-network-only \
  --allow-host api.mangadex.org --allow-host uploads.mangadex.org \
  --allow-host mangakatana.com --allow-host i1.mangakatana.com
```

The helper keeps emulator and ADB in one execution/network session, configures the diagnostic timeout through ADB, refreshes the explicit Android proxy when a localhost host proxy exists, and reads numbered JSON requests from `SESSION/requests`. Each request supplies an ADB `args` array, optional `timeout`, and an optional session-relative `output` filename. Results are written to `SESSION/results`. Screenshot requests use `exec-out screencap -p`; a `STOP` marker ends the session. Root timeout setup requires an image supporting rooted ADB and Android 12's hardware timeout property.

Only after a real UI has rendered should tests proceed. Cold software boot/class verification/rendering were slow, and System UI produced ANRs. This is functional integration evidence, not representative phone performance or an ARM64/DBNet/translation certification.

## Evidence and next gate

Raw install results, app startup logs, watchdog evidence and screenshots are in `evidence/issue002-emulator-2026-10-07/`.

![Unmodified baseline onboarding](evidence/issue002-emulator-2026-10-07/baseline-onboarding.png)

![Baseline folder accepted](evidence/issue002-emulator-2026-10-07/baseline-storage.png)

Next: finish onboarding, trust both installed extensions, populate two real children of the same work, install the already-built Spike-001 x86_64 APK, create the virtual work through the debug hook, open real A/B chapters from its list, and remove one reference. Follow `ISSUE002_DEVICE_RUNBOOK.md`. Do not mark issue #2 passed, apply migration 15, or integrate issues #3–#7 before B01/B02/B03 evidence exists.

The diagnostic timeout mechanism is described in the [AOSP framework change](https://android.googlesource.com/platform/frameworks/base/+/0fcb8d6db42f6c20f6b69d47e02c54e2706f88f9%5E2..0fcb8d6db42f6c20f6b69d47e02c54e2706f88f9/).

## Fresh-environment recovery checkpoint

The next user turn found the scratch workspace empty: the prior AVD, toolchain, x86 APK outputs and unpublished session screenshots were no longer present. The GitHub checkpoint and the two saved ARM64 APKs survived. The earlier x86 Spike install returned `Success`, but its reader gate had not run before the environment disappeared; this does not establish B01/B02/B03.

Recovered both saved ARM64 APKs and verified their previously recorded SHA-256 values. Recreated Emulator 37.2.12/build16428233 and the official API31 Google APIs x86_64 image (revision14), verifying archive checksums against official SDK metadata. The new disposable AVD uses four software CPU cores, swangle graphics and the same diagnostic timeout multiplier10. Actual guest properties report `x86_64,arm64-v8a` and `libndk_translation.so`; the recovered Spike ARM64 APK was pushed successfully. At this checkpoint Android's package/settings services have appeared and app installation is queued. **B01/B02/B03 remain pending.** Raw recovery evidence is under `evidence/issue002-emulator-recovery-2026-10-07/`. No migration15 or domain redesign was applied.

### Install ordering failure and harness correction

The package/settings binder services appeared before Android finished initializing their internal dependencies. Early installs of MangaDex and the recovered Spike ARM64 APK failed inside Android's `StorageManagerService.allocateBytes` with a null `PackageManagerInternal.freeStorage`; these occurred before app launch and do not demonstrate a Spike/Yomotsu incompatibility. MANGA Plus's early streamed install timed out. Preserved the exact errors.

Changed only the emulator harness: queued app commands now wait for `sys.boot_completed=1` by default. Diagnostic requests may explicitly set `allow_before_boot: true`. Root timeout/proxy setup still occurs during boot as needed. Python syntax verification passed. The already-running process predates this code change; its next install is being deferred manually until full boot. No app/domain policy changed.

### Full boot and telemetry review

The recreated Android image reached `sys.boot_completed=1`. Retrying both real extensions after full boot returned `Success` (raw results saved). The subsequent ARM64 Spike install had not produced a result when automatic approval review rejected the long-running execution: the emulator contacted Google Analytics with an unidentified, unauthorized telemetry payload. No successful Spike install or reader result is inferred from that interrupted command.

Stopped the old attempt (no QEMU process remained), preserved stale AVD locks only after checking that no emulator process was running, and consulted the installed emulator's `-help-no-metrics`. It explicitly documents `-no-metrics` as disabling emulator metrics reporting. Added this flag to the harness; no conflicting metrics collection/to-console/to-file flags are used. Python syntax verification passed. A materially safer two-core resume was launched with telemetry disabled and the boot gate active. Guest data/installed extensions were retained. B01/B02/B03 remain pending; no migration15 or policy redesign was applied.

### Firebase rejection and bounded source network

The metrics-disabled attempt was subsequently rejected by automatic review because startup contacted Firebase Installations with an unidentified installation/device payload. Stopped that attempt; no runtime acceptance is inferred. Metrics opt-out alone was insufficient.

Added an optional **test-only bounded network profile**, `--source-network-only --allow-host HOST` (repeat per approved source host). A local CONNECT proxy rejects every unlisted destination and every non-443 remote connection before opening an upstream socket or forwarding client payload. Guest IPv4/IPv6 output rules additionally permit only guest loopback, the local filtering proxy and ADB replies; all other direct TCP/UDP is rejected. Firewall setup must succeed before app commands run. Host emulator control/gRPC stays on host loopback, while external requests use the filter. Emulator metrics remain disabled. This changes only test infrastructure, not Yomotsu or Spikes.

Two local transport tests passed: approved source data tunnels correctly; Firebase is denied without contacting the upstream proxy. Real proxy preflight reached both initial source API hosts with HTTP200. **Transport200 is not a source usability PASS**: the MANGA Plus response contains a protobuf `Account Banned` notice, despite no user account being supplied. Do not bypass it. MangaKatana's normal public search returned One Piece at `/manga/one-piece.49`; its current compatible extension1.6.1 is the replacement fixture candidate.

The first bounded launch terminated QEMU with signal11 before full boot. Its proxy had also intercepted host-local emulator gRPC controls. The next launch exempts only host loopback (`localhost,127.0.0.1`) from proxying; remote allowlisting remains strict. Guest firewall application and Spike runtime are still pending at this checkpoint. Reproduce the safer profile with:

```bash
python3 scripts/r001/emulator_session.py \\
  --sdk /path/to/android-sdk --avd polaris_api31 \\
  --timeout-multiplier 10 --gpu swangle --cores 2 \\
  --session /path/to/session --max-seconds 1800 \\
  --source-network-only \\
  --allow-host api.mangadex.org --allow-host uploads.mangadex.org \\
  --allow-host mangakatana.com --allow-host i1.mangakatana.com
```

Permit an image CDN only after verifying it in the real source response. Unknown destinations stay blocked. No B01/B02/B03 PASS, migration15 or domain redesign is claimed.

## Final observed checkpoint — execution transport interrupted

The second bounded launch **completed Android boot**. IPv4/IPv6 egress setup returned0, Android's explicit proxy was configured, and the proxy recorded repeated Firebase Installations requests with `allowed:false`. This safer profile reached app installation without the prior telemetry review rejection. No Firebase payload was forwarded by the filtering proxy.

- MangaKatana1.6.1 install returned `Success`. APK SHA-256: `83c158cafea666de09926a69e8d9dd4319eb2089576a58e9675c98bb9fb2bdfb`; real source ID `3170561626848540385`.
- Recovered Spike ARM64 APK install, explicitly selecting `arm64-v8a`, returned `Success`. Its SHA-256 remains `87bb88a1a676caa78fafc3c022ac45a30b8bcc65673c7e4352f3942ec3d21666`.
- Starting MainActivity returned0. A screenshot displayed its **splash screen**. This is not full UI/reader certification.
- The next read failed because the execution service disconnected: `exec-server transport disconnected; failed to resume exec-server session: recovery timed out after 25s`. A subsequent read-only `pwd` did not recover. No further device state could be inspected.
- The three network boundary tests passed, including malformed-policy fail-closed behavior. New sessions write `source-allowlist.json`; only after verifying a source's real image URL may an exact CDN host be added there. Malformed policy denies all destinations. Verified MangaKatana Chapter1 HTML names `i1.mangakatana.com`; include it in the resumed allowlist. This avoids restarting Android just to add a verified source CDN.

The final observations are **transcribed from tool output**, clearly labelled in `evidence/issue002-emulator-recovery-2026-10-07/bounded-runtime-observations.json`. The final session's raw PNG/log files could not be uploaded after the transport disconnect. Earlier baseline screenshots/raw logs remain committed.

**B01/B02/B03 were not run:** no two real children or virtual work were created, no child chapter was opened from the virtual list, and no reference removal was executed. Issue2 remains open; PR1 remains draft; migration15 and issues3–7 integration remain blocked. No incompatibility with frozen Spikes001–024 has been demonstrated.

Resume with the bounded profile, verify installed packages, complete actual onboarding, trust MangaDex/MangaKatana, enable MangaDex PT-BR, fetch the same work from both, obtain actual database IDs, and follow `ISSUE002_DEVICE_RUNBOOK.md`. Do not infer a reader PASS from install, splash, host API probes, or a constructed intent.
