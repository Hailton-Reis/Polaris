# Local Android validation — no GitHub Actions minutes

Entry point: `polaris_local.py`. It runs the existing `scripts/r001/build_issue002.sh` in a guarded environment from a full Polaris checkout. It is not a replacement for the Android test gate.

From PowerShell, in the `Polaris` repository:

```powershell
py -3 tools\local-android\polaris_local.py check
py -3 tools\local-android\polaris_local.py prepare
py -3 tools\local-android\polaris_local.py build
```

`check`: read-only environment inspection; `prepare`: clones and pins upstream Yomotsu; `build`: runs baseline and patched Android build/tests, produces evidence under `~/PolarisLocal/evidence/` without overwriting. The Android runner does not access GitHub Actions or enable v2 restores.

Full instructions: [`docs/r001/LOCAL_ANDROID_BUILD_NO_ACTIONS.md`](../../docs/r001/LOCAL_ANDROID_BUILD_NO_ACTIONS.md).

Host orchestration self-tests (11 cases):

```powershell
py -3 -m unittest tools/local-android/test_polaris_local.py -v
```

The Python tests exercise command/protection logic only. Actual Windows/SDK/Gradle APK compilation must be executed on the user's PC.

## Build performance

The default `auto` profile detects CPU/RAM and enables project parallelism, task caching, incremental Kotlin and daemon reuse. A 16-thread/32 GiB machine selects up to 8 workers and an 8 GiB Gradle heap. Kotlin compilation runs in-process to avoid a second large compiler heap. This is an upper bound, not a guarantee of continuous full CPU usage.

Assembly and unit tests share one Gradle invocation per variant (two invocations total). Complete APK metadata, assembly completion and JUnit coverage are verified before the existing regression comparison. The build still uses isolated new worktrees. Hardware limits and per-phase times are saved in the evidence directory; no global Gradle properties are edited.

Optional diagnostic fallback: `polaris_local.py build --build-profile conservative`. Existing CMD option 4 needs no extra arguments and picks `auto` by default. See the [performance notes and verification limits](../../docs/r001/LOCAL_BUILD_PERFORMANCE_2026_10_31.md).


## Long-strip translation review

`polaris_translation_capture.py` supplies CMD actions 12 (paired screenshots, active source page and saved OCR/translation), 13 (FHD display) and 14 (restore display). It targets only the owned Polaris AVD, not phones or the baseline AVD. It requires the new diagnostic build and a loaded, already translated webtoon chapter. It does not start OCR/translation or upload evidence. See [the review procedure](../../docs/REVISAO_TRADUCAO_FAIXA_LONGA.md). Collection results are separate from pending quality acceptance; capture starts at the current reading position.


Polaris startup (actions 9/10) now selects a FHD framebuffer and applies 420 dpi before launching the reader, including when reusing a running owned AVD. Action 13 is optional. Action 14 restores saved manual overrides; the next launcher invocation prepares FHD again. The baseline AVD is unchanged. Shared display logic lives in `polaris_emulator_display.py`; the SDK explicitly documents that `-dpi-device` is obsolete/ignored, so density uses ADB instead.
