# Storage and translation lifecycle — P20261101.1

## Measured serialization example

`TranslationStorageSampleTest` uses the production `PageTranslation`/`TranslationBlock` classes and `Json.encodeToString`, then decodes the result to check lossless persistence. Each authored sample contains **20 pages and 200 blocks**, with source text, Portuguese translation and geometric fields. These are synthetic serialization measurements, not OCR results or measurements of the user's Guilty Library chapter.

| Source | Saved JSON bytes | Approximate KiB |
| --- | ---: | ---: |
| English | 47,772 | 46.7 |
| Japanese | 51,172 | 50.0 |
| Simplified Chinese | 48,172 | 47.0 |
| Traditional Chinese | 48,172 | 47.0 |
| Korean | 53,172 | 51.9 |

One hundred saved chapters with exactly this profile would use approximately 4.8–5.3 MB for chapter JSON alone. This does **not** include originals, paragraph cache, glossary, models, APK/native libraries, filesystem allocation overhead or PDF render cache. Real chapters vary in page count, text length, grouping/geometry and optional cleanup masks. There is no universal percentage increase and no second complete translated page image is persisted by this chapter pipeline.

## Separate storage groups

- Downloaded page images/comic archives: original content, usually the main per-chapter payload.
- Imported documents: a managed copy in `local/`; the original selected phone file remains outside it. Import can therefore add the file's size again.
- Chapter translations: text and geometry JSON under `translations/`.
- Machine phrase cache: persistent complete-line results in preferences, limited to 4,000 records per work/language pair. It is different from the persistent glossary and learned corrections.
- Document caches: materialized archive/PDF copies, rendered PDF PNG pages and translated text chunks. A 256 MiB **target** applies to these three managed cache directories together. Leases protect files/streams in use, so active files can temporarily exceed that target. Least recently used unpinned files are evicted; imported originals are outside the managed cache.
- ML Kit translation models: downloaded language resources shared between chapters. [Google's Android translation guide](https://developers.google.com/ml-kit/language/translation/android) describes models as approximately 30 MB. Actual installed languages are listed in the app; model/internal data bytes are included in the internal-data row. This is not a new model per chapter. Bundled OCR resources/native libraries also contribute to installation size.
- Installation: APK files, any extracted native libraries and Android-managed overhead. ARM APKs are exported individually to avoid sending the much larger all-ABI universal APK to each participant.

The storage screen measures app-owned internal/cache paths and the configured downloads/local/translations folders, never all PDFs on the phone. It reports ordinary file lengths, not exact disk allocation. SAF scans are capped by entry/time budgets, internal scans by entry budget; partial results are marked with `+`. Code cache is included with other cache. Native library files are shown separately when extracted. OS optimization/storage overhead and originals elsewhere on the device are outside this accounting.

## Deletion and retry behavior

`DownloadManager` routes both chapter and whole-work removal through `TranslationManager`. Existing chapter-deletion filters still run before cleanup, including the upstream protection rules. The translation gate cancels and joins the old translation worker before the original-delete callback and JSON removal. It removes the affected queued entries, serializes file edits/deletion and resumes other queued work unless the user paused it. Original deletion failure retains translation data and reports failure. A translation-file deletion failure is reported rather than counted as success.

Successful chapter cleanup removes the saved JSON and the chapter's source phrases from the work's machine cache across language pairs. Whole-work cleanup removes its machine phrase cache. Corrupt/missing chapter data causes a work-level machine-cache purge rather than guessing affected keys. **Neither operation clears `TranslationMemory`**, which retains glossary and learned corrections. A phrase shared with another chapter may lose a cached machine result and be recomputed, without losing vocabulary.

Re-download follows the existing explicit pending-request or effective automatic-translation policy. Known EN/JA/ZH/KO metadata can select the OCR input language without rewriting the user's preference. Same-source/target pairs do not queue a translation. Mixed/unknown source metadata uses the selected input. Asian global automation is opt-in initially; per-work overrides take priority. This is metadata routing, not recognition of a page's actual language.

The queue processes one source chapter at a time in this candidate to reduce simultaneous OCR/translation memory demand. The 4 MP PDF bitmap budget remains. Neither is a fixed process-RAM guarantee; physical-device memory/performance measurements remain pending.

## Glossary behavior

Native EPUB/DOCX/TXT translation now uses the same glossary protection/resolution helpers as comic translation. Its text cache key includes work title, language pair and vocabulary revision. Changing the glossary invalidates reuse of stale book text. CJK terms can match without Latin-style word boundaries, allowing names attached to particles to be protected; Latin word boundaries remain. These are text-level tests, not native OCR quality evidence.

## Beta acceptance boundary

The candidate targets Android 8/API 26 and exports ARM64 and ARM32 APKs with versionCode 102 and versionName `0.1.0-beta.1`. APK signatures and regression comparison are checked before the export. The export is not a store release or a claim of acceptance on A12/S20 FE/S8+/A52. See the private-beta guide and test matrix. English user screenshots remain the only user-confirmed translation language; Japanese, Chinese and Korean OCR/translation quality remain pending, including vertical text and a source-language review of the authored references.
