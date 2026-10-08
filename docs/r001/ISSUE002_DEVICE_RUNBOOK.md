# Issue #2 — device gate

Use the debug APK built with Spike-001 plus `integration/r001/debug/Spike001DebugActivity.kt`. The hook is absent from release builds. It adds a development activity; it does not replace the future work-first UX or change domain policies.

## Preconditions

- Android API 26+; prefer an ARM64 device matching the upstream DBNet runtime.
- Install and trust two compatible real source extensions.
- Add the same test work from both sources and refresh their chapters.
- After installing the patched debug APK, query child candidates using the read-only `inspect` hook below (or use Android Studio Database Inspector, `mangas` table, as a fallback). Never use virtual/merged IDs for these inputs.
- First install/launch the original baseline APK and record A01. Then install the patched APK with `adb install -r PATH_TO_SPIKE001_APK` and record its SHA-256. Both APKs use package `app.mihon.tachiyomiat.dev`.

## Find real manga IDs without Android Studio

Once the same work is saved in the library from **two different real sources**, run the read-only hook on the **patched debug APK**:

```bash
adb shell am start -n app.mihon.tachiyomiat.dev/eu.kanade.tachiyomi.polaris.Spike001DebugActivity \
  --es operation inspect --es title_filter "One Piece"
adb logcat -d -s PolarisSpike001:I
```

Replace `One Piece` with the work's title or a distinctive substring. Omit `--es title_filter ...` to see the first 50 saved, non-merged library entries; use `--ei limit 100` for more (maximum 200). Each line reports **childId**, **sourceId**, and **chapters** only; titles, URLs and cookies are not logged. The same title filter may match aliases differently between sources, so inspect again without the filter if only one candidate appears. Select two IDs belonging to **different** source IDs with chapter counts greater than zero. Do not infer real source availability solely from those rows.

This inspect command is part of the Spike-001 **debug-only** hook. It is not a product feature and is not evidence that B01/B02/B03 passed.

## Create the test work

```bash
adb shell am start -n app.mihon.tachiyomiat.dev/eu.kanade.tachiyomi.polaris.Spike001DebugActivity \
  --es operation create --el child_a CHILD_A --el child_b CHILD_B
adb logcat -d -s PolarisSpike001:I
```

The hook validates distinct source IDs and populated chapter lists, calls the existing `CreateMergedManga`, and logs the real children, sources, counts and virtual merge ID. For this test work only, it sets the existing `CHAPTER_SORT_NO_DEDUPE` setting so both overlapping source lists are visible. The production/default priority policy is unchanged.

Open the new library entry. Capture the combined list (B01), open a real chapter from A and then B through that entry, and verify the expected source content/page loader for each (B02). Record chapter IDs, child manga IDs, source IDs/names, work, extension versions, device/API, APK SHA-256, screenshots and logcat. Merely creating the row or constructing a Reader intent is insufficient for B02 PASS.

## Remove one reference

```bash
adb shell am start -n app.mihon.tachiyomiat.dev/eu.kanade.tachiyomi.polaris.Spike001DebugActivity \
  --es operation remove --el merge_id MERGE_ID --el child_id CHILD_A
adb logcat -d -s PolarisSpike001:I
```

The hook uses `DeleteMergedManga.deleteReference`, asserts the virtual parent survives and the remaining list excludes the removed child. Reopen the entry and a chapter from B; capture evidence (B03). It preserves the real child manga row.

Issue #2 remains open until these device checks pass. A host SQLite test, successful Gradle build or debug hook output does not certify reader runtime acceptance. Migration 15 remains prohibited until this gate passes.
