#!/usr/bin/env python3
"""Reproduce KNOWN R001 gaps; success means the problems were observed.

Diagnostic-only. Never count this as a correctness pass for Android.
"""
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
MIGRATION = ROOT.parent / 'new-files/data/src/main/sqldelight/tachiyomi/migrations/14.sqm'
PINNED_VIEW = ROOT / 'libraryView.pinned.sq'


def audit():
    con = sqlite3.connect(':memory:')
    con.execute('PRAGMA foreign_keys=ON')
    con.executescript("""
        CREATE TABLE mangas (_id INTEGER PRIMARY KEY, source INTEGER NOT NULL,
                            favorite INTEGER NOT NULL, title TEXT NOT NULL);
        CREATE TABLE chapters (_id INTEGER PRIMARY KEY, manga_id INTEGER NOT NULL,
                               read INTEGER NOT NULL, date_upload INTEGER NOT NULL,
                               date_fetch INTEGER NOT NULL, bookmark INTEGER NOT NULL,
                               scanlator TEXT);
        CREATE TABLE excluded_scanlators (manga_id INTEGER, scanlator TEXT);
        CREATE TABLE history (chapter_id INTEGER, last_read INTEGER);
        CREATE TABLE mangas_categories (manga_id INTEGER, category_id INTEGER);
    """)
    con.executescript(MIGRATION.read_text())
    con.executescript(PINNED_VIEW.read_text().split('\nlibrary:\n', 1)[0])
    con.executemany('INSERT INTO mangas VALUES (?,?,?,?)', [
        (10, 111, 0, 'Work A'), (20, 222, 0, 'Work B'), (900, 6969, 1, 'Virtual work'),
    ])
    con.executemany('INSERT INTO chapters VALUES (?,?,?,?,?,?,?)', [
        (1, 10, 1, 1, 1, 0, 'ScanA'), (2, 10, 0, 2, 2, 0, 'ScanA'),
        (3, 20, 0, 3, 3, 1, 'ScanB'), (4, 20, 0, 4, 4, 0, 'ScanB'),
    ])
    def ref(source, manga, url):
        con.execute("""INSERT INTO merged
            (info_manga, get_chapter_updates, chapter_sort_mode, chapter_priority,
             download_chapters, merge_id, merge_url, manga_id, manga_url, manga_source)
            VALUES (0, 1, 2, 0, 0, 900, 'merged://10-20', ?, ?, ?)""", (manga, url, source))
    ref(111, 10, 'A')
    ref(222, 20, 'B')
    ref(6969, 900, 'merged://10-20')
    badges = con.execute('SELECT totalCount, readCount, bookmarkCount FROM libraryView WHERE _id=900').fetchone()
    linked = con.execute("""SELECT count(*), sum(ch.read), sum(ch.bookmark)
        FROM merged m JOIN chapters ch ON ch.manga_id=m.manga_id
        WHERE m.merge_id=900 AND m.manga_source !=6969""").fetchone()
    ref(111, 10, 'A')
    duplicates = con.execute("""SELECT count(*) FROM merged
        WHERE merge_id=900 AND manga_id=10 AND manga_source=111""").fetchone()[0]
    con.close()
    result = {
        'scope': 'KNOWN_GAPS_NOT_ANDROID_ACCEPTANCE',
        'library_badges': list(badges),
        'linked_real_chapter_stats': list(linked),
        'duplicate_ref_rows_for_same_child': duplicates,
        'badges_incorrect': badges == (0, 0, 0) and linked == (4, 1, 1),
        'duplicate_ref_allowed': duplicates == 2,
    }
    print(json.dumps(result, indent=2))
    if not (result['badges_incorrect'] and result['duplicate_ref_allowed']):
        raise SystemExit('Known gap reproduction has changed: re-audit before relying on findings')
    return result


if __name__ == '__main__':
    audit()
