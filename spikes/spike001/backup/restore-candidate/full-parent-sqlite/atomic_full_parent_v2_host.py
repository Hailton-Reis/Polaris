"""Polaris R001 P0: isolated SQLite rehearsal of UUID-bound FULL parent metadata.

HOST-ONLY reference. NOT Yomotsu schema/SQLDelight/Android. Parent sources and
backup fields mirror pinned Yomotsu DTO names, with memo bytes encoded as base64.
Never wire into a production restore or lift the v2 preflight guard.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import sqlite3
import uuid
from typing import Any

VIRTUAL = 6969
UUID_MEMO = 'polaris.merge.work.uuid'
MANGA_FIELDS = frozenset('''source url title artist author description genre status thumbnailUrl
 dateAdded viewer chapters categories tracking favorite chapterFlags viewer_flags
 history updateStrategy lastModifiedAt favoriteModifiedAt excludedScanlators
 version notes initialized memo_b64'''.split())
CHAPTER_FIELDS = frozenset('''url name scanlator read bookmark lastPageRead dateFetch dateUpload
 chapterNumber sourceOrder lastModifiedAt version memo_b64'''.split())
HISTORY_FIELDS = frozenset('url lastRead readDuration'.split())
TRACKING_FIELDS = frozenset('''syncId libraryId mediaIdInt trackingUrl title lastChapterRead
 totalChapters score status startedReadingDate finishedReadingDate private mediaId'''.split())


def jdump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def memo_object(b64: str) -> dict:
    if not isinstance(b64, str):
        raise ValueError('Memo must be encoded as canonical base64')
    try:
        raw = base64.b64decode(b64, validate=True)
        if base64.b64encode(raw).decode('ascii') != b64:
            raise ValueError('Noncanonical memo base64')
        result = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeError, binascii.Error) as e:
        raise ValueError('Invalid JSON memo bytes') from e
    if not isinstance(result, dict):
        raise ValueError('Memo must contain a JSON object')
    return result


def canonical_uuid(value: str) -> bool:
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def exact_keys(item: dict, allowed: frozenset, kind: str) -> None:
    if not isinstance(item, dict) or set(item) != allowed:
        raise ValueError(f'{kind}: fields missing, renamed or unsupported')


def validate_snapshot(uuid_key: str, snapshot: dict) -> None:
    if not canonical_uuid(uuid_key):
        raise ValueError('Noncanonical UUID')
    exact_keys(snapshot, MANGA_FIELDS, 'BackupManga')
    if snapshot['source'] != VIRTUAL or not isinstance(snapshot['url'], str) or not snapshot['url'] or not snapshot['title']:
        raise ValueError('Invalid virtual parent source, URL or title')
    memo = memo_object(snapshot['memo_b64'])
    if memo.get(UUID_MEMO) not in (None, uuid_key):
        raise ValueError('Parent memo refers to another UUID')
    if not isinstance(snapshot['categories'], list) or len(set(snapshot['categories'])) != len(snapshot['categories']):
        raise ValueError('Repeated category orders')
    for key in ('chapters', 'history', 'tracking', 'excludedScanlators'):
        if not isinstance(snapshot[key], list):
            raise ValueError(f'{key} is not a list')
    chapters = snapshot['chapters']
    for c in chapters:
        exact_keys(c, CHAPTER_FIELDS, 'BackupChapter')
        if not isinstance(c['url'], str) or not c['url'] or not c['name']:
            raise ValueError('Invalid chapter URL/name')
        memo_object(c['memo_b64'])
    urls = [c['url'] for c in chapters]
    if len(urls) != len(set(urls)):
        raise ValueError('Duplicate chapter URLs')
    for h in snapshot['history']:
        exact_keys(h, HISTORY_FIELDS, 'BackupHistory')
        if h['url'] not in urls:
            raise ValueError('BackupHistory missing its BackupChapter; refuse silent omission')
    if len(set(h['url'] for h in snapshot['history'])) != len(snapshot['history']):
        raise ValueError('Repeated history URL')
    for t in snapshot['tracking']:
        exact_keys(t, TRACKING_FIELDS, 'BackupTracking')
    if len(set(t['syncId'] for t in snapshot['tracking'])) != len(snapshot['tracking']):
        raise ValueError('Duplicate tracker ID')
    if len(set(snapshot['excludedScanlators'])) != len(snapshot['excludedScanlators']):
        raise ValueError('Duplicate excluded scanlator')
    # Strictly validate all values are representable in JSON (including NaN rejection).
    jdump(snapshot)


def install_host_schema(conn: sqlite3.Connection) -> None:
    conn.execute('PRAGMA foreign_keys = ON')
    conn.executescript('''
    CREATE TABLE mangas (
      _id INTEGER PRIMARY KEY, source INTEGER NOT NULL, url TEXT NOT NULL,
      title TEXT NOT NULL, payload_json TEXT NOT NULL, memo_json TEXT NOT NULL,
      UNIQUE(source,url)
    );
    CREATE TABLE polaris_restore_ledger (
      archive_uuid TEXT PRIMARY KEY, parent_manga_id INTEGER NOT NULL UNIQUE,
      association_digest TEXT NOT NULL, metadata_digest TEXT NOT NULL,
      FOREIGN KEY(parent_manga_id) REFERENCES mangas(_id) ON DELETE CASCADE
    );
    CREATE TABLE categories (_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
    CREATE TABLE mangas_categories (manga_id INTEGER, category_id INTEGER,
      PRIMARY KEY(manga_id,category_id), FOREIGN KEY(manga_id) REFERENCES mangas(_id),
      FOREIGN KEY(category_id) REFERENCES categories(_id));
    CREATE TABLE chapters (_id INTEGER PRIMARY KEY, manga_id INTEGER NOT NULL,
      url TEXT NOT NULL, payload_json TEXT NOT NULL,
      UNIQUE(manga_id,url), FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE CASCADE);
    CREATE TABLE history (chapter_id INTEGER PRIMARY KEY, payload_json TEXT NOT NULL,
      FOREIGN KEY(chapter_id) REFERENCES chapters(_id) ON DELETE CASCADE);
    CREATE TABLE tracking (manga_id INTEGER NOT NULL, tracker_id INTEGER NOT NULL,
      payload_json TEXT NOT NULL, PRIMARY KEY(manga_id,tracker_id),
      FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE CASCADE);
    CREATE TABLE excluded_scanlators (manga_id INTEGER NOT NULL, scanlator TEXT NOT NULL,
      PRIMARY KEY(manga_id,scanlator), FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE CASCADE);
    CREATE TABLE merged (parent_id INTEGER NOT NULL, source_id INTEGER NOT NULL,
      source_url TEXT NOT NULL, real_manga_id INTEGER, settings_json TEXT NOT NULL,
      PRIMARY KEY(parent_id,source_id,source_url),
      FOREIGN KEY(parent_id) REFERENCES mangas(_id) ON DELETE CASCADE,
      FOREIGN KEY(real_manga_id) REFERENCES mangas(_id));
    ''')
    conn.commit()


def validate_works(works: list[dict], archive_categories: dict[int, str]) -> None:
    if not works:
        raise ValueError('No full-parent v2 works')
    if len(set(w['uuid'] for w in works)) != len(works):
        raise ValueError('Duplicate parent UUID')
    if len(archive_categories.values()) != len(set(archive_categories.values())):
        raise ValueError('Ambiguous archived category names')
    for w in works:
        if set(w) != {'uuid', 'snapshot', 'edges'}:
            raise ValueError('Unexpected work contract')
        validate_snapshot(w['uuid'], w['snapshot'])
        seen = set()
        for e in w['edges']:
            if set(e) != {'source', 'url', 'real_id', 'pending', 'settings'}:
                raise ValueError('Unexpected edge contract')
            key = (e['source'],e['url'])
            if key in seen or e['source'] == VIRTUAL or not e['url']:
                raise ValueError('Duplicate or invalid real child identity')
            seen.add(key)
            if e['pending'] != (e['real_id'] is None) or e['real_id'] is not None and e['real_id'] <= 0:
                raise ValueError('Resolved/pending mismatch')
            jdump(e)
        for order in w['snapshot']['categories']:
            if order not in archive_categories or not archive_categories[order]:
                raise ValueError('Missing archive category order/name')


def desired_state(conn: sqlite3.Connection, parent_id: int, snapshot: dict, category_ids: list[int], edges: list[dict], memo: dict) -> bool:
    row = conn.execute('SELECT source,url,title,payload_json,memo_json FROM mangas WHERE _id=?', (parent_id,)).fetchone()
    if row != (VIRTUAL, 'merged://polaris/'+memo[UUID_MEMO], snapshot['title'], jdump(snapshot), jdump(memo)):
        return False
    if [r[0] for r in conn.execute('SELECT category_id FROM mangas_categories WHERE manga_id=? ORDER BY category_id',(parent_id,))] != sorted(category_ids):
        return False
    chapter_rows = conn.execute('SELECT _id,url,payload_json FROM chapters WHERE manga_id=?',(parent_id,)).fetchall()
    if sorted((c[1],c[2]) for c in chapter_rows) != sorted((c['url'],jdump(c)) for c in snapshot['chapters']):
        return False
    ids_by_url = {url:cid for cid,url,_ in chapter_rows}
    expected_hist = sorted((ids_by_url[h['url']],jdump(h)) for h in snapshot['history'])
    chapter_ids = [r[0] for r in chapter_rows]
    if chapter_ids:
        placeholders=','.join('?' for _ in chapter_ids)
        actual_hist = conn.execute('SELECT chapter_id,payload_json FROM history WHERE chapter_id IN ('+placeholders+')',chapter_ids).fetchall()
    else:
        actual_hist=[]
    if sorted(actual_hist) != expected_hist:
        return False
    if sorted(conn.execute('SELECT tracker_id,payload_json FROM tracking WHERE manga_id=?',(parent_id,)).fetchall()) != sorted((t['syncId'],jdump(t)) for t in snapshot['tracking']):
        return False
    if [r[0] for r in conn.execute('SELECT scanlator FROM excluded_scanlators WHERE manga_id=? ORDER BY scanlator',(parent_id,))] != sorted(snapshot['excludedScanlators']):
        return False
    actual_edges=conn.execute('SELECT source_id,source_url,real_manga_id,settings_json FROM merged WHERE parent_id=?',(parent_id,)).fetchall()
    expected_edges=[(e['source'],e['url'],e['real_id'],jdump(e['settings'])) for e in edges]
    return sorted(actual_edges,key=str) == sorted(expected_edges,key=str)


def restore_all_or_throw(conn: sqlite3.Connection, works: list[dict], archive_categories: dict[int,str], fail_after_parent: int | None = None) -> list[int]:
    """Single BEGIN IMMEDIATE hosts parent, ledger, full fields, all relations.

    Precondition: linked real source rows have already been strictly restored.
    No-op only on full on-disk equivalence of all covered fixture fields.
    """
    validate_works(works, archive_categories)
    if conn.in_transaction:
        raise RuntimeError('Outer restore transaction not supported by this isolated harness')
    conn.execute('BEGIN IMMEDIATE')
    result=[]
    try:
        for pos,w in enumerate(works):
            uuid_key=w['uuid']; snap=w['snapshot']; edges=w['edges']
            url='merged://polaris/'+uuid_key
            memo=dict(memo_object(snap['memo_b64']))
            memo[UUID_MEMO] = uuid_key
            cats=[]
            for order in snap['categories']:
                name=archive_categories[order]
                cat_rows=conn.execute('SELECT _id FROM categories WHERE name=?',(name,)).fetchall()
                if len(cat_rows)!=1 or cat_rows[0][0]<=0:
                    raise ValueError('Missing/ambiguous destination category: '+name)
                cats.append(cat_rows[0][0])
            if len(cats)!=len(set(cats)):
                raise ValueError('Collapsed destination category IDs')
            for edge in edges:
                if edge['real_id'] is not None:
                    exact=conn.execute('SELECT _id FROM mangas WHERE source=? AND url=?',(edge['source'],edge['url'])).fetchall()
                    if exact != [(edge['real_id'],)]:
                        raise ValueError('Real child source+URL ID collision')
            md=hashlib.sha256(jdump({'snapshot':snap,'categories':archive_categories}).encode()).hexdigest()
            assoc=hashlib.sha256(jdump(edges).encode()).hexdigest()
            ledger=conn.execute('SELECT parent_manga_id,association_digest,metadata_digest FROM polaris_restore_ledger WHERE archive_uuid=?',(uuid_key,)).fetchall()
            if len(ledger)>1:
                raise ValueError('Ambiguous UUID ledger')
            if ledger:
                pid,prev_assoc,prev_md=ledger[0]
                if (prev_assoc,prev_md)!=(assoc,md) or not desired_state(conn,pid,snap,cats,edges,memo):
                    raise ValueError('Existing parent is not an unchanged full metadata replay')
                result.append(pid)
                continue
            for other_id,other_memo in conn.execute('SELECT _id,memo_json FROM mangas WHERE source=?',(VIRTUAL,)):
                old=json.loads(other_memo)
                if old.get(UUID_MEMO)==uuid_key:
                    raise ValueError('Legacy UUID parent exists without ledger')
            if conn.execute('SELECT 1 FROM mangas WHERE source=? AND url=?',(VIRTUAL,url)).fetchone():
                raise ValueError('UUID-stable parent URL already exists without ledger')
            pid=conn.execute('INSERT INTO mangas(source,url,title,payload_json,memo_json) VALUES(?,?,?,?,?)',
                             (VIRTUAL,url,snap['title'],jdump(snap),jdump(memo))).lastrowid
            if not pid or pid<=0:
                raise ValueError('Failed to insert parent')
            conn.execute('INSERT INTO polaris_restore_ledger VALUES(?,?,?,?)',(uuid_key,pid,assoc,md))
            for cat_id in cats:
                conn.execute('INSERT INTO mangas_categories VALUES(?,?)',(pid,cat_id))
            chapters={}
            for ch in snap['chapters']:
                cid=conn.execute('INSERT INTO chapters(manga_id,url,payload_json) VALUES(?,?,?)',
                                 (pid,ch['url'],jdump(ch))).lastrowid
                chapters[ch['url']]=cid
            for history in snap['history']:
                conn.execute('INSERT INTO history VALUES(?,?)',(chapters[history['url']],jdump(history)))
            for tracking in snap['tracking']:
                conn.execute('INSERT INTO tracking VALUES(?,?,?)',(pid,tracking['syncId'],jdump(tracking)))
            for scanlator in snap['excludedScanlators']:
                conn.execute('INSERT INTO excluded_scanlators VALUES(?,?)',(pid,scanlator))
            for edge in edges:
                conn.execute('INSERT INTO merged VALUES(?,?,?,?,?)',(pid,edge['source'],edge['url'],edge['real_id'],jdump(edge['settings'])))
            result.append(pid)
            if fail_after_parent == pos:
                raise RuntimeError('Injected interruption after inserted full parent')
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return result
