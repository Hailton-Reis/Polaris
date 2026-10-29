# Reader translation UX candidate

Applies to pinned Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`, after the existing Spike001/debug-hook contracts have passed.

## User behavior

The translation icon is available for a chapter that has not been downloaded. Its tooltip/accessibility label is **Download and translate / Baixar e traduzir**. One click records an explicit request for that chapter and uses the existing download queue. The existing download progress remains visible; translation starts through the existing queue only after successful download. Downloading a chapter normally still follows the existing per-work automatic-translation preference.

Explicit requests survive application restart. Cancelling the download, deleting its queued chapter/manga, clearing the download queue, or removing queued downloads during manga rename cancels the relevant requests. If the enqueue call throws, the explicit request remains available for retry. The action does not enable automatic translation for the whole work or change OCR/provider settings.

The text-fit selector now binary-searches only the geometric fit predicate, then checks word-boundary preservation from the largest fitting size downward. Word preservation can be nonmonotonic across font sizes; the old binary search could skip a larger intact layout. Measurements are memoized; existing balloon envelopes and maximum font sizes remain unchanged. This is a targeted layout fix, not a claim that every OCR/translation/layout defect is resolved.

## Apply

```
python3 scripts/r001/apply_reader_translation_ux.py PATH_TO_PATCHED_YOMOTSU
```

The build driver calls this after validating the original Spike001 changes. The overlay is idempotent, refuses unexpected source differences without partial application, and rejects migration15. The original pinned checkout is not modified.

## Validation

The candidate adds real Kotlin tests for persisted explicit requests, cancellation, retry after enqueue failure, duplicate/concurrent clicks, and a nonmonotonic word-fit regression. Existing translation launch and fit suites are included in the targeted Android unit-test run. The patch application tests use fresh real pinned worktrees, including source-drift rejection and the migration gate.

A successful build/unit suite does not prove the new UI on the user's Windows AVD. Existing screenshots prove the previous APK can download, translate with ML Kit, and display Portuguese pages from Guilty Library. The new candidate still needs that same single-source flow checked after an update. The separate two-source gate remains pending and does not block this reader-only candidate, per the user's new priority. No migration15, canonical translation bridge, repository catalog, backupv2 enablement or production release is included.
