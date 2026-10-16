#!/usr/bin/env python3
"""Polaris R001: prepare a redacted, review-only legacy-link reconciliation plan.

Never edits the supplied database. Optional simulation removes only byte-identical
extra merged rows inside a disposable in-memory clone and rehearses the staged
UNIQUE/ledger DDL there. NO automatic on-disk cleanup or migration exists here.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

from audit_legacy_merges import inspect_database, save_report_without_overwrite
from rehearse_restore_migration import rehearse_connection

FIELDS = (
    '_id', 'info_manga', 'get_chapter_updates', 'chapter_sort_mode',
    'chapter_priority', 'download_chapters', 'merge_id', 'merge_url',
    'manga_id', 'manga_url', 'manga_source',
)
ROOT_SOURCE = 6969
DEFAULT_DDL = (Path(__file__).resolve().parent.parent / 'atomic-sqlite' /
               'atomic_parent_restore_candidate.sql')


def _fingerprint(rows: list[tuple]) -> str:
    """Hash the exact row values, never display or include a URL in the report."""
    h = sha256(b'polaris-r001-reconciliation-v1\x00')
    for row in sorted(rows, key=lambda x: x[0]):
        encoded = json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode()
        h.update(len(encoded).to_bytes(8, 'big'))
        h.update(encoded)
    return h.hexdigest()


def candidate_plan(db: sqlite3.Connection) -> dict:
    """Group DUPLICATE edge conflicts transitively under BOTH future indexes.

    If row A shares a source identity with B, and B shares a real manga ID
    with C, A/B/C must be reviewed as ONE group, not incompatible pairwise
    'fixes'. Exact duplicates are potential manual review candidates only.
    """
    db.row_factory = sqlite3.Row
    schema = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'merged', 'mangas'} <= schema:
        return {'ready_for_review': False, 'reason': 'REQUIRED_SCHEMA_MISSING',
                'review_groups': [], 'summary': {'groups': 0}}
    rows = [tuple(r) for r in db.execute('SELECT '+','.join(FIELDS)+' FROM merged ORDER BY _id')]
    ids = [r[0] for r in rows]
    if len(ids) != len(set(ids)):
        return {'ready_for_review': False, 'reason': 'DUPLICATE_ROW_ID',
                'review_groups': [], 'summary': {'groups': 0}}
    by_id = {r[0]: r for r in rows}
    parent = {i: i for i in ids}

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    key_map = defaultdict(list)
    real_map = defaultdict(list)
    for r in rows:
        row_id, manga_id, manga_source = r[0], r[8], r[10]
        key_map[(r[6], manga_source, r[9])].append(row_id)
        if manga_id is not None:
            real_map[(r[6], manga_id)].append(row_id)
    for groups in (key_map, real_map):
        for members in groups.values():
            if len(members) > 1:
                for rid in members[1:]:
                    union(members[0], rid)

    components = defaultdict(list)
    for rid in ids:
        components[root(rid)].append(rid)

    groups = []
    for members in sorted(components.values(), key=min):
        if len(members) == 1:
            continue
        component_rows = [by_id[rid] for rid in sorted(members)]
        all_equal = len(set(r[1:] for r in component_rows)) == 1
        same_key = len({(r[6],r[10],r[9]) for r in component_rows}) == 1
        pending_states = {r[8] is None for r in component_rows}
        any_root = any(r[10] == ROOT_SOURCE for r in component_rows)
        same_real_id_diff_source = len({(r[10],r[9]) for r in component_rows}) > 1 and len({r[8] for r in component_rows if r[8] is not None}) < len([r for r in component_rows if r[8] is not None])
        if any_root:
            classification = 'VIRTUAL_ROOT_REVIEW_REQUIRED'
        elif len(pending_states) > 1 and same_key:
            classification = 'PENDING_VS_RESOLVED_MANUAL_REVIEW'
        elif same_real_id_diff_source:
            classification = 'REAL_IDENTITY_MANUAL_REVIEW'
        elif all_equal:
            classification = 'EXACT_DUPLICATE_CANDIDATE_REVIEW'
        else:
            classification = 'SETTINGS_OR_IDENTITY_MANUAL_REVIEW'
        keeper = min(members) if classification == 'EXACT_DUPLICATE_CANDIDATE_REVIEW' else None
        groups.append({
            'group_id': f'conflict-{min(members)}',
            'parent_ids': sorted(set(r[6] for r in component_rows)),
            'row_ids': sorted(members),
            'classification': classification,
            'row_fingerprint_sha256': _fingerprint(component_rows),
            'candidate_keep_row_id': keeper,
            'candidate_redundant_row_ids': [rid for rid in sorted(members) if rid != keeper] if keeper is not None else [],
            'automatic_changes_permitted': False,
            'manual_review_required': True,
        })
    counts = defaultdict(int)
    for g in groups:
        counts[g['classification']] += 1
    return {
        'ready_for_review': True,
        'schema_expected': True,
        'database_rows_sha256': _fingerprint(rows),
        'review_groups': groups,
        'summary': {'groups': len(groups), 'rows_in_conflicts': sum(len(g['row_ids']) for g in groups),
                    'classifications': dict(sorted(counts.items()))},
        'automatic_changes_permitted': False,
        'migration_approved': False,
    }


def simulate_exact_candidates(source: sqlite3.Connection, *, ddl: str | None = None) -> dict:
    """Dry-run exact duplicates in a separate :memory: clone, never live rows.

    Even byte-identical merged rows require human review before a real
    migration. Simulation merely shows whether exact consolidation would
    eliminate the candidate UNIQUE-index blockers; other audit findings remain.
    """
    plan = candidate_plan(source)
    result = {'simulation': 'NOT_RUN', 'source_database_modified': False,
              'candidate_removed_row_ids_in_memory_only': [], 'reason_code': None}
    if not plan['ready_for_review']:
        result.update(simulation='BLOCKED', reason_code=plan['reason'])
        return result
    clone = sqlite3.connect(':memory:')
    try:
        source.backup(clone)
        clone.execute('PRAGMA foreign_keys=ON')
        removals = [rid for g in plan['review_groups']
                    for rid in g['candidate_redundant_row_ids']]
        before = {tuple(row) for row in clone.execute('SELECT '+','.join(FIELDS)+' FROM merged')}
        for rid in removals:
            clone.execute('DELETE FROM merged WHERE _id=?', (rid,))
        clone.commit()
        after = {tuple(row) for row in clone.execute('SELECT '+','.join(FIELDS)+' FROM merged')}
        check = {r for r in before if r[0] not in removals}
        if after != check or len(before)-len(after) != len(removals):
            result.update(simulation='FAILED_IN_MEMORY_ONLY', reason_code='UNEXPECTED_SURVIVOR_CHANGE')
            return result
        migrated = rehearse_connection(clone, ddl if ddl is not None else DEFAULT_DDL.read_text())
        result.update(candidate_removed_row_ids_in_memory_only=removals,
                      remaining_blocker_codes=sorted(migrated['audit']['counts']),
                      simulation='PASS_IN_MEMORY_ONLY' if migrated['safe_to_install_unique_indexes'] else 'BLOCKED_IN_MEMORY_ONLY',
                      reason_code=migrated['reason_code'])
        return result
    finally:
        clone.close()


def inspect_copy(path: Path, simulate: bool = False) -> dict:
    if not path.is_file():
        raise FileNotFoundError('Supply a consistent existing SQLite database COPY')
    db = sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        plan = candidate_plan(db)
        audit = inspect_database(db)
        out = {'format': 'polaris-legacy-reconciliation-review-v1',
               'plan': plan, 'audit_summary': {'blocking_codes': sorted(audit['counts']),
                                               'safe_to_install_unique_indexes': audit['safe_to_install_unique_indexes']},
               'source_database_modified': False}
        if simulate:
            out['in_memory_simulation'] = simulate_exact_candidates(db)
        return out
    finally:
        db.close()


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('database', type=Path, help='Consistent COPY of Yomotsu/Polaris SQLite')
    p.add_argument('--report', type=Path, help='Create a NEW redacted JSON report, no overwrite')
    p.add_argument('--simulate-exact', action='store_true', help='Only on :memory: clone; never deletes original records')
    opts=p.parse_args(argv)
    try:
        out=inspect_copy(opts.database, opts.simulate_exact)
        rendered=json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True)
        if opts.report:
            save_report_without_overwrite(opts.database, opts.report, rendered)
        print(rendered)
        # An in-memory PASS never approves an on-disk migration. Conflicts
        # still require review, even when exact duplicates could be collapsed.
        review_needed = bool(out['plan'].get('review_groups'))
        blocked = not out['plan']['ready_for_review'] or not out['audit_summary']['safe_to_install_unique_indexes']
        if opts.simulate_exact and out['in_memory_simulation']['simulation'] != 'PASS_IN_MEMORY_ONLY':
            blocked = True
        return 2 if blocked or review_needed else 0
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({'error_type':type(exc).__name__, 'report_created':False,
                          'source_database_modified':False}), file=sys.stderr)
        return 3

if __name__=='__main__':
    sys.exit(main())