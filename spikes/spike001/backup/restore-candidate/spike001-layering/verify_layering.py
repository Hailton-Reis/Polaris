"""Fail-closed host compatibility rehearsal of ACTUAL staged Spike-001 migration14.

Nothing here applies changes to a user's database or the Android tree.
The base Yomotsu schema uses the existing manually transcribed host fixture;
Spike-001 .sq / .sqm are read from the actual Polaris repository tree.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
BACKUP = HERE.parents[1]  # /spikes/spike001/backup
SPIKE001 = BACKUP.parent
STAGED_SQL = SPIKE001 / 'new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq'
STAGED_MIGRATION = SPIKE001 / 'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm'
LEDGER_CANDIDATE = BACKUP / 'restore-candidate/atomic-sqlite/atomic_parent_restore_candidate.sql'
OLD_BRIDGE = BACKUP / 'restore-candidate/pinned-schema-bridge/merged_bridge_candidate.sql'
sys.path.insert(0, str(BACKUP / 'restore-candidate/pinned-schema-bridge'))
from pinned_schema_fixture import connect as pinned_connect  # pinned-shaped, NOT real adapter

PINNED_YOMOTSU = '0fb80c439ef816eeb50674f1b90af39918b176d8'
STAGED_BLOBS = {
    'merged.sq':'3e9fb499d0e1d0523aaaaaae336dd9bf5b2d4b62',
    '14.sqm':'8f23dc5219f49a0368705ba21d0c4e5a0d7fb1fb',
}
SOURCE_VIRTUAL = 6969
UUID_KEY = 'polaris.merge.work.uuid'


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def verify_original_spike_source() -> None:
    for name, path in (('merged.sq', STAGED_SQL), ('14.sqm', STAGED_MIGRATION)):
        if git_blob(path) != STAGED_BLOBS[name]:
            raise ValueError(f'Spike-001 {name} has drifted from known, previously built source; review differences')


def ddl_from_merged_sq() -> str:
    """DDL in the true Spike-001 .sq, stripping ONLY the Boolean annotation/import."""
    raw = STAGED_SQL.read_text()
    head = raw.split('selectByMergeId:', 1)[0]
    if 'selectByMergeId:' not in raw or head.count('CREATE TABLE merged(') != 1:
        raise ValueError('Unexpected merged.sq structure')
    return head.replace('import kotlin.Boolean;', '').replace('INTEGER AS Boolean', 'INTEGER')


def new_baseline() -> sqlite3.Connection:
    return pinned_connect()


def apply_spike14(db: sqlite3.Connection) -> None:
    verify_original_spike_source()
    db.executescript(STAGED_MIGRATION.read_text())


def native_columns(db: sqlite3.Connection, name: str) -> tuple[str, ...]:
    if name not in {'merged', 'mangas'}:
        raise ValueError('Unexpected table')
    return tuple(x[1] for x in db.execute(f'PRAGMA table_info("{name}")'))


def sql_objects(db: sqlite3.Connection) -> dict[str, str]:
    return {n: typ for n, typ in db.execute("SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}


def audit_existing_links(db: sqlite3.Connection) -> tuple[str, ...]:
    """Read-only safety gate before installing constraints, not a migration.

    Requires valid root parent/child keys, no existing untracked UUID claim,
    no duplicate source identities or resolved physical child references.
    No writes, no title-based repair, no silent deduplication.
    """
    reasons: set[str] = set()
    tables = sql_objects(db)
    if tables.get('merged') != 'table' or tables.get('mangas') != 'table':
        return ('SPIKE14_MISSING',)
    for row in db.execute('''
        SELECT merge_id,manga_source,manga_url,COUNT(*) AS n FROM merged
        GROUP BY merge_id,manga_source,manga_url HAVING n>1'''):
        reasons.add('DUPLICATE_SOURCE_IDENTITY')
    for row in db.execute('''
        SELECT merge_id,manga_id,COUNT(*) AS n FROM merged WHERE manga_id IS NOT NULL
        GROUP BY merge_id,manga_id HAVING n>1'''):
        reasons.add('DUPLICATE_REAL_ROW')
    for merge_id, msource, murl, mid, owner_source, owner_url, merge_url in db.execute('''
       SELECT e.merge_id,e.manga_source,e.manga_url,e.manga_id,m.source,m.url,e.merge_url
       FROM merged e LEFT JOIN mangas m ON m._id=e.merge_id'''):
        if owner_source != SOURCE_VIRTUAL or not owner_url or not str(owner_url).strip():
            reasons.add('INVALID_VIRTUAL_PARENT')
        if owner_url != merge_url:
            reasons.add('STALE_MERGE_PARENT_URL')
        if not murl or not str(murl).strip() or msource is None:
            reasons.add('INVALID_LINK_IDENTITY')
        if mid is not None:
            children = db.execute('SELECT source,url FROM mangas WHERE _id=?',(mid,)).fetchall()
            if children != [(msource, murl)]:
                reasons.add('STALE_RESOLVED_CHILD')
            matching = db.execute('SELECT _id FROM mangas WHERE source=? AND url=?',(msource,murl)).fetchall()
            if matching != [(mid,)]:
                reasons.add('AMBIGUOUS_SOURCE_ROW')
    seen_uuid: dict[str, int] = {}
    for mid, source, url, memo in db.execute('SELECT _id,source,url,memo FROM mangas WHERE source=?',(SOURCE_VIRTUAL,)):
        try:
            obj = json.loads(memo)
        except (ValueError, TypeError, UnicodeDecodeError):
            reasons.add('UNVERIFIABLE_VIRTUAL_MEMO')
            continue
        if not isinstance(obj, dict):
            reasons.add('UNVERIFIABLE_VIRTUAL_MEMO')
            continue
        if UUID_KEY in obj:
            if not isinstance(obj[UUID_KEY], str) or not obj[UUID_KEY].strip():
                reasons.add('UNVERIFIABLE_VIRTUAL_MEMO')
                continue
            u = obj[UUID_KEY]
            if u in seen_uuid:
                reasons.add('DUPLICATE_UUID_CLAIM')
            seen_uuid[u] = mid
            # Existing pre-ledger UUID identities must be reconciled manually.
            if tables.get('polaris_restore_ledger') != 'table':
                reasons.add('UNTRACKED_UUID_CLAIM')
            else:
                ledger = db.execute('SELECT parent_manga_id FROM polaris_restore_ledger WHERE archive_uuid=?',(u,)).fetchall()
                if ledger != [(mid,)]:
                    reasons.add('UNTRACKED_UUID_CLAIM')
    if db.execute('PRAGMA foreign_key_check').fetchall():
        reasons.add('FOREIGN_KEY_VIOLATION')
    return tuple(sorted(reasons))


def in_memory_rehearsal(source: sqlite3.Connection) -> dict[str, Any]:
    """Back up connection into in-memory clone; source remains byte/data unchanged."""
    result: dict[str, Any] = {'live_database_modified': False, 'applied_to_android': False}
    errors = audit_existing_links(source)
    result['blockers'] = errors
    if errors:
        result['status'] = 'BLOCKED_READ_ONLY'
        return result
    clone = sqlite3.connect(':memory:')
    try:
        source.backup(clone)
        clone.execute('PRAGMA foreign_keys=ON')
        before = list(clone.execute('SELECT * FROM mangas ORDER BY _id')), list(clone.execute('SELECT * FROM merged ORDER BY _id'))
        try:
            clone.executescript(LEDGER_CANDIDATE.read_text())
            after = list(clone.execute('SELECT * FROM mangas ORDER BY _id')), list(clone.execute('SELECT * FROM merged ORDER BY _id'))
            if before != after:
                result['status'] = 'FAILED_ORIGINAL_ROW_DRIFT'
            elif clone.execute('PRAGMA foreign_key_check').fetchall():
                result['status'] = 'FAILED_FOREIGN_KEYS'
            elif not {'polaris_restore_ledger','polaris_merged_source_identity_unique','polaris_merged_real_id_unique'} <= sql_objects(clone).keys():
                result['status'] = 'FAILED_MISSING_CONSTRAINTS'
            else:
                result['status'] = 'PASS_IN_MEMORY_ONLY'
        except sqlite3.DatabaseError:
            result['status'] = 'FAILED_DDL_REHEARSAL'
    finally:
        clone.close()
    return result


def seed_parent(db: sqlite3.Connection, parent_id: int = 500, child_id: int = 101) -> None:
    db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (parent_id, SOURCE_VIRTUAL, f'merged://polaris/{parent_id}', 'Parent', 0,1,1,0,0,0,0))
    db.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (child_id, 77, f'/real/{child_id}', 'Real', 0,1,1,0,0,0,0))


def seed_link(db: sqlite3.Connection, parent_id: int = 500, child_id: int|None = 101,
              source: int = 77, url: str = '/real/101', priority: int = 1) -> None:
    db.execute('''INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,
    download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source)
    VALUES (?,?,?,?,?,?,?,?,?,?)''', (1,1,2,priority,0,parent_id,f'merged://polaris/{parent_id}',child_id,url,source))


def verify_staged_and_migration_shape() -> tuple[tuple[str,...], list[tuple], list[tuple]]:
    """Run both authored DDLs on real SQLite, compare columns/FKs/indices."""
    verify_original_spike_source()
    a = new_baseline(); b = new_baseline()
    try:
        apply_spike14(a)
        b.executescript(ddl_from_merged_sq())
        cols_a=native_columns(a,'merged'); cols_b=native_columns(b,'merged')
        fk_a=list(a.execute('PRAGMA foreign_key_list(merged)'))
        fk_b=list(b.execute('PRAGMA foreign_key_list(merged)'))
        indices_a=[(x[1],x[2]) for x in a.execute('PRAGMA index_list(merged)')]
        indices_b=[(x[1],x[2]) for x in b.execute('PRAGMA index_list(merged)')]
        if (cols_a, fk_a, indices_a) != (cols_b, fk_b, indices_b):
            raise ValueError('Pinned Spike-001 migration14 and merged.sq CREATE DDL diverge')
        return cols_a, fk_a, indices_a
    finally:
        a.close(); b.close()
