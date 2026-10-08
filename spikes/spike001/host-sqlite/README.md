# Spike-001: real migration 14 SQLite contract gate

Run the stdlib-only tests from the repository root:

```bash
python3 -m unittest discover -s spikes/spike001/host-sqlite -p 'test_*.py' -v
```

The ten tests directly load and execute:
- `spikes/spike001/new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm`;
- `spikes/spike001/new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq`.

The tests use SQLite `:memory:` with `PRAGMA foreign_keys=ON` and a **minimal** `mangas` table fixture. They cover schema parity, insertion of two children plus the virtual parent, deleting one reference, cascade deletion of the virtual parent, SET NULL after source removal, FK validation, transaction rollback, sparse settings updates and the real `selectMergedMangasById` join.

**Verified locally on 2026-10-08:** 10/10 PASS using the exact production SQL files. Git blob identities of both SQL source files were verified against the repository before and after execution: migration `8f23dc5219f49a0368705ba21d0c4e5a0d7fb1fb`, queries `6dc74ac77f91b39583febb33d8224e5663ee64ba`. The new Python test itself was also matched by blob hash to the committed file `0e5780564d6ac96e67222f30e5f1d68816bf335d`.

Important limits:
- This uses desktop Python's SQLite runtime, **not** the actual Android SQLDelight driver or complete Yomotsu database.
- Android API 31's framework SQLite version is below 3.35, but pinned Yomotsu explicitly uses `AndroidxSqliteDriver(driver=BundledSQLiteDriver())` with FK enabled, and its own `mangas.sq` already relies on `RETURNING`. Do **not** remove working `RETURNING` queries based solely on the OS SQLite version. The existing `check_issue002_sql.py` now checks the pinned bundled-driver wiring statically. Android connection behavior still needs runtime verification.
- `DeleteMergedManga.deleteMerge` only removes association rows. The test documents that it **does not delete the virtual parent manga row**. This is a separate lifecycle/API issue and should not be misrepresented as a complete work deletion.
- These tests add **no migration 15**, make **no** claims about B01/B02/B03/B04/B05 Android reading, and do not close issue #2.

The SQL tests run before Gradle in `.github/workflows/domain-spikes.yml` and before the Android baseline build in `scripts/r001/build_issue002.sh`. GitHub Actions runner assignment remains a separate blocker.
