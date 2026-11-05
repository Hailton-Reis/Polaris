# Polaris R001 — category-name integrity for v2 restore (2026-10-20)

Status: HOST CANDIDATE ONLY. Original Yomotsu SHA 0fb80c439ef816eeb50674f1b90af39918b176d8. Branch r001/multisource-foundation, PR #1 Draft.

## Confirmed problem
Pinned Yomotsu `categories.sq` defines `_id`, `name`, `sort`, `flags`, with no UNIQUE constraint on `name`. `BackupManga.categories` references `BackupCategory.order`, not the eventual on-device category ID. The staged full-parent Kotlin adapter only verified category IDs were positive; an existing, but renamed/unrelated category could be silently assigned to a restored virtual parent, while all foreign keys and existing readback checks still passed.

## Candidate fix
`SqlDelightPolarisFreshParentAdapter.FreshWork.archiveCategories` now requires exact `BackupCategory` snapshots from the SAME decoded backup. For every category order used by the work, the adapter checks before any writes that:
- the archive category `order` set equals backup work orders and destination ID-map keys, with no duplicate or extraneous entries;
- archive category names are nonblank and unambiguous;
- the original pinned `selectPolarisRestoreCategoryCandidates(name)` query returns **exactly one** destination ID, equal to the ID selected for that archive order.
A name mismatch, rename, missing/extra source snapshot, ambiguous local name or wrong ID aborts the entire parent batch. The adapter does not rename/edit local categories; it preserves existing category names and flags. Integration MUST pass trusted BackupCategory snapshots from the decoded backup and not reconstruct them from destination IDs.

## Executed evidence
- 38/38 Kotlin/JVM behavior tests PASS (10 added), compiling the changed Kotlin adapter against API-shape **host stubs**.
- 26/26 Python SQL/source contract tests PASS (4 added), including an executable SQLite regression confirming the original categories schema permits duplicate names.
- Combined `bash adapter/run_host_contract.sh` PASS: `POLARIS_GENERATED_QUERY_BRIDGE_PASS 64`, no skipped tests.
- New configured gate minimum: 64 instead of 50, **1,167 tests across 24 configured gates**, NOT a full aggregate/CI/Android PASS.

## Remaining release blockers
Generated SQLDelight 2.3.2 code has NOT been compiled with the actual Android build; actual BackupCategory serialization/ProtoBuf, category manager lifecycle, true archive digest computation, migration reviewed for UUID ledger, existing-parent/replay and Android B01–B05 remain open. CI workflows have recently reported failures with 0 executed job steps (no source compilation result).

No production SQLite database or migration14/15 changed. PolarisRestoreCoordinator v2 preflight stays fail-closed, PR #1 Draft, issue #11 OPEN.