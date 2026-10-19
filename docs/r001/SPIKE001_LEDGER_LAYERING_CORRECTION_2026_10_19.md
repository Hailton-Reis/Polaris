# Polaris R001 — verified migration layering correction (2026-10-19)

The earlier note described a missing upstream `merged` table as a blocker. That conflated **pristine pinned Yomotsu** with **Yomotsu after Polaris Spike-001**. A `merged` table is expected to be absent from pristine Yomotsu. Polaris already includes the source `spikes/spike001/new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq` and migration `spikes/spike001/new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm`, and there is previously recorded evidence of a successful patched Android build in `docs/r001/ISSUE002_WORK_LOG.md`. The original Spike-001 migration14 must be kept; a second `CREATE TABLE merged` is unnecessary and would fail.

The correct forward path is a **separately reviewed additive ledger and uniqueness-index migration** on top of migration14, and a unified transaction for full backup metadata plus associations. The candidate schema remains isolated. Do not edit migration15 or bypass the fail-closed v2 import guard.

Reconciliation tests: **49/49 local host Python/SQLite PASS**; pinned `merged.sq` and `14.sqm` blob-identical to GitHub version; in-memory audit + candidate DDL preserve old rows; duplicated source/link keys, legacy UUID collisions, changed URLs and ambiguous real children are rejected; foreign-key on-delete behavior survives. Scope: a simplified upstream host schema, no complete Android build in this turn, no new mobile runtime source tests.

See `spikes/spike001/backup/restore-candidate/spike001-layering/README.md` for reproduction. PR #1 remains Draft; issue #2 and issue #11 remain open. No production changes.
