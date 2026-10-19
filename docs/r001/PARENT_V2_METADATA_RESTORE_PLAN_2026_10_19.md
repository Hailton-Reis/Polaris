# Polaris R001 — v2 parent metadata restore preflight candidate

Date: 2026-10-19. STAGING ONLY. NOT AN ANDROID RESTORER.

The candidate binds a FULL BackupManga snapshot to an exact canonical UUID and prepares a plan. Its checks reject UUID/ID collisions, source/URL mismatch, ambiguous existing parents, missing/duplicate category remaps, incomplete archives, and unknown or locally modified metadata. It distinguishes new parent, verified empty placeholder, and identical replay without replacing local edits.

The adapter still DOES NOT EXIST. Any future Android adapter must query the authoritative UUID ledger, compare ALL metadata for IDENTICAL_TO_ARCHIVE, prove EMPTY_PLACEHOLDER truly contains no changes, revalidate inside a single SQLDelight transaction, map categories by name, restore all requested chapter/history/tracking/settings/memo data without clobbering live edits, and roll back all work on failure. This plan has no persistence, no atomicity, no real ProtoBuf codec, no Android build, and MUST NOT remove the v2 fail-closed guard in PolarisRestoreCoordinator.

Local command executed: kotlinc with representative DTO, BackupManga, annotation and parent-payload doubles, then java -jar host.jar. 25/25 PASS. This validates the exact new planner source but not the committed real BackupPolarisBundle.kt and not the actual host runner paths. Re-run the committed runner and CI before considering it integrated.

After publication, execute:
`bash spikes/spike001/backup/parent-candidate/run_restore_plan_tests.sh`

Status blockers: Android B01–B05, actual protobuf v1/v2 golden-file round-trip, SQLDelight 2.3.2 migration/runtime, parent UUID ledger/transaction and full snapshot replay conflict policy. PR #1 remains Draft; issue #11 remains OPEN.