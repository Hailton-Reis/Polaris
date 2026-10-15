# Polaris R001 — stable merged work UUID without migration 15

Status: **staged candidate, host-only**. The Kotlin source has been compiled
and tested, but it has **not** been installed in Yomotsu, SQLDelight-generated
Kotlin or an Android app. The underlying issue #11 remains P0 OPEN.

## Proven pinned Yomotsu integration points

Pinned upstream: `kiritsuguxs/yomotsu@0fb80c439ef816eeb50674f1b90af39918b176d8`.

- `tachiyomi.domain.manga.model.Manga.memo: JsonObject`, a persistent JSON memo
  already saved by `MangaBackupCreator.toBackupManga()` and decoded by
  `BackupManga.getMangaImpl()`.
- `tachiyomi.domain.manga.model.MangaUpdate(id: Long, memo: JsonObject?)`.
- `tachiyomi.domain.manga.repository.MangaRepository.update(update): Boolean`,
  `getMangaById(id): Manga`.
- Existing virtual source ID `6969` in staged Spike-001.

No new database table or migration is needed just to persist a UUID:
`mangas.memo["polaris.merge.work.uuid"]` stores one canonical UUID string.

## Implemented API

`YomotsuMergedWorkUuidStore` has three suspend methods:

- **`ensure(parentId)`**: return a canonical UUID already stored for this
  source-6969 parent, otherwise generate one and save it using the actual pinned
  repository API shape; reread the saved row, fail closed if the update failed
  or a concurrent writer changed it. This is for preparing backups.
- **`ensureDistinct(parentIds)`**: reject repeated parent IDs or UUIDs shared by
  two different virtual works. Use the resulting ID→UUID map for
  `ExportVirtualWork.archiveWorkKey` and `canonicalUuid`; NEVER use
  `merged://<local IDs>` to identify a parent across devices.
- **`assignArchived(parentId, archivedUuid)`**: on restore, place exactly the
  UUID from the backup on an explicitly verified new virtual parent; if the
  parent already has another UUID, **abort instead of overwriting**; repeated
  restore of the same UUID does not write twice. Also checks canonical text,
  source 6969, return status and readback.

Both methods preserve other JSON memo keys; malformed typed memo or
noncanonical UUIDs cause a hard failure, not silent replacement. The code
takes a UUID generator dependency for deterministic tests.

**Integration sequence, NOT yet implemented:**
1. Export: before serializing, call `ensureDistinct` for every favorite virtual
   parent and set `archiveWorkKey = canonicalUuid` in the portable export plan.
   Build the existing `BackupPolarisBundle`, including **nonfavorite real child
   snapshots** and exact source+URL references. Abort if any resolved child
   snapshot is missing.
2. Import: validate whole archive before writing. Restore original plus
   supplemental `BackupManga` rows using real `MangaRestorer` and **await**
   completion. Find/create a verified virtual parent using a durable UUID
   lookup/ledger and then call `assignArchived` on that parent; only then
   transactionally restore exact child/root references and pending-source
   placeholders. Never guess parents/children by manga title.
3. Ensure retry and concurrently opened backups cannot create duplicate
   virtual parents, ideally enforcing UUID uniqueness and link uniqueness via
   a tested transactional/SQLDelight solution. Existing `mangas.memo` does
   **not** impose a UNIQUE constraint or atomic compare-and-swap.
4. Check persisted UUID survives actual Yomotsu protobuf, old backups, full
   real chapter state and device migration. Keep issue #2 B01–B05 Android
   gate and issue #10 DB uniqueness open until runtime proof.

## Verification

```bash
bash spikes/spike001/backup/uuid-candidate/run_uuid_host.sh
bash spikes/spike001/backup/run_tests.sh
```

Using **exact SHA-verified committed source files**, the host test suite
compiled under `kotlinc 1.9.0 / JDK 21` and passed:

- **21/21** UUID-specific Kotlin regression cases;
- **24/24** existing portable backup restore;
- **20/20** existing portable backup export;
- **65/65** combined Kotlin host backup tests, one successful
  `run_tests.sh` command.

`spikes/domain-lab/build.gradle.kts` also registers `spike001UuidStore` as a
dependency of `checkSpikes`, but there is **no successful Gradle CI/Android
build proof**. The six host test doubles have the Yomotsu API's source shape
and `JsonObject` operators, **not the real Android repository or
`kotlinx.serialization.json` runtime**.

The fail-closed project runner `scripts/r001/run_host_gate.py` now requires
**65** Kotlin backup tests and three distinct success markers; minimum full
five-stage R001 threshold is **72 Python + 36 SQLite + 38 core Kotlin +
17 backup SQLite + 65 backup Kotlin = 228**. Only the **65 Kotlin backup**
checks were run together at this checkpoint; never report the whole
228-check gate as PASS.

Evidence: [Polaris R001 UUID identity ZIP](https://drive.google.com/file/d/1KyLLuGPBziDX4hMbudXEpE5pLlDua0Li/view),
SHA-256 `e057ed04c44b9325072c6a329874bd5feb678264afc411ce5a8bacd5809ac303`.
The ZIP includes a JSON provenance manifest with source file Git blob SHAs,
run logs, scope and non-Android limitations.

**Not changed:** migration 14/15, production `BackupCreator`,
`BackupRestorer`, `merged.sq`, draft PR #1 status and real APK.
