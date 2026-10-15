# R001 / issues #10 and #11 — transactional restore (SQLite host candidate)

**Not installed in Yomotsu / Android. No changes to migrations 14/15.**

This directory contains a concrete **SQLite reference implementation** of
`PolarisAtomicVirtualWorkPort.commitAllOrThrow()`. It is not Kotlin and is not
the production SQLDelight adapter. It supplies tested atomic semantics for the
future Android port, with schemas checked against the pinned Yomotsu
`mangas.sq` (blob `b5d1909f759683136978e0bf2df182287ca4065d`)
and Polaris `merged.sq` (blob `3e9fb499d0e1d0523aaaaaae336dd9bf5b2d4b62`).

## Concrete changes

`atomic_parent_restore_candidate.sql` stages:

- `polaris_restore_ledger(archive_uuid PRIMARY KEY, parent_manga_id UNIQUE,
  archive_digest)` with a cascading parent foreign key. This is the physical
  one-parent-per-UUID mapping for import retries.
- A unique edge key `(merge_id, manga_source, manga_url)` applying equally to
  pending (`manga_id IS NULL`) and resolved links.
- A second partial unique edge index on `(merge_id,manga_id)` for resolved
  links, blocking the same real source row from being attached twice even when
  a corrupted reference stores a different source URL.

**Existing corrupted/duplicate merged rows intentionally cause unique-index
creation to fail.** Do **not** run this DDL directly on a user database:
first audit duplicates, build a reviewed migration/rollback plan, and
perform the entire migration in one real schema transaction. Do not
silently deduplicate, because doing so may lose per-link settings.

`atomic_parent_restore_host.py` implements a usable Python/SQLite
reference: `BEGIN IMMEDIATE`, fail-closed archive input validation,
pre-ledger UUID collision detection via JSON parsing **without JSON1
dependency**, strict real child source+URL and ID matching, creation of
virtual parent+UUID memo+ledger+root/children inside one transaction,
and `ROLLBACK` on every failure.

For an identical repeated backup, it returns the existing parent ID without
any write. If the local parent, UUID, its source links or its settings have
changed since the original import, the replay is rejected rather than
silently reattaching sources that a reader intentionally unlinked.
A different archive with the same UUID and conflicting fingerprint is also
rejected. Parent UUIDs already present in pre-ledger `memo` require manual
reconciliation, not a guessed match by title.

## Verified host evidence

```bash
cd spikes/spike001/backup/restore-candidate/atomic-sqlite
python3 -m unittest -v test_atomic_parent_restore.py
```

**31/31 tests PASS (Python 3.13.5, SQLite 3.46.1)**. Includes:
initial import, FK root and ledger, exact source ID+URL and pending NULL,
idempotent retry, deliberate unlink preservation, conflicting UUID and
settings, duplicate physical indexes, migration failure on old duplicates,
failure after the first or second parent with full rollback, and **two real
SQLite connections** contending for the same file (same archive accepted
exactly once, conflicting archives never both accepted).

The exact local source files are SHA-equal to the committed GitHub blobs:

- SQL: `35ed1fdb05e19cb7c2f2d0c0d21ad0f0cde3ce7f`
- Python implementation: `9183f66ffcd8835c4074216758458060f196e06d`
- 31-case test suite: `fb613a30a263fc1eb3f10ede79d3f3f060c76a68`

`domain-spikes.yml` and `run_host_gate.py` now require an
**eighth** stage `backup-atomic-sqlite` (minimum 31), making the eight
configured minima **291** (72+36+38+17+65+12+20+31).
This is **NOT a claim of a complete 291-case run** or even CI execution:
the 31-case suite alone was run locally.

## Required gates before production

1. Implement real Kotlin `PolarisAtomicVirtualWorkPort` using SQLDelight
   transactions and typed repositories; the Python port is a reference only.
2. Audit old duplicate references and devise safe deterministic migration
   strategy. Test the proposed ledger/indices with the pinned Yomotsu
   SQLDelight dialect on Android devices, including FK and indexes.
3. The reference uses `merged://polaris/<uuid>` as a newly created
   parent URL. Confirm this URL **actually works with Yomotsu's
   `MergedSource` navigation**, or adjust before integration.
4. Ensure restored `BackupManga` chapters/history/tracking succeed
   before calling this parent port; stock `BackupRestorer` may swallow
   per-manga exceptions.
5. Test actual Kotlin ProtoBuf legacy/new backups, android build and runtime
   cases B01–B05 from #2 with two different real sources.

Keep #10/#11 OPEN and PR #1 DRAFT; migration 15 remains untouched.
