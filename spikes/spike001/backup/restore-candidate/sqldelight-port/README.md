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

## 2026-10-15 evidence and gate

The locally executed Kotlin test source plus all Kotlin/SQL files and mock
SQLDelight classes are Git blob-identical to the corresponding committed
GitHub files. The **19/19** locally executed Kotlin cases include one extra
regression refusing a changed virtual parent URL, even if the UUID and
source-link rows still refer to that parent.

**10/10 SQLite syntax/contract checks PASS** with Python's built-in sqlite3
using a minimal pinned-Yomotsu-schema-shaped database. The GitHub Python
test suite is a shorter equivalent 10-test implementation; the
locally executed 10-test file is preserved separately in the evidence ZIP.
Neither suite is a real SQLDelight code-generation result.

[Full source, logs, SHA manifest (Drive)](https://drive.google.com/file/d/1BJBwYtub_1lYH07C1h8YByAVJLn2Jgjp/view).
ZIP SHA256: `06a6aa52bfa007f1484deb61236517cfcebc41fe5b34deb1758419841d15cde1`.

The offline host aggregator and CI now configure two more stages:
`backup-sqldelight-port` minimum **19**,
`backup-sqldelight-sqlite` minimum **10**. The total threshold for the
ten host stages becomes **320 configured** cases
(72+36+38+17+65+12+20+31+19+10). **The complete 320-case runner
has not been executed.** The 19/19 and 10/10 refer to separate local
host executions, not Gradle/Android acceptance.

Issue #10/#11 P0 stay open, #2 Android B01–B05 remains unverified,
PR #1 remains DRAFT and migration 15 is unchanged.
