# Polaris R001 — child-first restore coordinator (#11)

**Status: host-only candidate; NOT installed in Yomotsu Android.**
Source code: `PolarisRestoreCoordinator.kt`, with strict ports for restoring
real source mangas and atomic reconstruction of virtual parent associations.

## P0 failure reproduced in pinned Yomotsu

`kiritsuguxs/yomotsu@0fb80c439ef816eeb50674f1b90af39918b176d8`
`BackupRestorer.restoreFromFile()` starts category, app preferences,
source preferences, `restoreManga` and extension jobs with `launch`
inside `coroutineScope`. Stock `restoreManga()` attempts transaction
chunks; when a chunk fails it retries each manga individually and
**collects errors without rethrowing**. Therefore, waiting for the job's
completion alone **does not prove** that all resolved child source mangas
were restored. Creating virtual links immediately afterward could produce
a deceptively successful but incomplete Polaris archive import.

## New coordinator

`PolarisRestoreCoordinator.preflight(bundle, ordinary, libraryEntries)`
requires the **complete optional Polaris bundle** and exact child snapshot
coverage to validate before any ordinary restore starts. It also requires
each work's portable `archiveWorkKey` to equal a canonical UUID, not
a local `merged://<ID>` or work title.

`restore(..., awaitVerifiedOrdinaryRestore)` requires:
1. A callback which completes **only if every necessary ordinary real manga
   has been restored successfully** (cannot simply call the existing
   `BackupRestorer.restoreManga()`, which may suppress failures).
2. Supplemental source-specific `BackupManga` restored via
   `PolarisSourceRestorePort.restoreSupplementalMangaOrThrow()`.
   Errors are fatal before ANY virtual parent associations are committed.
3. Exact source ID+URL resolution to **one and only one positive local real
   manga ID** per non-pending link. Duplicate row matches and any
   cross-identity reuse of the same local ID abort.
4. A link exported as `isPending=true` remains `mangaId=NULL` even if
   another virtual parent uses the same resolved source identity. No
   relinking by title, no guessed local ID.
5. **One** call to `PolarisAtomicVirtualWorkPort.commitAllOrThrow` for
   all parent works. The Android implementation MUST provide a durable
   parent UUID ledger and a real SQLDelight transaction for
   all-or-nothing parent/root/child updates; that adapter **does not exist
   yet**. This coordinator itself is NOT an atomic transaction.

Legacy Yomotsu backups without `polaris`, or restores with the
library-entries option disabled, are a no-op for the new coordinator.

## Local validation

```bash
bash spikes/spike001/backup/restore-candidate/run_tests.sh
```

The local standalone Kotlin/JVM harness compiled the **same code file
whose Git blob** is
`89ef78974d85f7b1770ddbd0baa22e253745cf6d`
and returned `POLARIS_YOMOTSU_RESTORE_COORDINATOR_PASS 20`
(**20/20** scenarios). Cases include source-specific child-first ordering,
ordinary/supplemental failure propagation, ambiguous matches, pending
references, per-parent pending vs resolved, UUID collisions, unsupported
versions, missing child snapshot and single atomic parent-port call.

**Precision about evidence:** the locally executed test harness was
authored before a reformatted but equivalent 20-case harness was
committed to GitHub. Only the **coordinator implementation** was confirmed
byte-equal to the published blob, not the GitHub test file/runner.
The exact committed GitHub test suite still needs CI execution.

`scripts/r001/run_host_gate.py` now requires a **seventh** gate,
`backup-restore`, with an exact unique success marker and minimum 20.
The full configured seven-stage minimum is
**72 Python + 36 SQLite + 38 core Kotlin + 17 backup SQLite +
65 backup Kotlin + 12 Yomotsu export adapter + 20 restore coordinator
= 260 minimum**. **The combined 260-case gate was not run.**

`.github/workflows/domain-spikes.yml` runs the coordinator's
standalone script, and `spikes/backup-lab` explicitly excludes its
test doubles. Gradle/Android/real protobuf execution is still blocked
until runners and device test environment work.

[GitHub candidate](https://github.com/Hailton-Reis/Polaris/tree/r001/multisource-foundation/spikes/spike001/backup/restore-candidate)
· [Evidence ZIP in Polaris Drive](https://drive.google.com/file/d/1uwitwsFhcPNj3OoTvhld9YKOqaC9nL08/view)
SHA-256 `46077610e28e9675dfb210fe4cedc6f69a4380dc1ace6f04ecf79402cbec88ab`.
The ZIP contains source, host fake tests, logs, a SHA manifest and an
explicit statement about differences between the local and committed
test harnesses.

**Next mandatory implementation:**
- Add a verified Yomotsu `MangaRestorer` adapter that propagates
  individual failures, restores complete `BackupManga` children,
  and queries **all** exact `source+url` database matches.
- Add a single SQLDelight transaction performing UUID idempotent
  find/create, no ambiguous parents, root/child association upsert
  with pending-null links. Integrate with actual `BackupRestorer.kt`
  decode, preflight, coroutine barriers and error reporting.
- Verify old/new actual `kotlinx.serialization.protobuf` backups
  and Android B01–B05 with two live sources. Resolve issue #10's physical
  uniqueness/restore-ledger race before release.

PR #1 stays draft. Issues #2, #10 and #11 remain open, and the
production `merged.sq` / migration 14/15 are unchanged.
