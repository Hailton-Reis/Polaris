#!/usr/bin/env python3
"""Safe rehearsal of staged Polaris UNIQUE/UUID DDL against an in-memory SQLite clone.

Never applies DDL to the supplied DB. Only use a checkpointed, consistent copy.
This verifies actual SQLite semantics, NOT generated SQLDelight/Android behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from audit_legacy_merges import inspect_database, save_report_without_overwrite

DEFAULT_DDL = Path(__file__).resolve().parent.parent / 'atomic-sqlite' / 'atomic_parent_restore_candidate.sql'


def data_fingerprint(db, name):
    # Name comes exclusively from a static whitelist, never an untrusted parameter.
    if name not in ('mangas', 'merged'):
        raise ValueError('Unknown table requested')
    digest = hashlib.sha256()
    for row in db.execute(f'SELECT * FROM {name} ORDER BY _id'):
        encoded = repr(tuple(row)).encode('utf-8')
        digest.update(len(encoded).to_bytes(8, 'big'))
        digest.update(encoded)
    return digest.hexdigest()


def unique_index(db, table, columns, *, partial=False):
    for idx in db.execute(f'PRAGMA index_list("{table}")'):
        # row: (seq,name,unique,origin,partial)
        if not idx[2] or bool(idx[4]) != partial:
            continue
        actual = tuple(col[2] for col in db.execute(
            'PRAGMA index_info("%s")' % idx[1].replace('"', '""')))
        if actual == columns:
            return True
    return False


def constraints_present(db):
    cols = {c[1]: c for c in db.execute('PRAGMA table_info("polaris_restore_ledger")')}
    if not {'archive_uuid', 'parent_manga_id', 'archive_digest'} <= cols.keys():
        return False
    if cols['archive_uuid'][5] != 1 or not cols['parent_manga_id'][3] or not cols['archive_digest'][3]:
        return False
    fks = list(db.execute('PRAGMA foreign_key_list("polaris_restore_ledger")'))
    if not any(fk[2] == 'mangas' and fk[3] == 'parent_manga_id' and
               fk[4] == '_id' and fk[6].upper() == 'CASCADE' for fk in fks):
        return False
    return (unique_index(db, 'polaris_restore_ledger', ('parent_manga_id',)) and
            unique_index(db, 'merged', ('merge_id', 'manga_source', 'manga_url')) and
            unique_index(db, 'merged', ('merge_id', 'manga_id'), partial=True))


def rehearse_connection(source: sqlite3.Connection, ddl: str) -> dict:
    # Audit first and avoid adding any new schema on a database with blockers.
    audit = inspect_database(source)
    result = {
        'safe_to_install_unique_indexes': False,
        'audit': audit,
        'rehearsal': 'BLOCKED' if not audit['safe_to_install_unique_indexes'] else 'NOT_RUN',
        'reason_code': 'LEGACY_AUDIT_BLOCKER' if not audit['safe_to_install_unique_indexes'] else None,
        'scanned': audit.get('scanned', {}),
        'live_database_modified': False,
    }
    if not audit['safe_to_install_unique_indexes']:
        return result

    clone = sqlite3.connect(':memory:')
    try:
        source.backup(clone)
        clone.execute('PRAGMA foreign_keys=ON')
        clone.execute('PRAGMA query_only=OFF')
        before = {name: data_fingerprint(clone, name) for name in ('mangas', 'merged')}
        before_counts = {name: clone.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                         for name in ('mangas', 'merged')}
        try:
            clone.executescript(ddl)
            after = {name: data_fingerprint(clone, name) for name in ('mangas', 'merged')}
            integrity = clone.execute('PRAGMA integrity_check').fetchone()
            foreign_keys = list(clone.execute('PRAGMA foreign_key_check'))
            if before != after:
                result['reason_code'] = 'ORIGINAL_ROWS_CHANGED_IN_REHEARSAL'
            elif integrity != ('ok',) or foreign_keys:
                result['reason_code'] = 'SQLITE_INTEGRITY_CHECK_FAILED'
            elif not constraints_present(clone):
                result['reason_code'] = 'REQUIRED_CONSTRAINTS_ABSENT'
            else:
                result['reason_code'] = None
                result['safe_to_install_unique_indexes'] = True
                result['rehearsal'] = 'PASS_IN_MEMORY_ONLY'
            result['original_rows_before'] = before_counts
        except sqlite3.DatabaseError:
            result['reason_code'] = 'DDL_REHEARSAL_FAILED'
        except (ValueError, TypeError):
            result['reason_code'] = 'REHEARSAL_VALIDATION_FAILED'
        if result['rehearsal'] != 'PASS_IN_MEMORY_ONLY':
            result['rehearsal'] = 'FAILED_IN_MEMORY_ONLY'
    finally:
        clone.close()
    return result


def inspect_copy(path: Path, ddl_path: Path = DEFAULT_DDL):
    if not path.is_file():
        raise FileNotFoundError('Input must be an existing consistent SQLite file copy')
    ddl = ddl_path.read_text(encoding='utf-8')
    src = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        src.execute('PRAGMA query_only=ON')
        return rehearse_connection(src, ddl)
    finally:
        src.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path, help='Consistent COPY of the SQLite database')
    parser.add_argument('--report', type=Path, help='Create a NEW JSON report (will not overwrite)')
    args = parser.parse_args(argv)
    try:
        result = inspect_copy(args.database)
        output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
        if args.report:
            save_report_without_overwrite(args.database, args.report, output)
        print(output)
        return 0 if result['safe_to_install_unique_indexes'] else 2
    except (OSError, ValueError, sqlite3.DatabaseError) as exc:
        # Avoid echoing input values from potentially sensitive data.
        print(json.dumps({'safe_to_install_unique_indexes': False,
                          'reason_code': 'DATABASE_OR_DDL_UNREADABLE',
                          'error_type': type(exc).__name__}), file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
