"""Strict, READ-ONLY restore-v2 physical graph audit over Spike-001 migration14.

This is a stronger gate than uniqueness-index installation: a database may
safely accept indexes while containing incomplete virtual parents which may
never be silently reattached or considered a completed restore.

Does not validate full BackupManga user metadata. Even PASS does not authorize
removing the v2 preflight guard. No JSON1/SQLDelight/Android dependency.
"""
from __future__ import annotations
import json
import re
import sqlite3
import uuid

VIRTUAL_SOURCE = 6969
UUID_MEMO_KEY = 'polaris.merge.work.uuid'
UUID_PARENT_PREFIX = 'merged://polaris/'
_DIGEST = re.compile(r'^[0-9a-f]{64}$')


def _canonical(raw: str) -> bool:
    try:
        return isinstance(raw, str) and str(uuid.UUID(raw)) == raw
    except (ValueError, TypeError, AttributeError):
        return False


def _memo_obj(value) -> dict | None:
    try:
        decoded = json.loads(value)
        return decoded if isinstance(decoded, dict) else None
    except (TypeError, ValueError, UnicodeError):
        return None


def _schema(db: sqlite3.Connection) -> set[str]:
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def audit_v2_restore_readiness(db: sqlite3.Connection) -> tuple[str, ...]:
    """Return ONLY anonymous reason codes; never URLs, UUIDs, notes, titles.

    This audit MUST run inside the same transaction as the v2 parent writes in
    a future production adapter. A standalone PASS does not protect races.
    """
    reasons: set[str] = set()
    if not {'mangas', 'merged', 'polaris_restore_ledger'} <= _schema(db):
        return ('REQUIRED_RESTORE_TABLE_MISSING',)
    try:
        parents = {r[0]: (r[1], r[2], r[3]) for r in db.execute(
            'SELECT _id,source,url,memo FROM mangas WHERE source=? OR _id IN '
            '(SELECT merge_id FROM merged) OR _id IN '
            '(SELECT parent_manga_id FROM polaris_restore_ledger)',
            (VIRTUAL_SOURCE,))}
        links = list(db.execute('SELECT merge_id,merge_url,manga_id,manga_url,manga_source,'
                                'info_manga,get_chapter_updates,download_chapters FROM merged'))
        grouped: dict[int, list[tuple]] = {}
        for edge in links:
            grouped.setdefault(edge[0], []).append(edge)
        seen_urls: dict[str, int] = {}
        for mid, (source, url, _) in parents.items():
            if source != VIRTUAL_SOURCE or not isinstance(url, str):
                continue
            if url in seen_urls and seen_urls[url] != mid:
                reasons.add('DUPLICATE_VIRTUAL_URL')
            seen_urls[url] = mid
        for mid, (source, url, memo) in parents.items():
            if source != VIRTUAL_SOURCE:
                reasons.add('MERGE_PARENT_WRONG_SOURCE')
            if not isinstance(url, str) or not url.strip():
                reasons.add('INVALID_PARENT_URL')
            if source != VIRTUAL_SOURCE:
                continue
            roots = [e for e in grouped.get(mid, ()) if e[4] == VIRTUAL_SOURCE]
            if len(roots) != 1:
                reasons.add('ROOT_REFERENCE_CARDINALITY')
            for root in roots:
                if root[2] != mid or root[3] != url or root[1] != url or root[5]:
                    reasons.add('ROOT_REFERENCE_IDENTITY')
            obj = _memo_obj(memo)
            if obj is None:
                reasons.add('INVALID_PARENT_MEMO')
        physical_cache: dict[tuple[int, str], list[int]] = {}
        for e in links:
            parent_id, merge_url, child_id, child_url, child_source, *_ = e
            parent = parents.get(parent_id)
            if parent is None or parent[0] != VIRTUAL_SOURCE:
                reasons.add('MERGE_PARENT_WRONG_SOURCE')
                continue
            if merge_url != parent[1]:
                reasons.add('MERGE_URL_DRIFT')
            if not isinstance(child_url, str) or not child_url.strip():
                reasons.add('INVALID_CHILD_IDENTITY')
                continue
            if child_source == VIRTUAL_SOURCE:
                if child_id != parent_id or child_url != parent[1]:
                    reasons.add('ROOT_REFERENCE_IDENTITY')
                continue
            key = (child_source, child_url)
            if key not in physical_cache:
                physical_cache[key] = [r[0] for r in db.execute(
                    'SELECT _id FROM mangas WHERE source=? AND url=?', key)]
            if child_id is not None:
                if physical_cache[key] != [child_id]:
                    reasons.add('REAL_CHILD_IDENTITY_CONFLICT')
                if child_id == parent_id:
                    reasons.add('SELF_LINK_AS_REAL_CHILD')
            # For a deliberately pending child ID, a real row may now exist;
            # never relink it implicitly during replay.
        claims: dict[str, set[int]] = {}
        for mid, (source, url, memo) in parents.items():
            if source != VIRTUAL_SOURCE:
                continue
            obj = _memo_obj(memo)
            if obj is None or UUID_MEMO_KEY not in obj:
                continue  # legacy manual merge with valid root is supported
            raw = obj[UUID_MEMO_KEY]
            if not _canonical(raw):
                reasons.add('INVALID_UUID_MEMO')
                continue
            claims.setdefault(raw, set()).add(mid)
        ledger_rows = list(db.execute(
            'SELECT archive_uuid,parent_manga_id,archive_digest FROM polaris_restore_ledger'))
        for archive_uuid, parent_id, digest in ledger_rows:
            if not _canonical(archive_uuid):
                reasons.add('INVALID_LEDGER_UUID')
                continue
            if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
                reasons.add('INVALID_ARCHIVE_DIGEST')
            parent = parents.get(parent_id)
            if parent is None or parent[0] != VIRTUAL_SOURCE:
                reasons.add('INVALID_LEDGER_PARENT')
                continue
            if parent[1] != UUID_PARENT_PREFIX + archive_uuid:
                reasons.add('LEDGER_PARENT_URL_DRIFT')
            if parent_id not in claims.get(archive_uuid, ()):
                reasons.add('LEDGER_MEMO_DISAGREEMENT')
        ledger_claims = {(u, pid) for u, pid, _ in ledger_rows if _canonical(u)}
        for value, owners in claims.items():
            if len(owners) != 1:
                reasons.add('DUPLICATE_UUID_CLAIM')
            for mid in owners:
                if (value, mid) not in ledger_claims:
                    reasons.add('UUID_CLAIM_WITHOUT_LEDGER')
        if db.execute('PRAGMA foreign_key_check').fetchall():
            reasons.add('FOREIGN_KEY_VIOLATION')
    except (sqlite3.DatabaseError, ValueError, TypeError, UnicodeError):
        reasons.add('AUDIT_UNVERIFIABLE')
    return tuple(sorted(reasons))
