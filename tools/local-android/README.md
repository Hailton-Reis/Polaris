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

Host self-tests (8 safe, offline cases):

```powershell
py -3 -m unittest tools/local-android/test_polaris_local.py -v
```

The Python tests exercise command/protection logic only. Actual Windows/SDK/Gradle APK compilation must be executed on the user's PC.
