# Spike-001 actual Kotlin domain-contract tests (host-only)

Run `bash scripts/r001/test_spike001_host.sh` with a Kotlin JVM installation that includes `kotlinx-coroutines-core-jvm.jar` (e.g. SDKMAN Kotlin) and JDK 21.

The script compiles **the real staged** `GetMergedChaptersByMangaId.kt` and `MergedMangaReference.kt`, together with minimal API contract stubs located in this directory. It does not copy or rewrite the two production classes.

Eight host tests assert: combined chapters belong to both real child IDs, reader argument pairs retain their real child manga IDs, priority dedupe, highest-chapter mode, removal of a reference, nullable/orphan reference handling, live Flow updates after removal, and an empty result with no children.

The fixtures are stand-ins for Yomotsu repositories and coroutines collect flows on the JVM. Results **do not certify** SQLDelight, actual extensions, Android Activity launches, fetched pages or B01/B02/B03 runtime acceptance. Migration 15 must not be applied until the real Android gate passes.

The tested Kotlin files are byte-for-byte the real repository sources: `GetMergedChaptersByMangaId.kt`, `MergedMangaReference.kt`, and `InternalSourceIds.kt`. All three compile from the staged production paths; fake classes are restricted to API stand-ins for `Chapter`, `ChapterRepository`, and `MangaMergeRepository`. The test intentionally does not replace these production functions with simulated versions.

Validation on 2026-10-08: 8/8 PASS using JDK 21 + kotlinc 1.9.0 and the installed kotlinx-coroutines JVM jar. It is host-domain proof only, and neither live Android UI nor source extension/network proof.
