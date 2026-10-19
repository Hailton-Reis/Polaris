# Polaris R001 — Spike-001 / backup ledger layering (staging, 2026-10-19)

**CORRECTION OF THE PREVIOUS 'PINNED-SCHEMA-BRIDGE' DIAGNOSIS**

The pristine, pinned Yomotsu tree does not include a `merged` table. **This is expected, not an unanticipated incompatibility:** the already prepared Polaris **Spike-001** explicitly adds `merged.sq` and migration **14.sqm**. Previous work has evidence of a successful pinned Yomotsu baseline Android build **and** a successful Spike-001-patched build including SQLDelight generation and migration validation (`docs/r001/ISSUE002_WORK_LOG.md`, dated 2026-10-07). Runtime B01/B02/B03 remain unproven.

The *earlier* host `pinned-schema-bridge/merged_bridge_candidate.sql` creates another `merged` table; **do not apply it on top of Spike-001**. It is an alternative isolated fixture for testing the upstream pristine schema, not the desired Polaris integration path. `migrations/14.sqm` must remain the single origin of the merged table. The SQLDelight `merged.sq` source and migration14 DDL were compared byte-for-byte after stripping the Kotlin Boolean annotation: they describe exactly the same table and index, and their Git blob SHAs were verified against branch `r001/multisource-foundation`.

## Actual compatibility path

1. Start with pinned Yomotsu source commit `0fb80c439ef816eeb50674f1b90af39918b176d8`.
2. Apply the existing Polaris Spike-001, including `merged.sq` / migration14 and its virtual source/domain/reader plumbing. Previous baseline and patched builds already succeeded, but real two-source device verification remains open.
3. **READ ONLY** audit all existing `merged` rows, parent URLs and UUID memos on a consistent database snapshot. Reject duplicated `(merge_id,manga_source,manga_url)`, duplicated `(merge_id,manga_id)` for nonnull IDs, mismatched physical child `(source,url)`, ambiguous source rows, corrupt/unknown UUID memos, stale merge URLs and FK defects. No title guesses or destructive repair.
4. In a **future reviewed migration** (not created or installed here), add only `polaris_restore_ledger` and unique indexes from `backup/restore-candidate/atomic-sqlite/atomic_parent_restore_candidate.sql`, **without** creating a second `merged` table. Apply after a read-only duplicate audit. Verify the candidate SQLDelight generated APIs and compile the Android app.
5. Continue building unified metadata+associations transaction, full v2 ProtoBuf roundtrip and Android runtime tests. `PolarisRestoreCoordinator` v2 fail-closed guard remains installed until then. Do not apply canonical migration15 prematurely.

## Verification and limits

Run from a full Polaris branch checkout:

```sh
bash spikes/spike001/backup/restore-candidate/spike001-layering/run_tests.sh
```

**49/49 new Python SQLite tests PASS locally.** Staged `merged.sq` Git blob `3e9fb499d0e1d0523aaaaaae336dd9bf5b2d4b62`, migration14 blob `8f23dc5219f49a0368705ba21d0c4e5a0d7fb1fb`. The tests also execute the actual staged `insertReturningId` and `selectMergedMangasById` queries, test pending/root behavior, FK cascades, ledger and index enforcement, legacy duplicate/conflict refusal, and an **in-memory-only upgrade rehearsal** that does not mutate its source DB.

**The pristine Yomotsu base schema is a previously-authored host fixture** `pinned-schema-bridge/pinned_schema_fixture.py`, with SQLDelight aliases/adapters and original timestamp/version triggers removed. The real Android database, SQLDelight code generator, Kotlin adapters, ProtoBuf, source extensions and runtime B01/B02/B03 were **NOT executed this turn**. This candidate does not create migration15, does not unblock v2 backup restoration, and does not merge Draft PR #1.
