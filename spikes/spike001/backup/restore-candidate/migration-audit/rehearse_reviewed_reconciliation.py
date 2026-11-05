#!/usr/bin/env python3
"""Polaris R001: manually approved, reversible, IN-MEMORY legacy-link rehearsal.

A human explicitly selects exact-duplicate groups using a versioned JSON
approval manifest; no production DELETE or migration is ever performed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

from audit_legacy_merges import inspect_database, save_report_without_overwrite
from plan_legacy_reconciliation import FIELDS, candidate_plan
from rehearse_restore_migration import constraints_present

STAGED_DDL = (Path(__file__).resolve().parent.parent / 'atomic-sqlite' /
              'atomic_parent_restore_candidate.sql')
FORMAT = 'polaris-review-approvals-v1'


def fingerprint_database(db: sqlite3.Connection) -> str:
    """Hash every stored manga and merge field, without exposing row contents."""
    h = sha256(b'polaris-full-schema-snapshot-v1\x00')
    for table in ('mangas', 'merged'):
        h.update(table.encode())
        for row in db.execute(f'SELECT * FROM {table} ORDER BY _id'):
            fields = [v.hex() if isinstance(v, bytes) else repr(v) for v in row]
            raw = json.dumps(fields, separators=(',', ':'), ensure_ascii=False).encode()
            h.update(len(raw).to_bytes(8, 'big'))
            h.update(raw)
    return h.hexdigest()


def approval_template(db: sqlite3.Connection) -> dict:
    plan = candidate_plan(db)
    if not plan.get('ready_for_review'):
        raise ValueError('Legacy merge schema does not match expected format')
    return {
        'format': FORMAT,
        'database_rows_sha256': plan['database_rows_sha256'],
        'database_full_sha256': fingerprint_database(db),
        'available_exact_groups': [
            {'group_id': g['group_id'], 'group_sha256': g['row_fingerprint_sha256'],
             'keeper': g['candidate_keep_row_id'],
             'candidate_removals': g['candidate_redundant_row_ids']}
            for g in plan['review_groups']
            if g['classification'] == 'EXACT_DUPLICATE_CANDIDATE_REVIEW'
        ],
        'approved_groups': [],
        'reviewed_by_operator': False,
        'approval_note': '',
        'notice': 'Fill approved_groups manually from available_exact_groups. '
                  'This tool only rehearses on :memory:, never writes to original DB.',
    }


def _reject_indirect_references(db: sqlite3.Connection) -> None:
    """Keep row-id preservation conservative: unknown refs/triggers require review."""
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        if name.startswith('sqlite_'):
            continue
        for fk in db.execute('PRAGMA foreign_key_list("%s")' % name.replace('"', '""')):
            if fk[2] == 'merged':
                raise ValueError('An unknown table refers to merged rows')
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name='merged'").fetchone():
        raise ValueError('A trigger could depend on removed merged rows')


def _validate_approvals(template: dict, approvals: dict) -> list[int]:
    if approvals.get('format') != FORMAT:
        raise ValueError('Wrong approval format')
    if (approvals.get('database_rows_sha256') != template['database_rows_sha256'] or
        approvals.get('database_full_sha256') != template['database_full_sha256']):
        raise ValueError('Database changed since human review')
    if approvals.get('reviewed_by_operator') is not True:
        raise ValueError('Explicit operator review is required')
    if not isinstance(approvals.get('approval_note'), str) or not approvals['approval_note'].strip():
        raise ValueError('Nonempty rationale required')
    approved = approvals.get('approved_groups')
    if not isinstance(approved, list) or not approved:
        raise ValueError('At least one explicit approved group is required')
    choices = {g['group_id']: g for g in template['available_exact_groups']}
    selected, seen = [], set()
    for g in approved:
        if not isinstance(g, dict):
            raise ValueError('Approval must be an object')
        key = g.get('group_id')
        if not isinstance(key, str) or key in seen or key not in choices:
            raise ValueError('Unknown or repeated group or non-exact conflict')
        seen.add(key)
        authoritative = choices[key]
        if (g.get('group_sha256') != authoritative['group_sha256'] or
            type(g.get('keeper')) is not int or g.get('keeper') != authoritative['keeper'] or
            g.get('candidate_removals') != authoritative['candidate_removals']):
            raise ValueError('Group hash, survivor or removal IDs changed')
        selected += authoritative['candidate_removals']
    if len(selected) != len(set(selected)):
        raise ValueError('Some rows were approved more than once')
    return selected


def rehearse_approved(source: sqlite3.Connection, approvals: dict,
                      ddl: str | None = None) -> dict:
    """Restore exact deleted rows on the clone, proving *reversibility*.

    Also checks the staged candidate uniqueness indexes on the intervening
    repaired clone. Every mutation, including the inverse, occurs in memory.
    """
    template = approval_template(source)
    removed = _validate_approvals(template, approvals)
    result = {'simulation': 'BLOCKED_IN_MEMORY_ONLY', 'approved_remove_row_ids': removed,
              'source_database_modified': False, 'restoration_verified': False,
              'migration_approved': False, 'reason_code': None}
    clone = sqlite3.connect(':memory:')
    try:
        source.backup(clone)
        clone.execute('PRAGMA foreign_keys=ON')
        _reject_indirect_references(clone)
        baseline = fingerprint_database(clone)
        initial_merged = {r[0]: tuple(r) for r in clone.execute('SELECT '+','.join(FIELDS)+' FROM merged')}
        # Capture raw row bytes/column values to allow exact inverse inserts.
        removed_rows = [initial_merged[i] for i in removed]
        for i in removed:
            clone.execute('DELETE FROM merged WHERE _id=?', (i,))
        clone.commit()
        actual = {r[0]: tuple(r) for r in clone.execute('SELECT '+','.join(FIELDS)+' FROM merged')}
        if actual != {k: v for k, v in initial_merged.items() if k not in removed}:
            raise ValueError('Deletion changed another surviving association')
        try:
            clone.executescript(ddl if ddl is not None else STAGED_DDL.read_text())
            if not constraints_present(clone):
                result['reason_code'] = 'REQUIRED_CONSTRAINTS_ABSENT'
            elif clone.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                result['reason_code'] = 'SQLITE_INTEGRITY_CHECK_FAILED'
            elif list(clone.execute('PRAGMA foreign_key_check')):
                result['reason_code'] = 'FOREIGN_KEY_VIOLATION'
            elif not inspect_database(clone)['safe_to_install_unique_indexes']:
                result['reason_code'] = 'REMAINING_LEGACY_BLOCKERS'
            else:
                result['simulation'] = 'PASS_IN_MEMORY_ONLY'
        except sqlite3.DatabaseError:
            result['reason_code'] = 'DDL_REHEARSAL_FAILED'
        # Undo only our proposed DDL on disposable clone, then reinsert every
        # approved row with original _id, settings and NULL status unchanged.
        clone.execute('DROP INDEX IF EXISTS polaris_merged_real_id_unique')
        clone.execute('DROP INDEX IF EXISTS polaris_merged_source_identity_unique')
        clone.execute('DROP TABLE IF EXISTS polaris_restore_ledger')
        query = 'INSERT INTO merged('+','.join(FIELDS)+') VALUES('+','.join('?' for _ in FIELDS)+')'
        for row in removed_rows:
            clone.execute(query, row)
        clone.commit()
        result['restoration_verified'] = (fingerprint_database(clone) == baseline and
                                          {r[0]: tuple(r) for r in clone.execute(
                                              'SELECT '+','.join(FIELDS)+' FROM merged')} == initial_merged)
        if not result['restoration_verified']:
            result['simulation'] = 'FAILED_IN_MEMORY_ONLY'
            result['reason_code'] = 'UNDO_DID_NOT_RESTORE_ORIGINAL_ROWS'
        if result['reason_code'] is None and result['simulation'] != 'PASS_IN_MEMORY_ONLY':
            result['reason_code'] = 'DDL_BLOCKED'
        result['readiness_for_human_review'] = result['simulation'] == 'PASS_IN_MEMORY_ONLY'
        return result
    finally:
        clone.close()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('database', type=Path, help='Consistent SQLite COPY')
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--template', action='store_true', help='Create unsigned approval template')
    mode.add_argument('--reviewed-approvals', type=Path, help='Operator-edited approval JSON')
    p.add_argument('--report', type=Path, required=True, help='NEW JSON result only, no overwrite')
    args = p.parse_args(argv)
    try:
        if not args.database.is_file():
            raise FileNotFoundError('No consistent SQLite copy')
        conn = sqlite3.connect(args.database.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            conn.execute('PRAGMA query_only=ON')
            if args.template:
                report = approval_template(conn)
                status = 2  # An unapproved template can NEVER green-light migration.
            else:
                submitted = json.loads(args.reviewed_approvals.read_text())
                report = rehearse_approved(conn, submitted)
                status = 2  # Even a passing in-memory test requires migration approval.
            save_report_without_overwrite(args.database, args.report,
                                          json.dumps(report, sort_keys=True, indent=2))
            print(json.dumps({'report_written': True, 'simulation': report.get('simulation'),
                              'migration_approved': False}, sort_keys=True))
            return status
        finally:
            conn.close()
    except (OSError, ValueError, KeyError, TypeError, sqlite3.DatabaseError) as exc:
        print(json.dumps({'report_written': False, 'error_type': type(exc).__name__,
                          'migration_approved': False}), file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
