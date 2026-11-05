# Polaris reader translation — 29/10/2026

The user changed the immediate priority from the two-source runtime gate to improving the existing reader and translation experience. This change is independent of canonical persistence and does not complete R001, unblock migration15, or enable backupv2.

## Existing runtime evidence

The user's Windows API35 Spike001 AVD reached the library, loaded an English Guilty Library chapter, downloaded it, translated it with on-device ML Kit, and displayed Portuguese pages. User screenshots of chapter1.1/pages3–5 and their confirmation establish this single-source workflow in the previous APK. They also show fragmented lines and incomplete translation. These screenshots are not evidence of the new candidate's runtime quality.

## Candidate behavior

- A chapter's translation icon is now available before download. Its label is **Baixar e traduzir** when the chapter is not downloaded.
- One tap saves an explicit request for that chapter, starts/reuses the existing download queue, and queues translation after successful download. It does not turn on automatic translation for the entire work.
- Download and translation progress/error indicators use the existing queues. Cancelling the download removes the explicit request. If the enqueue call throws, the request remains available to retry.
- Pending requests survive restart but are classified as application state and excluded from preference backups. This prevents carrying operational chapter IDs into an unrelated restored library.
- The text-fit algorithm no longer binary-searches the nonmonotonic word-boundary predicate. It chooses the largest measured fitting layout that preserves whole words when one exists, retaining existing safe envelopes, font ceilings and overflow fallback.
- Existing downloaded/local chapters retain their previous translation availability. OCR/provider settings and saved translations are unchanged.

Implementation and application instructions: `integration/reader-translation-ux/README.md`.

## Runtime checks after updating the Windows test AVD

Use the existing local build/update path, keeping its existing workspace and signing key. No new setup, library recreation, uninstall or storage-folder selection is required by this code change.

1. Pick a chapter that is not downloaded and tap its translation icon. Verify download progress followed by translation progress and Portuguese pages.
2. Reopen the already translated Guilty Library chapter to compare text fit on the same pages, without redoing OCR to isolate the rendering change.
3. Cancel a pending download and confirm it does not later enqueue an explicit translation. Confirm an ordinary download still follows the work's existing automatic-translation preference.
4. For an intentionally failed download, retry and verify the explicit request remains scoped to that chapter. Check that duplicate taps do not create duplicate translation requests.

The cloud emulator previously hit Android System UI ANRs. A successful build/unit suite is not a replacement for these visual checks. Do not declare improved translation accuracy or completed multi-source acceptance from the candidate build alone.
