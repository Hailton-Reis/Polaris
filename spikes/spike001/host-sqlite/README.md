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


## 2026-10-11: atomic idempotent insert regression

Run `python3 -m unittest discover -s spikes/spike001/host-sqlite -p 'test_*.py' -v`; **20/20 SQLite tests PASS** on the exact staged query definitions. `test_merge_insert_idempotency.py` adds ten cases that verify both conditional `INSERT ... SELECT ... WHERE NOT EXISTS` statements, null-orphan identity fallback, preservation of existing priorities, relink after explicit deletion, separate parents, and concurrent same-child insertion through four separate SQLite file connections.

The red test run before changing the SQL produced **four assertion failures**; the rewritten DML and complete offline host gate (72 Python, 20 SQLite, 38 Kotlin) passed. **The physical `merged` schema and migration14 are byte-identical to the prior checkpoint.** This is **not** a database UNIQUE index or an actual Android driver acceptance; #10 is only partially mitigated. Legacy duplicates must be repaired under an explicit, reversible and tested migration after B01–B04.


## 2026-10-11 — returning distinct linked manga objects

`test_merge_select_integrity.py` adds seven tests against the real `selectMergedMangasById` query. A previous unrestricted join returned duplicate manga objects for duplicate legacy `merged` edges, and had no deterministic association priority order. New query groups by local manga ID before joining to `mangas` and orders by the most preferred reference and stable row ID. `selectByMergeId` also now has deterministic priority/row order. The original SQL failed four of these seven tests. New SQLite suite **27/27 PASS**, while Python 72/72 and Kotlin 38/38 completed separately. Source snapshots and red/green logs: https://drive.google.com/file/d/1rpLs10hlX343u0HlSTldyp6O27NBjRRA/view.

No schema/migration14 changes. **SQLite queries have not yet been passed through the on-device Yomotsu/SQLDelight generator**; keep issue #10 open and issue #2 Android baseline unverified.


## 2026-10-23 — correção de limpeza SQLite no Windows (WinError 32)

Em uma execução real do CMD único FIX6, o gate `python -m unittest discover` passou pelos testes de SQL mas falhou ao remover o arquivo temporário `shared.sqlite`: `PermissionError: [WinError 32]`. O arquivo era utilizado no teste `test_multiple_sqlite_connections_write_same_child_at_most_once`.

Causa: `with sqlite3.connect(path) as conn` **não fecha** a conexão ao sair do bloco; gerencia commit/rollback. Windows impede excluir um arquivo SQLite aberto. A correção usa `contextlib.closing(...)` nas conexões de backup, nas quatro conexões concorrentes e na verificação final. O teste de regressão verifica os três contextos explicitamente fechados.

Evidências executadas em Python 3.13/Linux com as definições SQL e fonte Kotlin reais do repositório: **37/37 testes PASS**, mais **50 execuções repetidas do teste de concorrência PASS**. Isso demonstra o fechamento explícito e que as rotinas passam no ambiente de validação; **WinError 32 só será confirmado como resolvido na próxima execução do usuário no Windows**.

A correção está na branch `r001/multisource-foundation` e será recebida automaticamente pelo CMD FIX6 quando este sincronizar um checkout limpo antes do build. Não é necessário reinstalar JDK/SDK nem baixar outro CMD.
