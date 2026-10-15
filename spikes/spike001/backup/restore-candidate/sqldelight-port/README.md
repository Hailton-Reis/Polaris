# Polaris R001 — Kotlin SQLDelight atomic restore port (candidate)

**NON-PRODUCTION:** This directory contains a data-layer Kotlin implementation
written against the pinned Yomotsu SQLDelight API and a matching staged
`polarisRestore.sq`. It is deliberately isolated from Android source sets:
production migration 15 and existing `merged.sq` remain untouched.

## Implemented

- `kotlin-candidate/SqlDelightPolarisAtomicVirtualWorkPort.kt` implements
  the `PolarisAtomicVirtualWorkPort` required by
  `PolarisRestoreCoordinator`. It uses `tachiyomi.data.Database.transaction`
  and proposed typed `database.polarisRestoreQueries` methods to ensure all
  parent works are committed together. Reuses UUID-ledger parents, checks a
  versioned digest, memo, immutable UUID-backed virtual URL and every source
  edge and flag. A deleted source or changed priority is NEVER reattached
  by replay of an old backup.
- `kotlin-candidate/PolarisRestoreDigest.kt` creates a length-prefixed
  versioned SHA256 fingerprint containing both root and child flags,
  source ID+URL, local manga ID and pending status. This hash is stored
  in the **local** restore ledger, not the portable backup archive.
- `sql-candidate/polarisRestore.sq` defines a UUID ledger, physical
  unique indexes for source child references, and nine SQLDelight-labelled
  queries. The virtual parent is created under
  `merged://polaris/<canonical-uuid>`; the existing `MergedSource`
  does not parse this URL, but real Android navigation remains untested.
- `tests` contains isolated, explicit **fake SQLDelight/JsonObject** types
  and a Kotlin test program. They must NEVER compile into the real app.
  `run_kotlin_host.sh` compiles the actual candidate Kotlin code against
  these fixtures only.

## Verification

- **19/19 Kotlin/JVM cases PASS** (kotlinc, fake Database with rollback
  and fake generated queries), including normal import, second import
  without duplicates, two works in one transaction, atomic rollback on
  second parent, ambiguous real children, pending links, UUID/URL drift,
  local edits and root settings.
- **10/10 Python SQLite checks PASS** for the proposed SQL syntax, nine
  named query contracts, ledger FK, source+URL uniqueness and
  pending-vs-resolved links. This tests SQLite execution, **NOT**
  actual SQLDelight Kotlin code generation or Android runtime.
- Executed main sources and all five Kotlin fixtures/tests are Git
  blob-identical to their published GitHub files.
- The 31-case previous Python/SQLite transaction reference remains separate
  and is not superseded by the proposed Kotlin port.

Reproduce:
```bash
bash spikes/spike001/backup/restore-candidate/sqldelight-port/run_kotlin_host.sh
python3 -m unittest discover -s spikes/spike001/backup/restore-candidate/sqldelight-port/tests -p 'test_*.py' -v
```

**Release blockers:** review legacy duplicate merged rows and migrate safely,
compile actual `polarisRestore.sq` with pinned SQLDelight, check typed
query signatures (including `awaitAsOne` for INSERT RETURNING), link the
real `MangaRestorer` error propagation and `BackupRestorer` entry point,
and execute full Kotlin ProtoBuf backup/restore on an Android device.
A `Database.transaction` call alone does not prove concurrency guarantees
without real database-driver/constraint verification. Issue #2 B01–B05 and
issues #10/#11 remain OPEN. PR #1 remains DRAFT.
