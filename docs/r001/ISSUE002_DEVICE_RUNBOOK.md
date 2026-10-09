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

## Validate refreshing a virtual work (supplemental B04)
With two real children already loaded, refresh the merged work from its own manga screen. The patched `MangaViewModel` must enumerate linked children with `MergedRefreshTargets` and call Yomotsu `UpdateMangaFromRemote` against each real child's `mangaId/source` — **never** `MergedSource.getMangaUpdate`. Record which source requests succeed, the updated real chapter counts, and the merged Flow list. Repeat with one source offline/challenged and ensure the second still refreshes; record the error, do not attempt a Cloudflare bypass. Verify no downloads are created using `merged://...` as a file or manga identity. The offline host test cannot establish this Android behavior.

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

## B01/B02/B03 reproducible evidence snapshots

The short ADB evidence command below collects Android API/ABI/fingerprint, APK SHA-256, a screenshot, and filtered Polaris/crash logcat. It never alters app state, captures no passwords/cookies intentionally, never overwrites an existing nonempty evidence directory, and always marks the result CAPTURED_UNVERIFIED. Review screenshots before sharing; they may contain user data or copyrighted page content. Do **not** commit unreviewed raw logcat or screenshots.

After the debug hook reports the real child IDs and virtual parent ID, open the **merged chapter list** and take the first snapshot:

```bash
python3 scripts/r001/capture_issue002_device_evidence.py B01   --apk /path/to/spike001-debug.apk --child-a CHILD_A --child-b CHILD_B   --merge-id MERGE_ID --out /path/to/evidence/B01
```

Open a real chapter from child A and then child B, wait until the actual page contents load, and capture each:

```bash
python3 scripts/r001/capture_issue002_device_evidence.py B02A   --apk /path/to/spike001-debug.apk --child-a CHILD_A --child-b CHILD_B   --merge-id MERGE_ID --out /path/to/evidence/B02A
python3 scripts/r001/capture_issue002_device_evidence.py B02B   --apk /path/to/spike001-debug.apk --child-a CHILD_A --child-b CHILD_B   --merge-id MERGE_ID --out /path/to/evidence/B02B
```

Then remove child A using the debug hook above, reopen child B's chapter via the virtual library entry and capture B03:

```bash
python3 scripts/r001/capture_issue002_device_evidence.py B03   --apk /path/to/spike001-debug.apk --child-a CHILD_A --child-b CHILD_B   --merge-id MERGE_ID --out /path/to/evidence/B03
```

For multiple connected devices add `--serial DEVICE_SERIAL`. Results are local files, one directory per phase; each `evidence.json` deliberately remains `runtime_verdict: CAPTURED_UNVERIFIED`. A reviewer still must establish source identity and chapter content independently before recording B01/B02A/B02B/B03 PASS. Use brief logcat/screenshot captures to avoid prolonged ADB sessions in unstable emulators.

## Debug hook privilege boundary

The exported development-only `Spike001DebugActivity` requires `android.permission.DUMP` in the generated **debug** manifest. This is intended to restrict launches to privileged diagnostic callers such as an appropriately authorized ADB shell; ordinary third-party apps must not be able to invoke its create/remove operations. Release manifests remain unmodified. Confirm on the target Android image that `adb shell am start ... --es operation inspect` is permitted; if it fails with `Permission Denial`, record that as a test-harness compatibility issue and use an authorized debug/instrumentation route rather than removing the privilege boundary. The actual Android permission behavior is not yet runtime-tested.


## B04 fault isolation observations

The virtual-work refresh now uses `MergedRefreshCoordinator` to enumerate unique linked real child manga IDs and submit a Yomotsu `UpdateMangaFromRemote` request for each in turn. For B04, record the real child `mangaId` and source ID for each request, verify the merged list updates through Flow after real child synchronization, and repeat with the first source unavailable to verify the second is still attempted. When all real child requests fail, the UI should show a refresh error. Cancellation must stop additional attempts. The diagnostic code and 22 host tests do **not** establish this UI/network behavior without an Android emulator/device.


## Read-only reader-source diagnostic (B02 preparation)

The updated debug hook supports `operation=route`. For a **real** chapter ID shown under the virtual work, it verifies that the chapter's child manga is linked to that particular merged parent, that the original source extension is currently installed, and which reader kind (`IMAGE` versus `NOVEL`) should be used. It rejects an unrelated chapter ID, a removed reference, a nested virtual child, or a missing source. It does **not** fetch any page, launch the reader, or count as B02 PASS.

```bash
# Replace IDs with values from operation=inspect / operation=create:
adb shell am start -n app.mihon.tachiyomiat.dev/eu.kanade.tachiyomi.polaris.Spike001DebugActivity \
  --es operation route --el merge_id MERGE_ID --el chapter_id REAL_CHAPTER_ID
adb logcat -d -s PolarisSpike001:I
```

Run it once for Source A and again for Source B before opening both chapters through the **real app UI**. The production `MangaScreen` now resolves the real child source for virtual chapters before choosing `ReaderActivity` versus `NovelReaderActivity`. For normal manga, it retains Yomotsu's original reader routing. If the child extension is not installed, the UI reports the missing source instead of launching the wrong reader type. **Runtime proof is still required**, and `android.permission.DUMP` on the debug-only hook requires an authorized ADB shell.


## Database backend follow-up (no migration 15)

Before checking real parent/child records, verify the app actually uses the pinned Yomotsu `AndroidxSqliteDriver(driver=BundledSQLiteDriver())` with FK constraints enabled, **not** the Android framework's SQLite 3.32 on API31. The original pinned Yomotsu itself uses SQL `RETURNING`, so its bundled driver is relevant. Save the real runtime SQLite version and FK status as part of Android acceptance; the host SQL preflight only checks this configuration statically.

Host migration integrity suite: `python3 -m unittest discover -s spikes/spike001/host-sqlite -p 'test_*.py' -v` (10/10 PASS locally on exact staged SQL). It does not certify real Android SQLDelight queries. The complete deletion of a virtual work (not single-child unlink) needs explicit follow-up under issue #8; do not assume deleting all references also removed the virtual parent.


## New background-worker safety regression (2026-10-09)

Pinned Yomotsu normally includes all library favorites in `LibraryUpdateJob` and `MetadataUpdateJob`. During R001, virtual merged parents are now **excluded by source ID** from these background queues. Ordinary real-source library entries should continue refreshing as usual. Test that scheduled library updates do not invoke `getMangaUpdate` or schedule downloads for virtual parent source `MERGED_SOURCE_ID`, while existing real-source update notifications still work.

**Known intentional limitation:** A virtual title alone in the library will not get its real child variants automatically refreshed by the regular Yomotsu scheduled updater until the source-aware planner of issue #5 is integrated; manual refresh of the merged detail screen follows linked child IDs. This safety restriction should not be described as complete automatic multi-source refresh functionality.

The Android build preflight now verifies both worker patches in the pristine pinned and staged patched checkout. This is static contract verification, not the actual library-update runtime acceptance.
