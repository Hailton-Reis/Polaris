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

## P20261102.1 — Polaris app identity

The new candidate is `0.1.0-beta.4`, versionCode 105. The beta.3 APK still identified itself as Yomotsu in Android. The overlay now gives the application its own Polaris label, star-and-book vector launcher icon, Android 13 themed icon, splash and About logo, and also updates the inherited app-name string. Unique launcher resources avoid upstream/debug icon overrides.

The exporter inspects the compiled APK with AAPT2 and rejects inherited names or a wrong application/round icon. Both ARM APKs and the x86_64 build passed branding verification. The package identifier and signing certificate match the distributed beta.3, allowing Android to offer an update to that installation. Actual A12 installation, icon cache refresh and data continuity still require the user's device check.

Android tests remain 525 total, 491 passed and the same 34 preexisting failures. The six packaging tests include three new compiled-branding boundary tests. The previous beta.3 build evidence remains in [TEST_RESULTS_P20261101_3.json](TEST_RESULTS_P20261101_3.json). The already published beta.3 APKs are not replaced by this candidate.


## P20261102.2 — internal long-strip translation review

Candidate `0.1.0-beta.5`, versionCode 106, remains unpublished. Advanced translation editing is off by default in both pager and webtoon; manual insertion and per-block editing are available when explicitly enabled. Gemini uses bounded complete-response batches and bypasses the shared offline phrase cache; saved chapters still support offline reading. A debug-only shell-permission receiver and the Windows collector export paired screenshots, the active original page and saved post-filter text. The collector does not initiate OCR/API requests. CMD options 13/14 apply and restore a FHD emulator display.

Missing last lines and text outside balloons remain unverified until an actual failing source page is captured. See [the diagnosis procedure](../../docs/REVISAO_TRADUCAO_FAIXA_LONGA.md). No emulator runtime or live Gemini quality acceptance is implied by host tests.


## P20261102.3 — ML Kit and OCR review

Candidate beta.6 / versionCode 107 keeps Gemini outside the current test round. Recognized single-character text is retained; detected balloons are protected from the oversized-short-text sound-effect filter. An opt-in, English-only long-page ML Kit path reads overlapping original-scale regions sequentially with a bounded decoded pixel budget and geometric duplicate reconciliation. It adds no model or API and remains off pending real-device/case validation. The unused direct generative SDK dependency was removed.

The Windows launcher selects a FHD framebuffer on Polaris startup and applies 420 dpi before opening the app, including existing AVD sessions; baseline is unchanged. An original synthetic long-strip CBZ and expected text are included as a pending manual control. See [the research and decisions](../../docs/PESQUISA_OCR_MLKIT_2026_11_02.md).


## P20261102.4 — shared regional OCR

Internal candidate beta.7 / versionCode 108 applies the bounded overlapping-region path to both ML Kit and the bundled Paddle Small, in English. The setting remains off by default and preserves the beta.6 preference key. The two engines share bounds/EXIF checks, sequential decoding and geometric duplicate reconciliation. No model was added; compiled ARM APKs grew by 18,988 bytes each, with all compared assets and native libraries unchanged.

The combined comparison has 547 JVM tests: 513 pass and the same 34 baseline failures. All twelve reconciliation tests pass, including recorded ML Kit/Small/Tiny geometry that preserves the 38 control lines. Two decoder component tests pass on AOSP Android 8 x86_64 with an isolated instrumentation Application: the minimal image lacks WebView, so full reader startup remains unvalidated there. This does not change the reader's Application. Actual ARM device acceptance remains pending. See [implementation, limits and validation](../../docs/OCR_FAIXAS_COMPARTILHADAS_P20261102_4.md) and [current evidence](TEST_RESULTS.json).

## P20261103.1 — capítulos únicos e fontes por obra

Beta.8 / versionCode 109 was published as a public prerelease on 2026-11-03; device acceptance remains pending. The work screen, reader, next-chapter actions and library counts now use one logical chapter per identity. Official/Unofficial versions stay stored but do not repeat the reading sequence; decimals, parts, volumes, seasons and identifiable extras remain distinct. Automatic discovery compares enabled installed providers in the same language using title, creator and numbering confirmation. A per-work source selector preserves records and downloads when switching. Portable origin metadata routes network requests while keeping the original library identity, glossary and storage scope. Alternative providers have separate translation/cache identities. About includes a local dedication easter egg.

The final comparison has **589 JVM tests: 555 pass and the same 34 baseline failures**. All 42 tests added since beta.7 pass, including foreground/background discovery, timeouts, hidden providers, cancellation, source-pin races and metadata-only refresh safety. Both ARM APKs assembled and retain the distributed signing certificate. Each grew by 1,676,188 bytes (about 1.60 MiB) versus beta.7; all compared assets/native libraries are byte-identical. No model was added. Device acceptance and real-provider workflows remain pending. All seven published assets were downloaded through public URLs without an Authorization header and matched their expected SHA-256/size. [Publication evidence](../public-releases/0.1.0-beta.8/PUBLICATION.json) is separate from device acceptance. See [behavior, storage and limits](../../docs/SEQUENCIA_E_FONTES_P20261103_1.md), [preserved beta.8 evidence](TEST_RESULTS_P20261103_1.json), and [the preserved beta.7 evidence](TEST_RESULTS_P20261102_4.json).

## P20261104.1 — limites de escrita e atualização recuperável

Internal beta.9 / versionCode 110 remains unpublished. Undetected captions now constrain their fallback writing area to the measured background. Both readers resolve overlapping writing regions together, including saved caption geometry. Legacy cleanup no longer adds padding beyond its measured rectangle. OCR strips and DBNet are mutually exclusive; existing conflicting flags retain strips with the selected OCR. The inert AOT-GAN setting was removed from the screen. No model or API was added.

The updater no longer cancels when its screen is disposed. Interrupted APK bytes use a URL/digest-specific partial file, HTTP Range, validated 206/416 handling, clean fallback to 200 and SHA-256 verification before atomic promotion. WorkManager retries transient failures with network constraints and backoff. A completion notification opens Android's installer on user action. This remains a full APK update, with same-file download recovery rather than binary delta patches.

The complete native comparison has **624 JVM tests: 607 pass and 17 preexisting failures**, with no new failures, skips or missing baseline cases. All 35 added cases pass, including 12 real localhost HTTP/stream tests. Seventeen old bitmap cases now pass after correcting their bulk-pixel test fixtures. Seven Android component tests pass on software AOSP API26 x86_64: four renderer controls, two decoder controls and one cleanup-mask control. These use an isolated Application and authored images with the default font. Real manga pages, Anime Ace, ARM inference, full app startup and Android update/install workflows still require acceptance.

Both ARM APKs retain the distributed signing certificate and verified Polaris branding. Fresh ZIP packaging removed unused incremental output space; both APKs are smaller than public beta.8 (exact sizes in the evidence JSON). Assets and native libraries remain identical. Every unsigned APK entry matches the full-test-build artifact before repackaging. See [behavior, diagnosis and limits](../../docs/CORRECOES_LEITURA_ATUALIZACAO_P20261104_1.md), [test evidence](TEST_RESULTS.json) and [rendered controls](caption-layout-controls/).

The [real chapter40 benchmark](../ocr-benchmark/20261104-chapter40/README.md) measures11 manually transcribed difficult regions from public Asura originals: Paddle9/11 exact (2/465 character errors), MLKit7/11 (10/465). White controls pass both. This is scoped OCR quality evidence, with desktop/Android runtime differences and an incomplete software-emulator regional pass; it is not physical ARM performance or full reader/translation acceptance.
