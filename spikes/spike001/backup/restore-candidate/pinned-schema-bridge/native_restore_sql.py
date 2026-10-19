"""Experimental v2 parent atomic write using *native-shaped* Yomotsu tables.

All tables other than source-absent `merged` and `polaris_restore_ledger` mirror
pinned source column names. This uses sqlite3 + explicit bindings, not SQLDelight.
NO production use; parent metadata readback is not yet comprehensive enough to
unblock v2. Strictly rejects replay rather than overwriting unknown local data.
"""
from __future__ import annotations
import base64
import hashlib
import json
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'full-parent-sqlite'))
from atomic_full_parent_v2_host import validate_works, jdump, memo_object, UUID_MEMO, VIRTUAL
from pinned_schema_fixture import connect,columns

BRIDGE_SQL=(Path(__file__).with_name('merged_bridge_candidate.sql')).read_text()

def open_db():
    c=connect()
    c.executescript(BRIDGE_SQL)
    c.commit()
    return c

def memo_bytes(x):
    return jdump(x).encode('utf8')

def snapshot_memo(s,uid):
    m=dict(memo_object(s['memo_b64']))
    m[UUID_MEMO]=uid
    return memo_bytes(m)

def chapter_memo(c):
    return base64.b64decode(c['memo_b64'],validate=True)

def write_parent(c,s,uid):
    # Explicit columns: no payload_json fixture allowed in native DB.
    values={
       'source':VIRTUAL,'url':'merged://polaris/'+uid,
       'artist':s['artist'],'author':s['author'],'description':s['description'],
       'genre':', '.join(s['genre']),'title':s['title'],'status':s['status'],
       'thumbnail_url':s['thumbnailUrl'],'favorite':int(s['favorite']),
       'last_update':0,'next_update':0,'initialized':int(s['initialized']),
       'viewer':s['viewer_flags'] if s['viewer_flags'] is not None else s['viewer'],
       'chapter_flags':s['chapterFlags'],'cover_last_modified':0,
       'date_added':s['dateAdded'],'update_strategy':s['updateStrategy'],
       'calculate_interval':0,'last_modified_at':s['lastModifiedAt'],
       'favorite_modified_at':s['favoriteModifiedAt'],'version':s['version'],
       'is_syncing':1,'notes':s['notes'],'memo':snapshot_memo(s,uid),
    }
    names=','.join(values)
    ids=','.join('?' for _ in values)
    return c.execute('INSERT INTO mangas('+names+') VALUES ('+ids+')',tuple(values.values())).lastrowid

def exact_parent(c,uid,pid,s,catids,edges):
    values=c.execute('SELECT source,url,title,artist,author,description,genre,status,thumbnail_url, favorite, initialized, viewer,chapter_flags,date_added,update_strategy,last_modified_at, favorite_modified_at,version,notes,memo,last_update,next_update,cover_last_modified,calculate_interval,is_syncing FROM mangas WHERE _id=?',(pid,)).fetchone()
    want=(VIRTUAL,'merged://polaris/'+uid,s['title'],s['artist'],s['author'],s['description'],', '.join(s['genre']),s['status'],s['thumbnailUrl'],int(s['favorite']),int(s['initialized']),s['viewer_flags'] if s['viewer_flags'] is not None else s['viewer'],s['chapterFlags'],s['dateAdded'],s['updateStrategy'],s['lastModifiedAt'],s['favoriteModifiedAt'],s['version'],s['notes'],snapshot_memo(s,uid),0,0,0,0,1)
    if values!=want:return False
    if sorted(x[0] for x in c.execute('SELECT category_id FROM mangas_categories WHERE manga_id=?',(pid,)))!=sorted(catids):return False
    chapters=c.execute('SELECT _id,url,name,scanlator,read,bookmark,last_page_read,chapter_number,source_order,date_fetch,date_upload,version,memo,last_modified_at,is_syncing FROM chapters WHERE manga_id=?',(pid,)).fetchall()
    if len(chapters)!=len(s['chapters']):return False
    seen={}
    for row in chapters:
        ch=next((x for x in s['chapters'] if x['url']==row[1]),None)
        if ch is None or row[1] in seen:return False
        if row[2:]!=(ch['name'],ch['scanlator'],int(ch['read']),int(ch['bookmark']),ch['lastPageRead'],ch['chapterNumber'],ch['sourceOrder'],ch['dateFetch'],ch['dateUpload'],ch['version'],chapter_memo(ch),ch['lastModifiedAt'],1):return False
        seen[row[1]]=row[0]
    history=list(c.execute('SELECT h.chapter_id,h.last_read,h.time_read FROM history h JOIN chapters c ON c._id=h.chapter_id WHERE c.manga_id=?',(pid,)))
    if sorted(history)!=sorted((seen[h['url']],h['lastRead'],h['readDuration']) for h in s['history']):return False
    tracks=list(c.execute('SELECT sync_id,remote_id,library_id,title,last_chapter_read,total_chapters,status,score,remote_url,start_date,finish_date,private FROM manga_sync WHERE manga_id=?',(pid,)))
    expected=[]
    for t in s['tracking']:
        remote=t['mediaIdInt'] or t['mediaId']
        expected.append((t['syncId'],remote,t['libraryId'],t['title'],t['lastChapterRead'],t['totalChapters'],t['status'],t['score'],t['trackingUrl'],t['startedReadingDate'],t['finishedReadingDate'],int(t['private'])))
    if sorted(tracks)!=sorted(expected):return False
    if sorted(x[0] for x in c.execute('SELECT scanlator FROM excluded_scanlators WHERE manga_id=?',(pid,)))!=sorted(s['excludedScanlators']):return False
    rows=list(c.execute('SELECT manga_source,manga_url,manga_id,info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters FROM merged WHERE merge_id=?',(pid,)))
    wantedges=[]
    for e in edges:
        f=e['settings']
        wantedges.append((e['source'],e['url'],e['real_id'],int(f['infoManga']),int(f['getChapterUpdates']),f['chapterSortMode'],f['chapterPriority'],int(f['downloadChapters'])))
    return sorted(rows,key=str)==sorted(wantedges,key=str)

def restore(c,works,archive_categories,fail_after_parent=None):
    validate_works(works,archive_categories)
    if c.in_transaction:raise RuntimeError('Explicit exclusive transaction required')
    # Prevalidate any lossy SQLite adapter conversions and bad types.
    for w in works:
        for genre in w['snapshot']['genre']:
            if not isinstance(genre,str) or ', ' in genre:raise ValueError('Genre cannot be represented losslessly in pinned column adapter')
    c.execute('BEGIN IMMEDIATE')
    result=[]
    try:
        for n,w in enumerate(works):
            s=w['snapshot'];uid=w['uuid'];edges=w['edges']
            catids=[]
            for order in s['categories']:
                ids=c.execute('SELECT _id FROM categories WHERE name=?',(archive_categories[order],)).fetchall()
                if len(ids)!=1 or ids[0][0]<=0:raise ValueError('Destination category ambiguous/missing')
                catids.append(ids[0][0])
            if len(set(catids))!=len(catids):raise ValueError('Categories collapse')
            for e in edges:
                if e['real_id'] is not None:
                    ids=c.execute('SELECT _id FROM mangas WHERE source=? AND url=?',(e['source'],e['url'])).fetchall()
                    if ids != [(e['real_id'],)]:raise ValueError('Real child not unique or drifted')
            fingerprint=hashlib.sha256(jdump({'s':s,'categories':archive_categories,'edges':edges}).encode()).hexdigest()
            ledger=c.execute('SELECT parent_manga_id,archive_digest FROM polaris_restore_ledger WHERE archive_uuid=?',(uid,)).fetchone()
            if ledger:
                pid,digest=ledger
                if digest!=fingerprint or not exact_parent(c,uid,pid,s,catids,edges):
                    raise ValueError('Archive differs from local restored parent')
                result.append(pid);continue
            if c.execute('SELECT 1 FROM mangas WHERE source=? AND url=?',(VIRTUAL,'merged://polaris/'+uid)).fetchone():
                raise ValueError('Untracked stable URL')
            # Legacy source-6969 UUID memos must be audited even if URL differs.
            for blob, in c.execute('SELECT memo FROM mangas WHERE source=?',(VIRTUAL,)):
                try: j=json.loads(blob)
                except (TypeError,ValueError,UnicodeError):raise ValueError('Corrupt legacy memo')
                if not isinstance(j,dict) or j.get(UUID_MEMO)==uid:
                    raise ValueError('Legacy UUID collision or corrupt memo')
            pid=write_parent(c,s,uid)
            c.execute('INSERT INTO polaris_restore_ledger VALUES (?,?,?)',(uid,pid,fingerprint))
            for cid in catids:c.execute('INSERT INTO mangas_categories(manga_id,category_id) VALUES(?,?)',(pid,cid))
            by_url={}
            for ch in s['chapters']:
                by_url[ch['url']]=c.execute('''INSERT INTO chapters
                  (manga_id,url,name,scanlator,read,bookmark,last_page_read,chapter_number,source_order,date_fetch,date_upload,last_modified_at,version,is_syncing,memo)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                    pid,ch['url'],ch['name'],ch['scanlator'],int(ch['read']),int(ch['bookmark']),ch['lastPageRead'],ch['chapterNumber'],ch['sourceOrder'],ch['dateFetch'],ch['dateUpload'],ch['lastModifiedAt'],ch['version'],1,chapter_memo(ch))).lastrowid
            for h in s['history']:
                c.execute('INSERT INTO history(chapter_id,last_read,time_read) VALUES (?,?,?)',(by_url[h['url']],h['lastRead'],h['readDuration']))
            for t in s['tracking']:
                c.execute('''INSERT INTO manga_sync(manga_id,sync_id,remote_id,library_id,title,last_chapter_read,total_chapters,status,score,remote_url,start_date,finish_date,private)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                  pid,t['syncId'],t['mediaIdInt'] or t['mediaId'],t['libraryId'],t['title'],t['lastChapterRead'],t['totalChapters'],t['status'],t['score'],t['trackingUrl'],t['startedReadingDate'],t['finishedReadingDate'],int(t['private'])))
            for excluded in s['excludedScanlators']:
                c.execute('INSERT INTO excluded_scanlators(manga_id,scanlator) VALUES (?,?)',(pid,excluded))
            for e in edges:
                f=e['settings']
                c.execute('''INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source)
                  VALUES(?,?,?,?,?,?,?,?,?,?)''',(
                    int(f['infoManga']),int(f['getChapterUpdates']),f['chapterSortMode'],f['chapterPriority'],int(f['downloadChapters']),pid,'merged://polaris/'+uid,e['real_id'],e['url'],e['source']))
            if not exact_parent(c,uid,pid,s,catids,edges):raise ValueError('Post-write readback differs')
            if fail_after_parent==n:raise RuntimeError('Injected failure after parent')
            result.append(pid)
        c.commit()
        return result
    except BaseException:
        c.rollback()
        raise
