# R001 — Yomotsu BackupCreator integration candidate (issue #11)

**Status: non-production, not installed into Spike-001 or Android.**
Baseline is strictly `kiritsuguxs/yomotsu@0fb80c439ef816eeb50674f1b90af39918b176d8`; original upstream `BackupCreator.kt` blob `98036c09002b6058a36520a82ac889fbaa9e93cb`.

## Source-aware exporter implemented

`PolarisYomotsuBackupExporter.collect(ordinary: List<Manga>, ordinarySnapshots: List<BackupManga>, options: BackupOptions)` uses actual pinned Yomotsu-style contracts:
- `MangaRepository.getMangaById`, `MangaMergeRepository.getReferencesById`, `YomotsuMergedWorkUuidStore.ensureDistinct`;
- the staged `MergedBackupExportPlanner` and `BackupPolarisBundleBuilder`;
- `MangaBackupCreator` with **the same `BackupOptions`** as the ordinary backup. The real Yomotsu creator is responsible for chapters, categories, history and tracking; **nothing is copied onto virtual parent chapters**.

Selected source-6969 favorites become portable works identified by persisted canonical UUIDs. The exporter verifies exactly one root reference per virtual parent, that root's own source+URL, resolved child IDs against real source+URL and positive local IDs, and flags/priorities. A NULL-manga child stays explicitly pending. A nonfavorite real child that is absent from the normal selected list is exported once as a supplemental `BackupManga`; children shared by multiple parents are deduplicated. When no virtual parent is selected or `libraryEntries=false`, optional Polaris payload is absent.

**Fail closed under concurrent changes:** the exporter rereads the parent and its source references after `MangaBackupCreator` completes, then delegates to the builder's complete link snapshot comparison. A deleted/resolved/pending changed link, title, UUID, or source identity aborts the candidate backup. This is NOT an atomic DB snapshot: an adversarial/concurrent writer can race after final readback; no production guarantee without SQLDelight transaction/CAS and issue #10 resolution.

## Pinned Yomotsu BackupCreator.kt candidate

- `BackupCreator.pinned.kt`: exact upstream source.
- `BackupCreator.staged.kt`: proposed source-level integration. Passes ordinary selected manga and their `BackupManga` rows to the new exporter, sets `Backup.polaris` (the independently staged optional top-level protobuf tag 107), and includes supplemental child mangas in `backupSources`.
- `apply_backup_creator_candidate.py`: SHA-gated, output-only patch regeneration. Accepts **only** the pinned Git blob, uses unique anchors, and refuses to overwrite the destination.
- `test_creator_stage.py`: **10 Python staging tests are configured** for exact provenance/reproducibility and safety; these tests are in GitHub Actions but **were not locally executed as a suite** in this checkpoint.

**Important additional safety correction:** Yomotsu originally deleted older auto-backups before creating/validating the new one. The staged variant defers pruning (keep four most recent files, including the new one) until after writing and validating the new file. For a non-null Polaris bundle, `BackupFileValidator` exceptions are **not swallowed**; failures abort and delete the incomplete new file. Legacy backups retain the pinned app's warning behavior. The candidate validator does not prove the new protobuf field is understood by Yomotsu; that must be tested with real runtime.

To reproduce the staged file (requires Python 3 and the pinned fixture):
```bash
python3 -m unittest discover -s spikes/spike001/backup/yomotsu-candidate -p 'test_creator_stage.py' -v
python3 spikes/spike001/backup/yomotsu-candidate/apply_backup_creator_candidate.py \
  --pinned spikes/spike001/backup/yomotsu-candidate/BackupCreator.pinned.kt \
  --output /tmp/your-existing-clean-dir/BackupCreator.kt
```

## Verified locally

```bash
bash spikes/spike001/backup/yomotsu-candidate/run_tests.sh
```

With local `kotlinc` + JDK21, the **12/12** exporter host tests passed: nonfavorite chapter snapshot selection, no duplicate snapshots, option forwarding, two parents sharing children, explicitly pending source links, invalid root/source, source mutation during serialization, virtual title mutation, disabled library entries, absence of virtual works and durable UUID creation. Exact source and runner Git blob hashes were checked for 16 source files.

[Evidence ZIP in the Polaris Drive project](https://drive.google.com/file/d/1_L5Xw5NEcEseNVoTcccx2RIlIWyvGvhH/view), SHA-256 `9006b19e3a3c47652968554f17ae06faa4050454081421fe141bb318f8ddfe6f`.

`scripts/r001/run_host_gate.py` now includes the **sixth** fail-closed gate `backup-adapter` (minimum 12), giving configured minimum **240** (72 Python, 36 original SQLite, 38 main Kotlin, 17 backup SQLite, 65 backup Kotlin, 12 adapter Kotlin). No full 240-case run was executed. CI invokes the pinned Python staging test and Kotlin adapter runner, but GitHub runners must actually start.

**Unfinished and release blocking:** real Android DI registration for `MangaMergeRepository`; copy compiled candidate files into real Android source sets; Kotlin `ProtoBuf` tag107 real encode/decode; implement **restore-first** handling of normal+supplementary child chapters and identity-safe, transactional virtual-parent links; test legacy backup. Beware pinned `BackupRestorer.restoreManga()` catches some per-row failures, so an actual Polaris restorer must propagate failed child restore instead of considering it success. The current staging includes an export adapter **only**: no working full backup/restore round trip, no APK/B01-B05 gate, no production migration 15 change.

Keep PR #1 draft and issues #2, #10, #11 open.
