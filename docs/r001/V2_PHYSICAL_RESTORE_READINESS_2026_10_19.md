# Polaris R001 — physical restore-v2 readiness audit

Date: 2026-10-19. **HOST-ONLY, FAIL-CLOSED, READ-ONLY.**

## Concrete reproduced gap

The existing `spike001-layering/verify_layering.py:audit_existing_links` was designed for **additive ledger/index DDL installation** on top of Spike-001 migration14, not as proof that a fully backed-up virtual parent can be restored. It accepts a virtual parent with a healthy real-source edge but **NO synthetic root** edge (`manga_source=6969`, `manga_id=merge_id`). A real restored parent needs exactly one correct root, and it cannot be silently recreated after user edits. A negative test reproduces the old audit's empty finding; the new readiness audit rejects it.

## Added implementation

`spikes/spike001/backup/restore-candidate/spike001-layering/audit_v2_readiness.py` is a separate, read-only SQLite inspection function `audit_v2_restore_readiness(connection)`. It checks:

- Spike-001 `mangas`/`merged` and separate UUID ledger presence;
- exactly one virtual self-link, pointing to its physical parent ID, URL and source; no root marked as the info provider;
- each physical resolved real child has a unique, matching (source, URL) row; pending NULL references are intentionally kept pending;
- all edge `merge_url` values agree with the parent, and no two virtual parents occupy the same URL;
- valid JSON-object parent memo, canonical UUID claims, no duplicate or orphaned claims;
- UUID-ledger parent ID, memo, `merged://polaris/<uuid>` URL, lowercase SHA256 digest shape and foreign keys;
- missing or malformed rows fail closed, returning anonymous codes rather than user URLs, UUIDs or notes.

The function **does not mutate or repair a database**, run title heuristics, insert missing links, or claim that full user metadata is identical. A future production adapter must re-run equivalent checks **inside the same database transaction** as the complete parent metadata + child edges and mandatory readback. This host gate is NOT enough to lift v2 preflight.

## Executed evidence

- Existing `test_spike001_layering.py`: **49 PASS**.
- New `test_audit_v2_readiness.py`: **49 PASS** (root cardinality, malformed UUID/memo/digest, duplicate virtual URL, FK, pending and ambiguous child, physical ledger mismatch, redacted diagnostics).
- Both together via the published `run_tests.sh`: **98/98 Python SQLite PASS** locally. These use the actual Polaris-authored migration14 and restore-ledger candidate and the previously developed **pinned-shaped fixture** for Yomotsu tables, not the real Android database or SQLDelight-generated types.
- Four staged source files match exactly their published Git blob SHA hashes (code, tests, runner and README).

Updated the **existing** `backup-spike001-layering` host gate from 49 to **98**. Its CI YAML step already exists and invokes the updated runner. The total configured host minimum is now **847 tests in 19 gates**, *NOT 847 executed passes*. GitHub Actions remains a separate unverified requirement.

Evidence ZIP SHA256: `01ee7811bf2f4df64acd7f7d6fac879d9f3233559d0b3187a998581bc34785b0`.
Library `/Polaris/R001/spike001-layering-reconciliation/`.

## Release boundary

No modifications to original Spike-001 `merged.sq`, migration14, migration15, Android production model, user data or the `PolarisRestoreCoordinator` v2 fail-closed block. Real codegen, full `BackupManga` field readback, real ProtoBuf, and Android B01–B05 remain blockers. Keep GitHub PR #1 DRAFT, issues #2 and #11 OPEN.
