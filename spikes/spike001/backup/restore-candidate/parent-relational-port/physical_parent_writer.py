"""Polaris R001: disposable SQLite execution of Yomotsu-shaped parent-LAST writes.

Intentionally NOT an Android SQLDelight generated adapter. Accepts the field
projection's property naming. No network, live user DB, migrations or backups.
Every write is in a single BEGIN IMMEDIATE / deferred-FK transaction.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import re
import sqlite3
import uuid as uuid_mod
from pathlib import Path
from typing import Callable, Optional, Sequence

HERE = Path(__file__).resolve().parent
QUERY_FILE = HERE.parent / 'parent-sqldelight-fields/PolarisParentMetadataRestore.sq'
SPIKE_SQL = HERE.parents[2] / 'new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq'
UUID_KEY = 'polaris.merge.work.uuid'
MERGED_SOURCE = 6969


def _parse_named_queries(path: Path) -> dict[str, str]:
    s = path.read_text()
    results: dict[str, str] = {}
    for match in re.finditer(r'(?ms)^([A-Za-z][A-Za-z0-9_]*):\s*\n(.*?;)', s):
        if match[1] in results:
            raise ValueError('DUPLICATE_SQLDELIGHT_QUERY')
        results[match[1]] = match[2].strip()
    return results


SQL = _parse_named_queries(QUERY_FILE)
MERGED_SQL = _parse_named_queries(SPIKE_SQL)


@dataclass(frozen=True)
class Edge:
    source: int
    url: str
    manga_id: Optional[int]
    priority: int
    info: bool = False
    updates: bool = False
    sort: int = 2
    download: bool = False


@dataclass(frozen=True)
class Batch:
    uuid: str
    digest: str
    # These keys match PolarisBackupMangaSqlProjection.ParentRow and .sq binding names.
    parent: dict
    chapters: list[dict]
    categories: list[int]
    history: list[dict]
    tracking: list[dict]
    exclusions: list[str]
    edges: list[Edge]


PARENT_BINDINGS = dict(
    destinationUrl='destinationUrl', artist='artist', author='author',
    description='description', genre='genre', title='title', status='status',
    thumbnailUrl='thumbnailUrl', favorite='favorite', lastUpdate='lastUpdate',
    nextUpdate='nextUpdate', initialized='initialized', viewer='viewer',
    chapterFlags='chapterFlags', coverLastModified='coverLastModified',
    dateAdded='dateAdded', updateStrategy='updateStrategy',
    calculateInterval='calculateInterval', lastModifiedAt='lastModifiedAt',
    favoriteModifiedAt='favoriteModifiedAt', version='version',
    notes='notes', memo='memo')
PARENT_PHYSICAL = dict(
    source='source', destinationUrl='url', artist='artist', author='author',
    description='description', genre='genre', title='title', status='status',
    thumbnailUrl='thumbnail_url', favorite='favorite', lastUpdate='last_update',
    nextUpdate='next_update', initialized='initialized', viewer='viewer',
    chapterFlags='chapter_flags', coverLastModified='cover_last_modified',
    dateAdded='date_added', updateStrategy='update_strategy',
    calculateInterval='calculate_interval', lastModifiedAt='last_modified_at',
    favoriteModifiedAt='favorite_modified_at', version='version',
    notes='notes', memo='memo', isSyncing='is_syncing')
CHAPTER_PHYSICAL = dict(
    chapterUrl='url', chapterName='name', scanlator='scanlator', read='read',
    bookmark='bookmark', lastPageRead='last_page_read',
    chapterNumber='chapter_number', sourceOrder='source_order',
    dateFetch='date_fetch', dateUpload='date_upload',
    chapterLastModifiedAt='last_modified_at', chapterVersion='version',
    chapterIsSyncing='is_syncing', chapterMemo='memo')
TRACK_PHYSICAL = dict(
    syncId='sync_id', remoteId='remote_id', libraryId='library_id',
    trackTitle='title', lastChapterRead='last_chapter_read',
    totalChapters='total_chapters', trackStatus='status', trackScore='score',
    remoteUrl='remote_url', startDate='start_date', finishDate='finish_date',
    isPrivate='private')


def _rows(con: sqlite3.Connection, sql: str, params=()) -> list[dict]:
    cursor = con.execute(sql, params)
    columns = [x[0] for x in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _exact_row(actual: dict, expected: dict, error: str) -> None:
    if actual != expected:
        raise ValueError(error)


def _memo_bytes(m: dict) -> bytes:
    if not isinstance(m, dict) or any(not isinstance(k, str) for k in m):
        raise ValueError('POLARIS_BAD_MEMO')
    return json.dumps(m, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def _genre_text(items: list[str]) -> str:
    if not isinstance(items, list) or any(not isinstance(x, str) or not x.strip() for x in items):
        raise ValueError('POLARIS_BAD_GENRE')
    encoded = ', '.join(items)
    decoded = encoded.split(', ') if encoded else []
    if decoded != items:
        raise ValueError('POLARIS_LOSSY_GENRE')
    return encoded


def _assert_batch_shape(b: Batch) -> None:
    try:
        uid = uuid_mod.UUID(b.uuid)
    except (ValueError, AttributeError, TypeError):
        raise ValueError('POLARIS_BAD_UUID') from None
    if str(uid) != b.uuid:
        raise ValueError('POLARIS_BAD_UUID')
    if not re.fullmatch(r'[a-f0-9]{64}', b.digest):
        raise ValueError('POLARIS_BAD_DIGEST')
    parent = b.parent
    if parent.get('destinationUrl') != 'merged://polaris/' + b.uuid or parent.get('source') != MERGED_SOURCE:
        raise ValueError('POLARIS_BAD_DESTINATION')
    memo = parent.get('memo')
    if not isinstance(memo, dict) or memo.get(UUID_KEY) != b.uuid:
        raise ValueError('POLARIS_BAD_MEMO_UUID')
    if parent.get('isSyncing') != 0 or not parent.get('title'):
        raise ValueError('POLARIS_BAD_PARENT_FIELDS')
    _memo_bytes(memo)
    _genre_text(parent.get('genre'))
    if len(set(b.categories)) != len(b.categories) or any(not isinstance(x, int) or x <= 0 for x in b.categories):
        raise ValueError('POLARIS_BAD_CATEGORIES')
    chapter_urls = [x.get('chapterUrl') for x in b.chapters]
    if any(not u or not isinstance(u, str) for u in chapter_urls) or len(chapter_urls) != len(set(chapter_urls)):
        raise ValueError('POLARIS_BAD_CHAPTER_URLS')
    if any(x.get('chapterIsSyncing') != 0 or not isinstance(x.get('chapterMemo'), dict) for x in b.chapters):
        raise ValueError('POLARIS_BAD_CHAPTER_FIELDS')
    if len(set(x.get('chapterUrl') for x in b.history)) != len(b.history) or any(x.get('chapterUrl') not in chapter_urls or x.get('readDuration', -1) < 0 for x in b.history):
        raise ValueError('POLARIS_BAD_HISTORY')
    if len(set(x.get('syncId') for x in b.tracking)) != len(b.tracking):
        raise ValueError('POLARIS_BAD_TRACKING')
    if len(set(b.exclusions)) != len(b.exclusions) or any(not x for x in b.exclusions):
        raise ValueError('POLARIS_BAD_EXCLUSIONS')
    if len(set((e.source,e.url) for e in b.edges)) != len(b.edges) or len(set(e.priority for e in b.edges)) != len(b.edges):
        raise ValueError('POLARIS_BAD_EDGES')
    if not b.edges or not any(e.source != MERGED_SOURCE for e in b.edges):
        raise ValueError('POLARIS_NO_SOURCE_CHILD')
    root = [e for e in b.edges if e.source == MERGED_SOURCE]
    if len(root) != 1 or root[0].url != parent['destinationUrl'] or root[0].info or root[0].updates or root[0].download:
        raise ValueError('POLARIS_INVALID_ROOT')
    if any(e.source == MERGED_SOURCE for e in b.edges if e is not root[0]):
        raise ValueError('POLARIS_EXTRA_ROOT')
    if any(not e.url or not isinstance(e.url, str) or (e.manga_id is not None and e.manga_id <= 0) for e in b.edges):
        raise ValueError('POLARIS_BAD_EDGE_FIELDS')
    if sum(int(e.info) for e in b.edges) != 1:
        raise ValueError('POLARIS_BAD_INFO_EDGE')


def _check_existing(con: sqlite3.Connection, b: Batch, pid: int):
    if _rows(con, 'SELECT _id FROM mangas WHERE source=? AND url=?', (MERGED_SOURCE, b.parent['destinationUrl'])):
        raise ValueError('POLARIS_PARENT_URL_OCCUPIED')
    if _rows(con, 'SELECT _id FROM mangas WHERE _id=?', (pid,)):
        raise ValueError('POLARIS_PARENT_ID_OCCUPIED')
    if _rows(con, 'SELECT * FROM polaris_restore_ledger WHERE archive_uuid=? OR parent_manga_id=?', (b.uuid, pid)):
        raise ValueError('POLARIS_PARENT_LEDGER_OCCUPIED')
    # Legacy UUID claim may not yet have a ledger record. Must find *every* virtual manga.
    for row in _rows(con, 'SELECT _id, memo FROM mangas WHERE source=?', (MERGED_SOURCE,)):
        try:
            seen = json.loads(row['memo'])
        except (ValueError, TypeError, UnicodeDecodeError):
            raise ValueError('POLARIS_UNVERIFIABLE_VIRTUAL_MEMO') from None
        if not isinstance(seen, dict):
            raise ValueError('POLARIS_UNVERIFIABLE_VIRTUAL_MEMO')
        if seen.get(UUID_KEY) == b.uuid:
            raise ValueError('POLARIS_LEGACY_UUID_OCCUPIED')
    for e in b.edges:
        if e.source == MERGED_SOURCE:
            if e.manga_id not in (None, pid):
                raise ValueError('POLARIS_WRONG_ROOT_ID')
            continue
        if e.manga_id is not None:
            matches = _rows(con, 'SELECT _id FROM mangas WHERE source=? AND url=?', (e.source,e.url))
            if len(matches) != 1 or matches[0]['_id'] != e.manga_id:
                raise ValueError('POLARIS_STALE_REAL_CHILD')
        else:
            # Pending snapshots MUST NOT auto-resolve or forge local IDs.
            if _rows(con, 'SELECT _id FROM mangas WHERE source=? AND url=?', (e.source,e.url)):
                raise ValueError('POLARIS_PENDING_CHILD_NOW_RESOLVED')
    for category in b.categories:
        if _rows(con, 'SELECT _id FROM categories WHERE _id=?',(category,)) != [{'_id':category}]:
            raise ValueError('POLARIS_UNRESOLVED_CATEGORY')


def _write_one(con: sqlite3.Connection, b: Batch, pid: int, fault: Optional[Callable[[str,int,sqlite3.Connection], None]]):
    if b.parent.get('reservedParentId', pid) != pid or any(
        c.get('parentId', pid) != pid for c in b.chapters
    ):
        raise ValueError('POLARIS_PREPARED_ID_MISMATCH')
    _check_existing(con,b,pid)
    params = {'parentId':pid}
    for category in b.categories:
        con.execute(SQL['insertPolarisRestoredCategoryExact'], dict(params, categoryId=category))
    chapter_id: dict[str,int] = {}
    for chapter in b.chapters:
        cp = dict(chapter, parentId=pid, chapterMemo=_memo_bytes(chapter['chapterMemo']))
        cid = con.execute(SQL['insertPolarisRestoredChapterFull'], cp).fetchone()[0]
        chapter_id[chapter['chapterUrl']] = cid
    for hist in b.history:
        con.execute(SQL['insertPolarisRestoredHistoryExact'], dict(chapterId=chapter_id[hist['chapterUrl']], lastRead=hist['lastRead'],readDuration=hist['readDuration']))
    for track in b.tracking:
        con.execute(SQL['insertPolarisRestoredTrackExact'], dict(track, parentId=pid))
    for exclusion in b.exclusions:
        con.execute(SQL['insertPolarisRestoredExclusionExact'], dict(parentId=pid, excludedScanlator=exclusion))
    for edge in b.edges:
        target = pid if edge.source == MERGED_SOURCE else edge.manga_id
        ep=dict(infoManga=int(edge.info),getChapterUpdates=int(edge.updates),chapterSortMode=edge.sort,
            chapterPriority=edge.priority,downloadChapters=int(edge.download),mergeId=pid,
            mergeUrl=b.parent['destinationUrl'],mangaId=target,mangaUrl=edge.url,mangaSource=edge.source)
        cur=con.execute(MERGED_SQL['insertReturningId'],ep)
        if cur.fetchone() is None:
            raise ValueError('POLARIS_SILENT_EDGE_DUPLICATE')
    con.execute('INSERT INTO polaris_restore_ledger(archive_uuid,parent_manga_id,archive_digest) VALUES(?,?,?)',(b.uuid,pid,b.digest))
    if fault: fault('before_parent',pid,con)
    p=dict(b.parent,parentId=pid,genre=_genre_text(b.parent['genre']),memo=_memo_bytes(b.parent['memo']))
    created=con.execute(SQL['insertPolarisRestoredReservedParentLast'],p).fetchone()[0]
    if created != pid:
        raise ValueError('POLARIS_PARENT_ROW_ID_CHANGED')
    if fault: fault('before_readback',pid,con)
    _assert_readback(con,b,pid)


def _assert_readback(con:sqlite3.Connection,b:Batch,pid:int):
    parents=_rows(con, SQL['selectPolarisRestoredParentFull'],{'parentId':pid})
    if len(parents)!=1:
        raise ValueError('POLARIS_PARENT_READBACK_FAILED')
    parent_expected={x:b.parent[x] for x in PARENT_PHYSICAL}
    parent_expected['genre']=_genre_text(b.parent['genre'])
    parent_expected['memo']=_memo_bytes(b.parent['memo'])
    fields={col:parent_expected[x] for x,col in PARENT_PHYSICAL.items()}
    fields['is_syncing']=0
    expected=dict(_id=pid,**fields)
    _exact_row(parents[0],expected,'POLARIS_PARENT_METADATA_DRIFT')

    chapters=_rows(con,SQL['selectPolarisParentChaptersFull'],{'parentId':pid})
    if len(chapters)!=len(b.chapters):
        raise ValueError('POLARIS_CHAPTER_COUNT_DRIFT')
    ids:dict[str,int]={}
    for ch in chapters:
        ids[ch['url']]=ch['_id']
    for original in b.chapters:
        target=next((ch for ch in chapters if ch['url']==original['chapterUrl']),None)
        if not target:
            raise ValueError('POLARIS_CHAPTER_URL_DRIFT')
        expected=dict(_id=target['_id'],manga_id=pid)
        expected.update({v:(_memo_bytes(original[k]) if k=='chapterMemo' else original[k]) for k,v in CHAPTER_PHYSICAL.items()})
        _exact_row(target,expected,'POLARIS_CHAPTER_METADATA_DRIFT')
    history = _rows(con,SQL['selectPolarisParentHistoryFull'],{'parentId':pid})
    expected_history=[dict(chapter_id=ids[h['chapterUrl']],chapter_url=h['chapterUrl'],last_read=h['lastRead'],time_read=h['readDuration']) for h in b.history]
    if sorted(history,key=lambda r:r['chapter_id'])!=sorted(expected_history,key=lambda r:r['chapter_id']):
        raise ValueError('POLARIS_HISTORY_METADATA_DRIFT')
    tracks=_rows(con,SQL['selectPolarisParentTrackingFull'],{'parentId':pid})
    if len(tracks) != len(b.tracking):
        raise ValueError('POLARIS_TRACKING_COUNT_DRIFT')
    orig_tracks = {x['syncId']: x for x in b.tracking}
    if len(orig_tracks) != len(b.tracking):
        raise ValueError('POLARIS_TRACKING_DUPLICATE')
    for actual in tracks:
        original = orig_tracks.get(actual['sync_id'])
        if original is None:
            raise ValueError('POLARIS_TRACKING_ID_DRIFT')
        expected = dict(_id=actual['_id'], manga_id=pid,
                        **{v:original[k] for k,v in TRACK_PHYSICAL.items()})
        _exact_row(actual, expected, 'POLARIS_TRACKING_METADATA_DRIFT')
    cats=_rows(con,SQL['selectPolarisParentCategoriesFull'],{'parentId':pid})
    if cats!=[{'category_id':c} for c in sorted(b.categories)]:
        raise ValueError('POLARIS_CATEGORY_DRIFT')
    exclusions=_rows(con,SQL['selectPolarisParentExclusionsFull'],{'parentId':pid})
    if exclusions!=[{'scanlator':x} for x in sorted(b.exclusions)]:
        raise ValueError('POLARIS_EXCLUSION_DRIFT')
    edges=_rows(con,SQL['selectPolarisParentEdgesFull'],{'parentId':pid})
    expected_edges=[dict(info_manga=int(e.info),get_chapter_updates=int(e.updates),chapter_sort_mode=e.sort,
       chapter_priority=e.priority,download_chapters=int(e.download),merge_id=pid,merge_url=b.parent['destinationUrl'],
       manga_id=pid if e.source==MERGED_SOURCE else e.manga_id,manga_url=e.url,manga_source=e.source)
       for e in sorted(b.edges,key=lambda x:x.priority)]
    if [{k:v for k,v in row.items()} for row in edges]!=expected_edges:
        raise ValueError('POLARIS_MERGED_EDGES_DRIFT')
    ledger=_rows(con,'SELECT archive_uuid,parent_manga_id,archive_digest FROM polaris_restore_ledger WHERE parent_manga_id=?',(pid,))
    if ledger!=[dict(archive_uuid=b.uuid,parent_manga_id=pid,archive_digest=b.digest)]:
        raise ValueError('POLARIS_LEDGER_DRIFT')


def restore_fresh_parents(con:sqlite3.Connection, batches:Sequence[Batch], fault:Optional[Callable[[str,int,sqlite3.Connection],None]]=None)->list[int]:
    """Host reference. ONCE, atomic. No reuse or auto-fix of existing parents."""
    if not batches: raise ValueError('POLARIS_EMPTY_BATCH')
    if con.in_transaction: raise ValueError('POLARIS_OUTER_TRANSACTION_UNSUPPORTED')
    if con.execute('PRAGMA foreign_keys').fetchone()!=(1,): raise ValueError('POLARIS_FOREIGN_KEYS_OFF')
    if len({b.uuid for b in batches})!=len(batches): raise ValueError('POLARIS_DUPLICATE_ARCHIVE_UUID')
    for b in batches: _assert_batch_shape(b)
    try:
        con.execute('BEGIN IMMEDIATE')
        con.execute('PRAGMA defer_foreign_keys=ON')
        if con.execute('PRAGMA defer_foreign_keys').fetchone()!=(1,): raise ValueError('POLARIS_DEFERRED_FK_UNAVAILABLE')
        result=[]
        for b in batches:
            pid=con.execute('SELECT COALESCE(MAX(_id),0)+1 FROM mangas').fetchone()[0]
            if pid <= 0 or pid>=9223372036854775807: raise ValueError('POLARIS_ID_RESERVATION_FAILED')
            _write_one(con,b,pid,fault)
            result.append(pid)
        if con.execute('PRAGMA foreign_keys').fetchone()!=(1,) or con.execute('PRAGMA defer_foreign_keys').fetchone()!=(1,):
            raise ValueError('POLARIS_TRANSACTION_CONTEXT_LOST')
        if con.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('POLARIS_FK_INTEGRITY_FAILURE')
        con.commit()
        return result
    except BaseException:
        if con.in_transaction: con.rollback()
        raise
