# Translation placement and English-source auto-download — 30/10/2026

User evidence: Guilty Library chapter1.3, pages2–11, Windows API35 Spike001. Portuguese overlays leave English text visible and sometimes cover neighboring art/balloons. The user subsequently confirmed the screenshots are from the old installed APK; the candidate's font-fit and placement changes have not yet been tested there. This is not accepted as correct visual placement. The 29/10 font-fit tests did not certify geometry in an actual reader.

The candidate corrects layout constraint handling before scaling, uses physical absolute coordinates, and maps stored translation dimensions to the reader's source-image dimensions. The existing font-fit algorithm can then measure within the intended region. It does not claim to identify every balloon correctly or choose a new font family automatically.

On download completion, the default English-source policy reuses the existing translation queue. Unknown/multilingual source metadata does not establish English; those sources require an explicit request or a per-work choice. English input and a different translation target are required. A user-selected per-work on/off overrides the global default; the global setting is exposed in Translations. No additional confirmation dialog is introduced.

## Manual acceptance after the candidate build

- Reopen the same already translated chapter/pages; compare text and cleanup placement before re-running OCR, at fit-to-width and zoomed views.
- Download a new chapter from an English source with no work override: observe download followed by translation.
- Disable automatic translation for the work, then repeat on another new chapter: downloading alone must not translate it. Explicit translation must still work.
- Portuguese/unknown sources must not translate solely because the global English default is on.

Successful compilation and policy/scale tests are not visual acceptance. R001 multi-source acceptance, migration15 and backupv2 remain separate and unchanged.
