#!/usr/bin/env python3
"""Read-only migration preflight for Polaris R001 legacy merged manga databases.

Blocks schema evolution if duplicate or ambiguous data would invalidate
physical uniqueness or silently damage a user's source choices. NEVER mutates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sqlite3
import sys
from uuid import UUID

VIRTUAL = 6969
MEMO_KEY = 'polaris.merge.work.uuid'
LIMIT = 100


def uuid_is_canonical(value):
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except (TypeError, ValueError, AttributeError):
        return False


def parse_memo(raw):
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (ValueError, TypeError, UnicodeError):
        return None


def inspect_database(db: sqlite3.Connection):
    """Read original mangas/merged/optional ledger without writing to the DB."""
    db.row_factory = sqlite3.Row
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    findings = []
    counts = Counter()

    def finding(code, blocker=True, *, parent_id=None, row_id=None, count=None):
        counts[code] += 1
        if len(findings) < LIMIT:
            record = {'code': code, 'severity': 'blocker' if blocker else 'warning'}
            if parent_id is not None: record['parent_id'] = parent_id
            if row_id is not None: record['row_id'] = row_id
            if count is not None: record['count'] = count
            findings.append(record)

    if not {'mangas', 'merged'}.issubset(tables):
        finding('REQUIRED_SCHEMA_MISSING')
        return {'safe_to_install_unique_indexes': False, 'findings': findings,
                'counts': dict(counts), 'scanned': {}, 'truncated': False}

    parents = {r['_id']: r for r in db.execute(
        'SELECT _id,source,url,memo FROM mangas WHERE source=?', (VIRTUAL,))}
    references = list(db.execute('SELECT _id,merge_id,merge_url,manga_id,manga_url,'
                                 'manga_source,info_manga FROM merged ORDER BY _id'))
    by_parent = defaultdict(list)
    for row in references:
        by_parent[row['merge_id']].append(row)

    has_ledger = 'polaris_restore_ledger' in tables
    registered = {}
    if has_ledger:
        for entry in db.execute('SELECT archive_uuid,parent_manga_id,archive_digest '
                                'FROM polaris_restore_ledger'):
            registered[entry['parent_manga_id']] = entry['archive_uuid']
            if not uuid_is_canonical(entry['archive_uuid']) or not entry['archive_digest']:
                finding('INVALID_LEDGER_ENTRY', parent_id=entry['parent_manga_id'])
            parent = parents.get(entry['parent_manga_id'])
            if parent is None:
                finding('LEDGER_PARENT_MISSING_OR_NONVIRTUAL', parent_id=entry['parent_manga_id'])

    uuid_map = defaultdict(list)
    for pid, parent in parents.items():
        memo = parse_memo(parent['memo'])
        if memo is None:
            finding('INVALID_VIRTUAL_MEMO', parent_id=pid)
            continue
        if MEMO_KEY in memo:
            uid = memo[MEMO_KEY]
            if not uuid_is_canonical(uid):
                finding('INVALID_VIRTUAL_UUID', parent_id=pid)
            else:
                uuid_map[uid].append(pid)
                if registered.get(pid) != uid:
                    finding('UUID_WITHOUT_MATCHING_LEDGER', parent_id=pid)
        elif pid in registered:
            finding('LEDGER_UUID_NOT_IN_PARENT_MEMO', parent_id=pid)
    for pids in uuid_map.values():
        if len(pids) > 1:
            for pid in pids:
                finding('DUPLICATE_VIRTUAL_UUID', parent_id=pid, count=len(pids))

    # Mirrors the UNIQUE(merge_id,manga_source,manga_url) migration constraint.
    # Detect duplicate source+URL across NULL-pending and resolved rows.
    seen_identity = defaultdict(list)
    seen_real_id = defaultdict(list)
    for row in references:
        pid = row['merge_id']
        seen_identity[(pid, row['manga_source'], row['manga_url'])].append(row['_id'])
        if row['manga_id'] is not None:
            seen_real_id[(pid, row['manga_id'])].append(row['_id'])
    for (pid, _, _), duplicates in seen_identity.items():
        if len(duplicates) > 1:
            finding('DUPLICATE_LINK_SOURCE_IDENTITY', parent_id=pid,
                    row_id=duplicates[0], count=len(duplicates))
    for (pid, _), duplicates in seen_real_id.items():
        if len(duplicates) > 1:
            finding('DUPLICATE_LINK_REAL_MANGA_ID', parent_id=pid,
                    row_id=duplicates[0], count=len(duplicates))

    # All parent references must map back to an actual virtual manga row;
    # otherwise the proposed new FK/ledger should never be applied blindly.
    root_groups = defaultdict(list)
    for row in references:
        pid, src, child_id, url = (row['merge_id'], row['manga_source'],
                                   row['manga_id'], row['manga_url'])
        parent = parents.get(pid)
        if parent is None:
            finding('REFERENCE_PARENT_MISSING_OR_NONVIRTUAL', parent_id=pid, row_id=row['_id'])
            continue
        if row['merge_url'] != parent['url']:
            finding('PARENT_URL_MISMATCH', parent_id=pid, row_id=row['_id'])
        if src == VIRTUAL:
            root_groups[pid].append(row)
            if child_id != pid or url != parent['url'] or row['info_manga']:
                finding('INVALID_VIRTUAL_ROOT', parent_id=pid, row_id=row['_id'])
            continue
        if src is None or not str(url).strip():
            finding('INVALID_CHILD_SOURCE_IDENTITY', parent_id=pid, row_id=row['_id'])
        if child_id is not None:
            matches = list(db.execute('SELECT _id FROM mangas WHERE source=? AND url=?',
                                      (src, url)))
            if len(matches) != 1 or matches[0]['_id'] != child_id:
                finding('RESOLVED_CHILD_IDENTITY_AMBIGUOUS', parent_id=pid, row_id=row['_id'], count=len(matches))
        # Pending rows are deliberately not relinked: even if a real child is
        # present on the device, restoring them would undo a user's choice.

    for pid in parents:
        roots = root_groups[pid]
        if len(roots) != 1:
            finding('VIRTUAL_ROOT_MISSING_OR_DUPLICATED', parent_id=pid, count=len(roots))
        if not by_parent[pid]:
            finding('VIRTUAL_PARENT_HAS_NO_REFERENCES', parent_id=pid)

    # Foreign-key check is read-only and catches hard-to-spot legacy orphans.
    for row in db.execute('PRAGMA foreign_key_check'):
        finding('FOREIGN_KEY_VIOLATION', row_id=row[1])

    blockers = any(f['severity'] == 'blocker' for f in findings)
    return {'safe_to_install_unique_indexes': not blockers,
            'findings': findings, 'counts': dict(sorted(counts.items())),
            'scanned': {'virtual_parents': len(parents), 'merge_references': len(references),
                        'ledger_present': has_ledger},
            'truncated': sum(counts.values()) > len(findings)}


def inspect_file(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'No database found: {path}')
    # URI mode=ro prevents accidental updates even if future code changes.
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        return inspect_database(connection)
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path, help='Path to a COPY of a Yomotsu/Polaris SQLite DB')
    parser.add_argument('--report', type=Path, help='Write redacted JSON report here (never modifies database)')
    args = parser.parse_args(argv)
    try:
        report = inspect_file(args.database)
    except (sqlite3.DatabaseError, OSError, FileNotFoundError) as exc:
        print(json.dumps({'error': str(exc), 'safe_to_install_unique_indexes': False}), file=sys.stderr)
        return 3
    output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(output + '\n', encoding='utf-8')
    print(output)
    return 0 if report['safe_to_install_unique_indexes'] else 2

if __name__ == '__main__':
    sys.exit(main())
