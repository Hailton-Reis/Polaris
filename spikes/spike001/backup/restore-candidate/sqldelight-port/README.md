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

## 16 Oct 2026: integrated real portable data classes and coordinator

The Kotlin runner now compiles **the actual** `BackupPolarisBundle.kt`,
`PolarisRestoreCoordinator.kt`, `SqlDelightPolarisAtomicVirtualWorkPort.kt`
and `PolarisRestoreDigest.kt` together, instead of using
`tests/HostModel.kt`. The latter remains in the tree but is no longer
compiled. The adapter test imports the real backup settings class.

The updated runner executes two independent suites: 19 adapter and
16 cross-module integration cases. **35/35 Kotlin/JVM PASS locally**,
including backup preflight, child-before-parent order, pending state,
UUID checks, unchanged legacy backup, idempotent import, unlink
preservation and all-parent rollback on an injected transaction error.
Their executed source Git hashes match the published branch.

The R001 host gate now checks both unique markers:
`POLARIS_SQLDELIGHT_PORT_PASS 19` and
`POLARIS_REAL_MODEL_END_TO_END_PASS 16`. A missing or undercounted
suite fails regardless of the other suite's count. The eleven-stage
configured minimum rises from 405 to **421**, NOT an executed
aggregate.

The **database and query generator are still host fakes**, as are the
serialization annotations and the source `BackupManga` restorer.
This is neither a real protobuf roundtrip nor a real SQLDelight
code-generation or Android runtime test. Migration15 remains unchanged.

## 2026-10-17 — fixed stale resolved real-child identity on ledger replays

**Newly reproduced failure:** on UUID ledger reuse, the prior
`SqlDelightPolarisAtomicVirtualWorkPort` validated its cached
`merged` edges and digest but skipped revalidating whether
`mangas._id` still points to the same exact `(sourceId,sourceUrl)`
saved for each real child. The previously unguarded replay could accept a
real manga row whose `source` or `url` had changed without altering its
local `_id`. A new negative test FAILED on the old implementation,
demonstrating the problem before patching.

**Fix:** move the exact-key query
`selectAllExactSourceChildIds(sourceId,sourceUrl)` to the start of EACH
work's database transaction, before checking either existing or new
UUID ledger entries. Every resolved child's result must be the singleton
`[realMangaId]`. Missing, moved, renamed or ambiguous real rows cause
the entire transaction to abort; no title guessing or automatic relink.
Explicit `manga_id=NULL` pending references stay pending even if a matching
real row appears later.

**New regressions:** 6 Kotlin cases (URL changed, source ID changed,
missing local manga, ambiguous same source+URL, rollback when the SECOND
ledger work has a stale real ID, pending association remaining NULL after
source arrival). Verified **25/25 Kotlin parent adapter cases** plus
**16/16 integration cases = 41/41 PASS locally**. New 6 SQLite
tests execute the actual staged SQLDelight lookup and real SQLite FK
behavior, for **16/16 SQLite PASS** (the existing 10 plus 6).
Therefore **57 assertions/cases across two separately executed host
suites**, not a single Android suite.

The updated files are checked against their GitHub blobs:
- Adapter: `09edf277b9060ce0e0df5b9b7dcf0d4810a29ccc`
- Kotlin tests: `563f04df2aa45b1f901e9d8b216eea62c5b9f7a2`
- SQLite regressions: `7c31425d186f70aec285971eb4253c6cef39ddf2`

Host thresholds: `backup-sqldelight-port` increased 35→41;
`backup-sqldelight-sqlite` 10→16. The R001 twelve-stage **configured
minimum is 486**, up from 474. **486/486 was NOT executed.**
Only the 41/41 Kotlin and 16/16 SQLite candidate suites completed here.
The actual generated SQLDelight 2.3.2 Kotlin types, Android database driver,
ProtoBuf and Android B01–B05 remain untested. Production migration 15 is
unchanged. The archive `Polaris_R001_Replay_Identidade_Real_2026-10-17.zip`
contains the pre-fix failing log, post-fix logs, exact code and SHA256
manifest.
