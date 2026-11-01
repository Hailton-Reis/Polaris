# Document reader and research candidate — P20261101.1

This overlay adds local document reading and discovery to the pinned Android candidate. Apply it after Spike001, the debug hook and the reader translation overlay. `scripts/r001/build_issue002.sh` now applies that sequence automatically. The original upstream checkout stays pinned at `0fb80c439ef816eeb50674f1b90af39918b176d8`.

## Behavior

- **More → Documents and research → Browse and add a file** uses the Android file picker to select a document already on the phone. It does not scan Downloads, MediaStore or the phone's other directories. The original local source still lists files intentionally placed in the app's own `local/` directory.
- Selecting a file, opening a shared document, choosing a search result or entering a direct HTTP(S) link opens an organization form. Only **Add to library** copies/downloads the document and adds a favorite. Cancelling dismisses the selection without copying the file or changing the library. Each completed import gets a unique directory; the original phone file remains in place and existing imports are not overwritten.
- The form offers an optional title, a content type (**Manga, Manhwas, Comics, Books, Articles or Documents**), optional format grouping, existing library categories and an optional new personal category. Local files default to Documents; their extension does not determine their content type. Bibliographic results suggest Books or Articles, which the user can change.
- Content type and optional format use normal library categories, such as **Books** and **Format: PDF**. Matching categories are reused, including the supported Portuguese/English labels and case/accent variants. New categories inherit the library's sort flags. Membership is written only for the newly imported work. Category assignment failures are reported before the work is marked as a library favorite. Existing works are not bulk reclassified; the library's existing category editor remains available.
- PDF pages use Android `PdfRenderer`, bounded raster dimensions, the existing page reader, reading progress and OCR translation queue. Local PDF/archive chapters can be translated without downloading them again.
- EPUB follows its spine order and displays text and embedded local images. DOCX extracts body paragraphs, line breaks, table cell text and embedded images. TXT supports UTF-8, UTF-16 with BOM and Windows-1252 fallback.
- Text documents have a separate native section reader, font size, contents, original/translated text and explicit completion. Section, paragraph and scroll offset are stored in the existing chapter memo, preserving unrelated memo fields. History uses the existing history table. No database migration is added.
- Text translation uses the existing input/output language preferences with ML Kit on-device models, skips OCR and caches translated chunks. It does not inherit the comic-specific prompt. It may need to download language models first.
- Articles query Crossref and Europe PMC; books query Gutendex and Open Library. Queries support general terms, title, author and DOI. Results identify their providers and retain separate provenance. File links come from provider metadata or the known PDF endpoint for an explicitly open-access PMC article. A failed provider does not hide another provider's results.
- A configurable website URL with `{query}` opens broader searches inside the existing in-app browser. This is a website search, not an additional parsed metadata API. Direct document links can be copied back into the importer. Bundled defaults do not restrict the user's choice of website.
- Android **Open with / Share** accepts PDF, EPUB, DOCX and TXT content URIs; the file picker also accepts the existing comic archive formats.

## Scope and limits

DOCX/EPUB use reflowable reading: Word pagination, complex tables, equations, styles, footnotes, CSS and interactive content are not reproduced faithfully. EPUB contents initially use spine item names rather than a complete EPUB navigation document. PDF is rendered as pages, including text PDFs; translation currently uses the existing page OCR pipeline rather than native PDF text extraction. Password-protected/DRM documents are unsupported.

Search returns the first results from the stated providers. It does not cover the entire internet, guarantee publisher access or invent a full-text download for metadata-only results. Direct import does not reuse a publisher website's logged-in browser session.

Files are bounded at 256 MiB; text/XML at 16 MiB and individual EPUB sections at 4 MiB. Text chunks are bounded before translation. Archive references resolve inside the archive and never fetch remote images. PDF pages and translation data use Android cache storage; original imported files stay in the chosen local-source storage folder. Removing a favorite does not delete the original local file.

## Apply and verification

```
python3 scripts/r001/apply_document_reader.py PATH_TO_PATCHED_YOMOTSU
POLARIS_YOMOTSU_CHECKOUT=PATH_TO_PINNED_YOMOTSU python3 -m unittest discover -s scripts/r001 -p test_apply_document_reader.py -v
```

The applier requires the pinned commit and current reader prerequisite, is idempotent, rejects source drift atomically and refuses migration15. [TEST_RESULTS.json](TEST_RESULTS.json) records final build and test evidence. [The organization guide](../../docs/reader/DOCUMENT_ORGANIZATION_P20261031_4.md) covers the new selective import flow; [the document reading guide](../../docs/reader/DOCUMENTS_P20261031_3.md) covers the underlying readers. The prior revision's evidence is preserved in [TEST_RESULTS_P20261031_3.json](TEST_RESULTS_P20261031_3.json). Neither assembly nor unit tests establish native Android rendering or a successful user-device import.

The earlier crop-off diagnosis is confirmed by the user. Automatic crop protection and this document UI still require visual acceptance. The separate R001 two-source gate and backupv2 remain pending. This is an engineering candidate, not a production release.

## P20261101.1 — internal beta and storage

This revision introduced versionName `0.1.0-beta.1` and versionCode 102. The [beta guide](../internal-beta/README.md) covers private ARM APK distribution, storage measurement, download/translation deletion, persistent vocabulary and the still-pending EN/JA/ZH/KO device matrix. [Storage implementation and measured examples](../internal-beta/STORAGE_AND_LIFECYCLE.md) distinguish chapter JSON, originals, language models and bounded regenerable document cache. Prior P20261031.4 evidence is preserved in [TEST_RESULTS_P20261031_4.json](TEST_RESULTS_P20261031_4.json).

## P20261101.3 — About and update channels

The current candidate is `0.1.0-beta.3`, versionCode 104. It retains the P20261101.2 automatic English-to-Portuguese preparation and adds an expanded About screen, manual checks and daily opening checks against Polaris GitHub Releases. Experimental releases require an explicit opt-in, off by default even in beta builds. Published `manifest.json` metadata gates package identity, versionCode, Android and ABI; downloaded APKs must match their SHA-256 before installation is offered. Checks never start APK downloads automatically.

The beta.3 prerelease and repository are now public, with release title and notes written for general readers; all six asset sizes and SHA-256 match the verified package. Changing the release presentation did not change its APKs. See [publication status](../internal-beta/PUBLICATION_STATUS.json). Login-free handset access and an actual same-signature upgrade remain pending, along with storage and language acceptance. The twenty added tests passed; the complete comparison has 491 passes and the same 34 preexisting failures. Previous English-preparation evidence is preserved in [TEST_RESULTS_P20261101_2.json](TEST_RESULTS_P20261101_2.json).
