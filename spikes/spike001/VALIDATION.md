# Spike-001 Validation

## Baseline
- Yomotsu commit: `0fb80c439ef816eeb50674f1b90af39918b176d8`
- TachiyomiSY commit: `14648c7cf0aa84e5a35d48de9dbf1386df6cca42`

## Completed

### Patch applicator
`apply_spike001.py` was executed against a fixture containing the exact Yomotsu baseline anchor blocks used by the patch.

Result: PASS.

### Kotlin compilation — domain slice
The real Spike-001 domain sources and `MergedSource` were compiled with Kotlin/JVM using minimal stubs for Yomotsu APIs.

Result: PASS.

### Domain behavior tests
Validated:
1. CHAPTER_SORT_PRIORITY
2. CHAPTER_SORT_MOST_CHAPTERS
3. CHAPTER_SORT_HIGHEST_CHAPTER_NUMBER
4. CHAPTER_SORT_NO_DEDUPE

Result: SPIKE001_DOMAIN_TESTS_PASS.

## Architectural finding
Yomotsu's manga screen launches the reader with `chapter.mangaId`, not the displayed parent manga ID.

Therefore a virtual merged work can display chapters belonging to real child manga entries and clicking a chapter naturally opens the reader using that child's real source.

## Pending
- Real Yomotsu Gradle build.
- SQLDelight generation against the full project.
- Android runtime test.
- Creating a real merged entry.
- Opening chapters from two installed extensions.
