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

A successful build/unit suite does not prove the new UI on the user's Windows AVD. Existing screenshots prove the initial APK can download, translate with ML Kit, and display Portuguese pages from Guilty Library. The user explicitly confirmed that their screenshots still come from the old installed version. The new candidate still needs that same single-source flow checked after an update. The separate two-source gate remains pending and does not block these independent improvements, per the user's new priority. No migration15, canonical translation bridge, backupv2 enablement or production release is included.

## 2026-10-30 — placement and English-source downloads

The user supplied screenshots from the old installed APK showing original English text still visible, with Portuguese overlays outside the corresponding balloons. They have not yet tested the font-fit or placement changes in this candidate.

Text and cleanup now use unbounded TopStart wrapping around explicitly sized regions so Compose cannot center oversized source-space children inside viewport constraints before scaling. OCR/page coordinates use absolute offsets (independent of UI layout direction). Pager zoom also accounts for source image width versus stored translation width; a downsampled translation must map into the source image's pixel space before viewer zoom.

A new default setting, **Traduzir downloads de fontes em inglês**, enables translation on completion for sources declaring English, when input is configured as English and target differs. This is source-metadata routing, not content language recognition. Portuguese, multilingual/unknown sources are not guessed. Explicit per-work choices win, including disabling automatic translation for a particular work. The work menu reflects this effective policy and updates when global settings/languages change. Existing explicit **Baixar e traduzir** requests retain priority. Already downloaded chapters are not automatically reprocessed.

These changes do not switch OCR engine, font family or translation provider, and do not require DBNet/ARM64. Stored translations are retained. Placement changes affect their rendering on reopening; no retranslation is required just to compare the new layout. Actual balloon detection/OCR grouping can still be imperfect and needs visual verification on the same pages and zoom levels.

## 2026-10-30 — repository discovery and chapter variants

An initial bundled catalog offers Project Nox and Keiyoushi from Browse settings, the Extensions menu and the repository toolbar. Search filters this local catalog by name, language or maintainer; it is not an internet-wide repository search. Adding an entry uses the existing repository parser/storage and extension refresh directly, with no new Polaris confirmation dialog. Permanent notices explain third-party code, signatures, overlapping repositories and source-use terms. Extension installation retains existing Android permission/signature checks. Nothing is installed merely by opening discovery.

Catalog tests cover search and duplicate aliases, including legacy repo.json and GitHub raw redirects. Controller tests cover repeated clicks, registration failures/retry, observer failures/retry and preserving registration when refresh throws. The existing extension manager can also handle listing failures itself with its existing toast; the controller does not claim to detect every per-repository failure suppressed by that layer. Public index HTTP/metadata probes are recorded separately and do not certify extension APKs or Android runtime behavior.

Chapter titles can span two lines, and source-supplied scanlator/group labels have a separate line marked Group/version. Counts say chapters/versions, and the chapter header points to the existing persistent group filter. Global-search results explain that they remain separated by source. Work action buttons use two columns on narrow layouts or with larger system fonts, keeping four columns when space permits. These presentation changes do not merge, delete, renumber or automatically hide entries. MangaFire's official/unofficial/side-story labels are preserved without inferring their authority. See [candidate notes](../../docs/reader/DISCOVERY_CHAPTER_CLARITY_2026_10_30.md).

## 2026-10-31 — paginated viewport synchronization

The user reports aligned long-strip rendering and displaced paginated rendering, and believes they updated, but the installed overlay revision is unconfirmed. SSIV applies pending fit/center changes during draw without necessarily emitting its scale/center callbacks. The paginated overlay now samples the image transform after each image draw, publishes scale and origin atomically, skips invalid/unready geometry, and renders in a fixed viewport with pixel translation. Image-load callbacks also respect the translation visibility preference and avoid forced SSIV casts for animated images. The long-strip rendering path is unchanged.

About now includes the candidate revision **Polaris P20261031.1**, separate from the pinned upstream commit. The revision label identifies this code candidate; rebuilding the same candidate updates the debug build date, not the revision label or Android versionCode. Future overlay code revisions must bump the label. See [implementation, evidence limits and visual checks](../../docs/reader/PAGER_VIEWPORT_2026_10_31.md). Geometry tests and assembly do not establish visual acceptance of the new paginated overlay.

## P20261031.2 — original image geometry for translated pages

The user confirmed P20261031.1 in About, demonstrated displaced paginated overlays without zoom, then confirmed that disabling **Crop borders** immediately aligned the saved translation. The prior viewport-synchronization change did not handle decoder cropping: stored OCR coordinates describe the original image, while SSIV source coordinates may describe the cropped image.

Translated pages now retain their original borders in both reader modes. Untranslated pages still use the selected crop preference; preferences are not rewritten. If a translation arrives on an already cropped open page, its holder requests one uncropped decode and withholds the obsolete overlay during that transition. Holder recycling resets the applied-crop state. Reader settings explain the translated-page exception. No OCR rerun, metadata rewrite or provider change is needed. About identifies this candidate as **Polaris P20261031.2**.

The automatic candidate still needs visual acceptance. The user's successful manual crop-off test is runtime evidence for the diagnosis and workaround, not a runtime PASS for the new APK. See [crop fix, tradeoff and checks](../../docs/reader/PAGER_CROP_FIX_P20261031_2.md).
