# Spike-001 actual Kotlin domain-contract tests (host-only)

Run `bash scripts/r001/test_spike001_host.sh` with a Kotlin JVM installation that includes `kotlinx-coroutines-core-jvm.jar` (e.g. SDKMAN Kotlin) and JDK 21.

The script compiles **the real staged** `GetMergedChaptersByMangaId.kt` and `MergedMangaReference.kt`, together with minimal API contract stubs located in this directory. It does not copy or rewrite the two production classes.

Eight host tests assert: combined chapters belong to both real child IDs, reader argument pairs retain their real child manga IDs, priority dedupe, highest-chapter mode, removal of a reference, nullable/orphan reference handling, live Flow updates after removal, and an empty result with no children.

The fixtures are stand-ins for Yomotsu repositories and coroutines collect flows on the JVM. Results **do not certify** SQLDelight, actual extensions, Android Activity launches, fetched pages or B01/B02/B03 runtime acceptance. Migration 15 must not be applied until the real Android gate passes.

The tested Kotlin files are byte-for-byte the real repository sources: `GetMergedChaptersByMangaId.kt`, `MergedMangaReference.kt`, and `InternalSourceIds.kt`. All three compile from the staged production paths; fake classes are restricted to API stand-ins for `Chapter`, `ChapterRepository`, and `MangaMergeRepository`. The test intentionally does not replace these production functions with simulated versions.

Validation on 2026-10-08: 8/8 PASS using JDK 21 + kotlinc 1.9.0 and the installed kotlinx-coroutines JVM jar. It is host-domain proof only, and neither live Android UI nor source extension/network proof.


## CI integration

The domain-spikes GitHub workflow also invokes an isolated Gradle/Kotlin 2.4.10 host lab:

```bash
gradle -p spikes/spike001/host-lab checkHost --no-daemon --stacktrace
```

The lab uses Kotlin/JVM 2.4.10, JDK21 and kotlinx-coroutines 1.10.2 to compile the real staged Kotlin sources (including `InternalSourceIds.kt`) plus the host-only repository contracts. This Gradle path is committed but **not verified in a CI runner yet** because existing GitHub Actions jobs are failing before any runner step executes. The manual `kotlinc` path passed 12 scenarios locally.


## Additional refresh fault-tolerance scenarios (2026-10-08)

The real staged `MergedRefreshCoordinator.kt` is now compiled by both host runners. Six added host cases test: two successful child refreshes, recovery after a failed first source, all-source failure with last exception propagated, prompt cancellation without subsequent requests, rejection of cross-work/orphan/virtual references, and rejection of an empty merge. The complete **22/22 JVM host tests passed locally** using JDK21, Kotlin 1.9.0, the system coroutine jar and exact staged Kotlin production source files. This does not verify Android APK source fetches.


## 2026-10-08 extension — real virtual-work lifecycle (26 host scenarios)

Added four tests that instantiate the actual staged `CreateMergedManga`, `GetMergedChaptersByMangaId` and `DeleteMergedManga` classes together. Fake `MangaRepository`, `MangaMergeRepository` and `ChapterRepository` boundaries are deliberately in-memory; the production interactor implementations are compiled directly from their unmodified staging paths. The tests verify root + two real references, real source ID preservation, duplicate creation idempotence, one-child reference deletion without losing parent or other source, and rejection of only one distinct child.

**26/26** host Kotlin scenarios PASS on JDK21/kotlinc1.9 + installed coroutines JAR. Production `CreateMergedManga.kt` and `DeleteMergedManga.kt` Git blobs were compared to the checked-in source: `b049cf1613918ed817bbb4e3b4c13bc439263b5b` and `0ff4c41e757cc510044cdfadc22a968dd2ca50d8`. The four new tests are **host data-contract proof only**, not actual SQLDelight/Android B01/B03 acceptance.

The Gradle host lab additionally compiles only those two interactor files from the directory by excluding the four unrelated production interactors that would require further real repository interfaces. Gradle CI runner execution is still unverified.


## Recovery from an interrupted first insert

The real `CreateMergedManga` inserts the virtual parent before writing its reference transaction. A failed reference insert can therefore leave an orphan parent. The original implementation incorrectly returned this empty parent on the next call. The updated interactor only returns an existing parent directly if there is **at least one** saved reference. If none exist, it uses that same parent to retry the references, without resurrecting a deliberately removed individual child when some references remain.

The defect was first reproduced against the original production source using an injected repository failure (test **FAILED** as expected), then the byte-identical updated production source was compiled using kotlinc1.9/JDK21 and passed **3 focused checks**. The full host suite has two additional corresponding tests staged, now **28 definitions**; it still needs a full rerun before counting all 28 as PASS.


## Guard against malformed virtual children

The staged real `CreateMergedManga.kt` now validates that all children have a **real**, non-`MERGED_SOURCE_ID` source and that the child selection spans at least two distinct real source IDs. This is consistent with the existing debug B01 creation gate. Invalid nested merge and same-source inputs are rejected before `insertNetworkManga` can create the virtual parent.

Focused host Kotlin proof on the exact staged production file: **5/5 PASS** (orphan recovery, idempotence, intentional unlink, same-source rejection, nested-merge rejection). Two new scenarios were added to the combined Kotlin host test, increasing committed definitions to **30**. **This does not establish a 30/30 complete host run**; last complete validated combined Kotlin run had 26 scenarios. Run `bash scripts/r001/test_spike001_host.sh` in a fully provisioned checkout.
