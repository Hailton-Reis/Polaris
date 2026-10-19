# Polaris R001 — UUID-stable destination URL correction (2026-10-19)

## Concrete integration defect

`PolarisParentMetadataRestorePlanner` originally required an already-resolved
virtual parent's destination `mangas.url` to equal `parentSnapshots[*].manga.url`.
But the staged `SqlDelightPolarisAtomicVirtualWorkPort` deliberately inserts new
parents under `merged://polaris/<canonicalUuid>`, while a full BackupManga
snapshot may contain a *legacy origin* virtual URL from another device.
As a result, an entirely valid second-device restore or UUID replay could be
rejected by the planner before the atomic port was called.

## Narrow, staging-only fix

- `ParentRestoreCommand` now explicitly carries `destinationUrl`, computed as
  `merged://polaris/<UUID>`, independently of `fullBackupManga.url`.
- The full input BackupManga remains unchanged and attached to the command:
  the planner does not mutate or overwrite historical archive metadata.
- Existing UUID-ledger rows must use the stable destination URL, not the
  original backup URL; an old/untracked parent URL must be explicitly migrated,
  not guessed or relinked by title.
- This does NOT change Yomotsu production SQLDelight, schema, backup model, or
  `PolarisRestoreCoordinator`'s v2 import refusal.

## Evidence

The three new tests did not compile against the prior model because
`ParentRestoreCommand.destinationUrl` did not exist (`red_compile.log`).
The updated source plus 25 old and 3 new Kotlin/JVM cases passed (`green_28_pass.log`).
The offline harness uses `BackupManga`, bundle, serializer annotation test doubles;
it does not prove actual protobuf, SQLDelight generator, Android or transaction.

## Remaining P0

The future Android implementation must: check the real UUID ledger *inside*
one SQLDelight transaction; verify/merge parent memo JSON without losing keys;
remap categories by names; restore every selected full BackupManga field,
chapters/history/tracking with rollback or explicit replay policy; compare live
metadata on retries; reject existing untracked parents and local changes;
exercise real v1/v2 ProtoBuf round-trips; complete Android B01–B05.
Never remove the v2 import guard until this is independently proven.