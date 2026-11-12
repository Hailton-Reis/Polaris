# Polaris R001 — protobuf backup candidate (issue #11)

**Candidate only. Not applied to the Android app. No change to migration 14/15.**
Pinned baseline: `kiritsuguxs/yomotsu@0fb80c439ef816eeb50674f1b90af39918b176d8`.
Pinned `Backup.kt` Git blob: `0c021d34a8426dc0bd5844b4e00f9c13767610bf`.

## What was implemented

- `BackupPolarisBundle.kt`: concrete `@Serializable` Kotlin message classes for **versioned** Polaris backup payload. It contains explicit canonical works, real source+URL links with five merge flags, optional stable UUID, root settings and **supplemental full `BackupManga`** objects for source children absent from Yomotsu's regular backup selection. No local `manga_id` is persisted as portable identity.
- `validateForImport()`: checks version, duplicate keys, duplicate/malformed links, root flags, source 6969 exclusion, missing names, redundant/cross-work extra snapshots. Restore must call before any database modifications.
- `Backup.pinned.kt`: exact pinned Yomotsu model fixture (Git blob hash above).
- `apply_backup_proto_candidate.py`: a **fail-closed, output-only** patch generator. It checks exact pinned blob SHA and unique SQL-independent anchor, then creates a **new output directory** holding patched `Backup.kt` with `@ProtoNumber(107) var polaris: BackupPolarisBundle? = null` and the new Kotlin DTO. It will not overwrite any existing directory or modify the input checkout.
- `test_proto_apply.py`: 7 unit cases exercising exact provenance, field numbers, output-only changes, drift rejection, missing model and repeated runs.
- `host-tests/`, `run_model_validation.sh`: isolated Kotlin compilation with **fake annotations and fake BackupManga**, followed by 18 fail-closed validation cases. These doubles are *not* real kotlinx.protobuf runtime.

The pinned top-level Yomotsu protobuf numbers `1,2,101,104,105,106` remain unchanged; `107` is **proposed**, subject to Android library/collision validation. The ordinary pre-Polaris backup leaves nullable `polaris` absent.

## Reproduce the staging

```bash
python3 -m unittest discover -s spikes/spike001/backup/proto-candidate -p 'test_proto_apply.py' -v
python3 spikes/spike001/backup/proto-candidate/apply_backup_proto_candidate.py \
    --pinned-backup /path/to/pinned/Yomotsu/app/src/main/java/eu/kanade/tachiyomi/data/backup/models/Backup.kt \
    --output-dir /tmp/polaris-backup-proto-new-output
bash spikes/spike001/backup/proto-candidate/run_model_validation.sh
```

**Tested in host environment (2026-10-11):**
- **7/7** Python fail-closed staging assertions PASSED.
- **18/18** Kotlin DTO validation assertions PASSED; compiled with Kotlin 1.9 and **stubs**, not the real kotlinx.serialization plugin.
- **12/12** separate Python `google.protobuf` (6.33.6) dynamic schema/wire tests PASSED. These tested protobuf field layout, UTF-8/source IDs including negative signed IDs, old→new and new→old decoding, child snapshot bytes and gzip framing; **not the real Yomotsu Kotlin serializer**.
- Total: **37 individual host candidate checks**, separate from the previously configured **207** main host-gate minimum. No 207/207 claim.

A complete portable evidence ZIP includes `test_wire_compact.py`, a longer reference `test_backup_wire_candidate.py`, Python/Kotlin logs, manifest, exact source snapshots and generated output:
[Google Drive — protobuf backup candidate evidence](https://drive.google.com/file/d/1dicLCIZXa-DJWW8OaR8J852fryD6Qpdx/view?usp=drivesdk).
SHA-256: `704b3f3f261a576821744baca27babdd0b6638b0d0d9d02ed73c385063cb3bd5`.

## Remaining work — DO NOT treat this as production restore

1. Compile `BackupPolarisBundle.kt` using Yomotsu's **actual kotlinx.serialization plugin and ProtoBuf runtime**. Generate a compressed `.tachibk` and verify real original/extended decoding and golden bytes; synthetic Python wire layouts alone are insufficient.
2. Connect `MergedBackupExportPlanner` to actual `BackupCreator`, ensuring all extra nonfavorite real children are serialized by `MangaBackupCreator` with the user's selected `BackupOptions`. Call validation **before** writing ZIP/GZIP, and never produce an incomplete successful backup on a missing real child.
3. Restore normal + supplemental `BackupManga` records **first** through `MangaRestorer`; await completion, map sourceId+URL to new local IDs, then transactionally restore the virtual work and explicit associations. No guessed links, no synthetic parent chapter rows. An orphaned child with no extension stays pending.
4. Supply durable archive identity / restore ledger to ensure retry and multiple archives do not create multiple virtual parents; link priority and intentional unlink preserved.
5. Android SQLDelight/runtime baseline B01–B05 (#2), real backup roundtrip and old backup compatibility must pass before #11 is closed. PR #1 stays DRAFT and migration 15 BLOCKED.

**Source-code provenance:** the application backup generator/reader has *not* been modified by this candidate; these files are deliberately staged outside `spikes/spike001/new-files` and outside the current `apply_spike001.py`.

## 2026-10-12: verified snapshot completeness bridge (new)

**New files:** `BackupPolarisBundleBuilder.kt` and `host-tests/BackupPolarisBundleBuilderTest.kt`. The DTO `BackupPolarisBundle.kt` has two additions: `BackupPolarisLink.isPending` (optional link tag 5, default false), and `validateSnapshotCoverage(ordinaryManga: List<BackupManga>)`.

This fixes an integrity blind spot in the initial candidate format: previously, it could record links for a resolved real manga without verifying that a normal or supplemental `BackupManga` record existed. Such an archive could look valid while silently losing that child's chapters/progress.

The builder now receives the existing `MergedBackupExportPlan`, explicit current virtual parent/child links, the persisted real child catalog, regular Yomotsu `BackupManga` snapshots and supplementary `BackupManga` snapshots. It checks that:
- the supplement is an **exact source-ID+URL set match** for `additionalRealChildMangaIds`; no duplicates, missing or extraneous snapshots;
- no manga snapshot appears in both sections; all **resolved** child links are covered by one section;
- only explicitly `manga_id=NULL` links are `isPending=true` and can lack a manga snapshot; pending/resolved status is **per link**, not a global source key;
- no link/title/settings or archive parent identity changed between the export plan and serializing the protobuf DTO.

The future application caller must use Yomotsu `MangaRepository.getMangaById(id)` to load the additional persisted real children, then **the existing `MangaBackupCreator(additionalMangas, options)`** to produce full snapshots respecting the same backup options. The candidate builder does not fetch DB rows or serialize itself, and will throw if caller provides incomplete snapshots. This logic must execute before the app returns any successful backup.

Validation:
```bash
bash spikes/spike001/backup/proto-candidate/run_model_validation.sh
```
**18/18** old DTO Kotlin checks + **16/16** new builder checks PASS, compiled against explicit serialization and BackupManga stubs (not actual ProtoBuf). In this checkpoint, the older separate 24/24 restore and 20/20 export Kotlin checks, plus 7/7 pinned-apply Python checks, were rerun: **85 isolated host checks PASS**, not a unified five-stage gate. `spikes/domain-lab/build.gradle.kts` now requires both protobuf host test mains as tasks of `checkSpikes`. No actual Gradle task, Kotlin protobuf wire serialization, APK or on-device restore has run.

[Evidence ZIP](https://drive.google.com/file/d/1FuHz10bYD-4-ZfS4-yE9Dq6RQzMaXOac/view) SHA256 `5bec9bf2e3cf5dd5abccffee884a1bc67e2ca8e607dc9d98d9149523788f8998`. The newer [12/10 handoff](../../../../docs/r001/RESUME_2026_10_12.md) supersedes the older progress count. Do not apply the candidate to production before issue #2 gates and real Kotlin serializer tests.

## 2026-10-17 — backup field 107, pending-only and duplicate parent fail-closed

Three concrete staging errors corrected: `BackupCreator.staged.kt` wrote
`Backup.polaris` while `Backup.staged.kt` defined `polarisBundle`
and `BackupRestorer.staged.kt` read `backup.polarisBundle`. Both now
use the same `polaris` property as the existing 107-tag patcher.
`BackupPolarisBundle` now forbids supplemental full-manga snapshots
if ALL associated source links are pending. A shared source remains
eligible when at least one parent has a resolved link.

Critically, `BackupPolarisBundle.validateSnapshotCoverage` fails closed
when an archive contains both actual Polaris virtual works and ordinary
Yomotsu backup mangas with `source=6969`, which would otherwise
create two different virtual parent rows on import. This is a P0
incompatibility with the current staged exporter: **do not bypass**.
Complete portable parent metadata preservation and duplicate-free
restoration before enabling Android export/import.

New `backup-proto-contract` host gate compiles the staged
`Backup.staged.kt`, real portable DTO and requires four unique
success markers with minima 18+19+9+5 = **51**. It runs via
`bash spikes/spike001/backup/proto-candidate/run_model_validation.sh`.
CI also checks the six cross-file field-107 contracts in Python.

Locally executed **32/32** DTO/staged field tests, **53/53** strict
restore, **41/41** atomic port and **16/16** SQLite = 142 distinct
host test cases across four suites, plus **7/7** pinned proto staging
Python cases; all PASS. The builder's 19 tests are configured but
not rerun here. The 13-stage **configured** host minimum is
**537**, not an executed full gate. No actual ProtoBuf or Android
Gradle SQLDelight codegen.

[Evidence ZIP](https://drive.google.com/file/d/164HHr-yLvfW9Br24WNISJyDDQsULA4Bj/view):
SHA256 `2d525668bca17556211bc8d6cc554add4b10d3d405bc49f12133bd44d6a53c09`.
No production migrations or file writes to a user's Android data.
