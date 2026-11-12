# Polaris R001 — reviewed, reversible link reconciliation rehearsal

**Staging candidate; never run a schema migration against a user database.**

`rehearse_reviewed_reconciliation.py` extends the earlier read-only `plan_legacy_reconciliation.py` and in-memory index rehearsal with an explicit operator review manifest. It does **not** generate production cleanup SQL and never writes to the provided SQLite database.

## Workflow

Use a consistent SQLite backup copy, including WAL/checkpoint data as needed. Do not put private user databases in GitHub or tickets.

1. Produce a **new** JSON approval template:

   ```bash
   python3 spikes/spike001/backup/restore-candidate/migration-audit/rehearse_reviewed_reconciliation.py \
     /path/to/consistent-backup.sqlite --template --report /path/to/new-template.json
   ```

2. Inspect the results with a reviewer. **Only exact duplicate groups** are eligible. Manually copy the chosen objects from `available_exact_groups` to `approved_groups`, set `reviewed_by_operator` to `true`, and provide a nonempty `approval_note`. Keep the original database fingerprint and all source/group hash fields unchanged. Pending-vs-resolved, settings differences and virtual-root conflicts always remain blocked.

3. Rehearse selected approvals:

   ```bash
   python3 spikes/spike001/backup/restore-candidate/migration-audit/rehearse_reviewed_reconciliation.py \
     /path/to/consistent-backup.sqlite --reviewed-approvals /path/to/edited-approval.json \
     --report /path/to/new-result.json
   ```

The simulator binds approval to **the entire `mangas` and `merged` snapshot** plus each approved group hash and exact keeper/removal IDs. It refuses any changed rows, unsigned approval, unexpected group, altered selection, missing rationale, referenced `merged._id` foreign keys or triggers attached to `merged`. It then opens a disposable SQLite `:memory:` clone, removes only approved copies, rehearses the staged UNIQUE/ledger DDL there, checks all survivor rows, drops staged constraints, reinserts the original rows with their IDs, and verifies the full source-row fingerprint is restored. Any remaining blockers cause a failed rehearsal. The source DB is always read-only.

**Both modes return exit code 2 even on a successful rehearsal.** Exit 0 is not emitted as a migration green light. Error codes 3 indicate an unreadable DB, invalid approval, report collision, or similar blocker. JSON report paths must be new `.json` files; previous no-clobber and `0600` safeguards apply. Reports exclude manga titles and full URLs.

## Evidence / limits

Run `python3 -m unittest discover -s spikes/spike001/backup/restore-candidate/migration-audit -p 'test_*.py' -v` for this host-only module. **85/85 passed locally** on Python/SQLite for 2026-10-16: 62 prior tests + 23 new review and reversal tests, including tampering, partial approvals, FK references, triggers, DDL corruption and source-file byte-preservation. This is not actual Android SQLDelight compilation, nor approved data deletion.

**Before production:** confirm generated SQLDelight query signatures, physical SQLite constraints on Android, legacy child ID references, a reviewed irreversible-operation procedure with a durable undo backup, real MangaRestorer error propagation and two-source B01–B05 runtime tests. PR #1 must remain draft, issues #2/#10/#11 open, and migration15 unchanged.