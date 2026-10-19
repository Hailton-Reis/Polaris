# Polaris R001 — field-complete SQLDelight queries and verified pinned trigger blocker

**Date:** 2026-10-19. **STAGING ONLY — NOT A DEPLOYABLE RESTORER.**
**Parent issues:** #2 (Android runtime), #11 (lossless v2 backup).
**Pinned base:** Yomotsu `0fb80c439ef816eeb50674f1b90af39918b176d8`.
**Polaris baseline:** existing Spike-001 `merged.sq` and migration14 remain unchanged.

## Implemented now

Created `spikes/spike001/backup/restore-candidate/parent-sqldelight-fields/`:
- `PolarisParentMetadataRestore.sq`: named candidate SQLDelight read queries for complete physical parent manga, real source candidates, exact categories, chapters, history, tracking, excluded scanlators and merge edges; explicit full-column INSERT for mangas and chapters, plus exact INSERT statements for history, tracking, categories, exclusions.
- `pinned_update_triggers.sql`: host copy of relevant *existing upstream Yomotsu* UPDATE and category triggers, with exact names and logic transcribed from the pinned commit. **These triggers are not newly proposed app migrations.**
- `test_parent_sqldelight_fields.py`: 35 executable Python/SQLite host regressions, executing SQL statements parsed from the new candidate .sq on the native-shaped fixture with **Polaris migration14, additive candidate UUID ledger and original-style pinned update triggers**.
- `run_tests.sh`, README and downloaded evidence logs.

This is materially closer to real Yomotsu SQLDelight schema than the earlier synthetic payload prototype, but **the candidate .sq file has NOT been installed in the Android data module or compiled through SQLDelight codegen**. The existing production SQLDelight adapter of full-parent metadata is still missing.

## Confirmed incompatibility — exact timestamp and version replay

The upstream `mangas.sq` defines `update_last_modified_at_mangas`, `update_manga_version` and `update_last_favorited_at_mangas`. `mangas_categories.sq` inserts trigger an UPDATE of `mangas.version` when `is_syncing=0`, and `chapters.sq` defines chapter UPDATE timestamps/version tracking.

The new host test proves all three important conditions:
1. Insert a parent with archived `version=7`, `last_modified_at=123456789`, `is_syncing=0`, then add its archived category. Parent version becomes 8 and timestamp changes. **Not lossless**.
2. Temporarily insert with `is_syncing=1` to preserve version and timestamp while attaching categories. This protects intermediate state only; an app MUST NOT leave this flag enabled after restore.
3. Finalize the technical state with `UPDATE mangas SET is_syncing=0`. The pinned UPDATE trigger then resets `last_modified_at` to current clock time; analogous chapter finalization changes chapter timestamp. **Still not lossless**.

A strict post-restore metadata readback detects this mismatch and rolls back the entire transaction, including both parents when a later parent fails. Therefore **no safe complete timestamp-preserving finalize solution has yet been proven against the pinned triggers**. It is not acceptable to silently ignore timestamp drift, leave `is_syncing=1`, disable/drop production triggers, or declare v2 import successful.

Other material adapter constraints still apply: `StringListColumnAdapter` joins genres with a literal `, ` separator (lossy if a genre value contains that separator); `BackupManga.viewer_flags ?: viewer` defines the stored viewer flag; `memo` is JSON encoded as a ByteArray and must retain unknown keys; category backup references are `BackupCategory.order`; history must map original URLs to *new* chapter IDs, with exact read duration rather than stock additive upsert; legacy tracker media IDs must be resolved safely.

## Tests executed vs configured

- **35/35 NEW host tests PASS** in 0.131s, using real candidate SQL statements with transcribed original triggers and source-shaped SQLite tables.
- **98/98 earlier migration14/ledger physical audit tests PASS** when rerun in this turn, independent of new suite.
- **133 locally executed Python/SQLite checks across these two suites**, not actual app runtime tests.
- New 20th gate `backup-parent-sqldelight-fields` (minimum 35) added to `scripts/r001/run_host_gate.py` and `.github/workflows/domain-spikes.yml`; **882 minimum configured tests / 20 groups**, NOT run as a full suite, and NOT CI-confirmed.

Evidence ZIP SHA256: `47e590c65c5397865ee16a5ceca63277d03099b66f5589289475b0cc23f95d7c`.
ChatGPT Library folder: `/Polaris/R001/parent-sqldelight-fields/`.

## Required before runtime

Implement a reviewed transaction-safe strategy to finalize `is_syncing` and preserve relevant timestamps and versions (or explicitly record and adjudicate an unavoidable deviation **without** silently claiming exact restore). Compile candidate queries against pinned SQLDelight generated Kotlin types and adapters. Implement concrete `PolarisFullParentAtomicTransactionPort` with exact field+edge readback and a single real DB transaction, validate actual ProtoBuf v1/v2 and Android B01–B05. The current fail-closed `PolarisRestoreCoordinator.preflight` v2 block must remain.

**No production migration, migration15, Yomotsu source logic, user SQLite database or PR merge was changed.** PR #1 stays Draft; issues #2 and #11 stay OPEN.
