"""Host reference of PolarisAtomicVirtualWorkPort's intended SQLite semantics.

Candidate only: intentionally not installed into Kotlin/Android/SQLDelight.
The caller MUST have restored/validated all child Manga backups first.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import sqlite3
import uuid

MERGED_SOURCE = 6969
MEMO_KEY = 'polaris.merge.work.uuid'


@dataclass(frozen=True)
class Link:
    source: int
    url: str
    manga_id: int | None
    pending: bool
    info: bool = False
    updates: bool = True
    sort: int = 2
    priority: int = 0
    downloads: bool = False


@dataclass(frozen=True)
class Work:
    archive_uuid: str
    title: str
    children: tuple[Link, ...]
    root_sort: int = 2
    root_priority: int = 2147483647


def canonical(uuid_value: str) -> bool:
    try:
        return str(uuid.UUID(uuid_value)) == uuid_value
    except (ValueError, TypeError, AttributeError):
        return False


def fingerprint(work: Work) -> str:
    data = dict(title=work.title, root_sort=work.root_sort,
                root_priority=work.root_priority,
                children=[vars(link) for link in work.children])
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def validate_input(works: list[Work]) -> None:
    identifiers = [w.archive_uuid for w in works]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate archive parent UUID')
    for w in works:
        if not canonical(w.archive_uuid) or not w.title.strip() or not w.children:
            raise ValueError('Invalid portable parent identity/title/children')
        if w.root_sort not in range(5):
            raise ValueError('Invalid root sort mode')
        if sum(link.info for link in w.children) > 1:
            raise ValueError('Multiple metadata sources')
        keys = [(link.source, link.url) for link in w.children]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate source+URL within parent')
        for link in w.children:
            if link.source == MERGED_SOURCE or not link.url.strip():
                raise ValueError('Invalid real child source identity')
            if link.pending != (link.manga_id is None):
                raise ValueError('Pending flag and manga ID disagree')
            if link.manga_id is not None and link.manga_id <= 0:
                raise ValueError('Invalid positive real manga ID')
            if link.sort not in range(5):
                raise ValueError('Invalid chapter sort mode')


def rows_for_work(work: Work, parent_id: int, url: str) -> list[tuple]:
    links = [
        (int(l.info), int(l.updates), l.sort, l.priority, int(l.downloads),
         parent_id, url, l.manga_id, l.url, l.source)
        for l in work.children
    ]
    return links + [(0, 0, work.root_sort, work.root_priority, 0,
                     parent_id, url, parent_id, url, MERGED_SOURCE)]


def commit_all_or_throw(conn: sqlite3.Connection, works: list[Work],
                        fail_after_parent: int | None = None) -> list[int]:
    """BEGIN IMMEDIATE + physical ledger/edge indexes; all-or-nothing.

    Never take an already-present UUID from a parent without its ledger:
    that is an untracked legacy identity requiring an explicit migration.
    """
    validate_input(works)
    if conn.in_transaction:
        raise RuntimeError('Caller transaction must be explicit and exclusive')
    ids = []
    conn.execute('BEGIN IMMEDIATE')
    try:
        for position, work in enumerate(works):
            digest = fingerprint(work)
            rec = conn.execute('SELECT parent_manga_id,archive_digest '
                               'FROM polaris_restore_ledger WHERE archive_uuid=?',
                               (work.archive_uuid,)).fetchone()
            if rec:
                parent_id, existing_digest = rec
                if digest != existing_digest:
                    raise ValueError('Conflicting archive contents for registered UUID')
                parent = conn.execute('SELECT source,url,title,memo FROM mangas WHERE _id=?',
                                      (parent_id,)).fetchone()
                if not parent or parent[0] != MERGED_SOURCE or parent[2] != work.title:
                    raise ValueError('Registered virtual parent deleted or changed')
                try:
                    memo = json.loads(parent[3])
                except (ValueError, TypeError):
                    raise ValueError('Corrupt parent memo')
                if memo.get(MEMO_KEY) != work.archive_uuid:
                    raise ValueError('Restored parent UUID changed')
                actual = conn.execute('SELECT info_manga,get_chapter_updates,chapter_sort_mode,'
                    'chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source '
                    'FROM merged WHERE merge_id=? ORDER BY _id', (parent_id,)).fetchall()
                expected = rows_for_work(work, parent_id, parent[1])
                # Reject local edits. Repeating the identical archive may NOT
                # resurrect a deliberately removed child association.
                if sorted(actual, key=str) != sorted(expected, key=str):
                    raise ValueError('Local parent references changed since original import')
                ids.append(parent_id)
                continue

            # A UUID already held in any pre-ledger virtual memo is NOT free.
            # This host scan is explicit, portable SQLite (no JSON1 required).
            for old_id, old_memo in conn.execute('SELECT _id,memo FROM mangas WHERE source=?',
                                                 (MERGED_SOURCE,)):
                try:
                    info = json.loads(old_memo)
                except (ValueError, TypeError):
                    raise ValueError('Corrupt legacy virtual parent memo')
                if info.get(MEMO_KEY) == work.archive_uuid:
                    raise ValueError('UUID exists without ledger: manual reconciliation needed')
            for link in work.children:
                if link.manga_id is None:
                    continue
                rows = conn.execute('SELECT _id FROM mangas WHERE source=? AND url=?',
                                    (link.source, link.url)).fetchall()
                if rows != [(link.manga_id,)]:
                    raise ValueError('Real manga ambiguous or changed before transaction')
            url = 'merged://polaris/' + work.archive_uuid
            if conn.execute('SELECT 1 FROM mangas WHERE source=? AND url=?',
                            (MERGED_SOURCE, url)).fetchone():
                raise ValueError('Virtual URL collision; cannot create parent')
            memo = json.dumps({MEMO_KEY: work.archive_uuid}, separators=(',', ':')).encode()
            cursor = conn.execute('INSERT INTO mangas(source,url,title,status,favorite,initialized,'
                     'viewer,chapter_flags,cover_last_modified,date_added,memo) '
                     'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                     (MERGED_SOURCE, url, work.title, 0, 1, 1, 0, 0, 0, 0, memo))
            parent_id = cursor.lastrowid
            conn.execute('INSERT INTO polaris_restore_ledger(archive_uuid,parent_manga_id,archive_digest) '
                         'VALUES(?,?,?)', (work.archive_uuid, parent_id, digest))
            conn.executemany('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,'
                             'chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) '
                             'VALUES(?,?,?,?,?,?,?,?,?,?)', rows_for_work(work, parent_id, url))
            ids.append(parent_id)
            if fail_after_parent == position:
                raise RuntimeError('Injected failure after partially inserted virtual parent')
        conn.commit()
        return ids
    except BaseException:
        conn.rollback()
        raise
