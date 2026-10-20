"""Pinned Yomotsu SQLDelight schema, adapted only for bare sqlite3 execution.

Commit: 0fb80c439ef816eeb50674f1b90af39918b176d8
Original SQLDelight CREATE TABLE statements in data/src/main/sqldelight/tachiyomi/data.
The Kotlin type adapter aliases (AS Boolean/List/JsonObject/Date) are stripped;
this IS NOT a byte-for-byte checkout, SQLDelight code generation, or Android.
No merged table occurs anywhere in the upstream pinned git tree.
"""
from __future__ import annotations
import sqlite3

ORIGIN="0fb80c439ef816eeb50674f1b90af39918b176d8"
SOURCE_BLOBS={
 'mangas.sq':'b5d1909f759683136978e0bf2df182287ca4065d',
 'chapters.sq':'b6280be75e8fab1b4f7087df6bdeb238eb07d58c',
 'history.sq':'6cecd5784df875f402bde42783e7a59178ff8690',
 'categories.sq':'a94f38f934f89da4ab400a96cb1fb081c1301095',
 'mangas_categories.sq':'7500d797ab9bfaac6a0e29c7083ffd8bbf5137e7',
 'manga_sync.sq':'f76b6bb7eb0e7d485974335d3ce6f1d4b68b2d7e',
 'excluded_scanlators.sq':'37ed6489ec4b18e3fabdd5778e627d0fff73606c',
}
# Whole CREATE TABLE column sets and constraints mirrored from the pinned blob
# sources. SQLDelight source imports / annotations are not SQLite grammar.
SCHEMA='''
CREATE TABLE mangas (
 _id INTEGER NOT NULL PRIMARY KEY, source INTEGER NOT NULL, url TEXT NOT NULL,
 artist TEXT, author TEXT, description TEXT, genre TEXT,
 title TEXT NOT NULL, status INTEGER NOT NULL, thumbnail_url TEXT,
 favorite INTEGER NOT NULL, last_update INTEGER, next_update INTEGER,
 initialized INTEGER NOT NULL, viewer INTEGER NOT NULL, chapter_flags INTEGER NOT NULL,
 cover_last_modified INTEGER NOT NULL, date_added INTEGER NOT NULL,
 update_strategy INTEGER NOT NULL DEFAULT 0,
 calculate_interval INTEGER DEFAULT 0 NOT NULL,
 last_modified_at INTEGER NOT NULL DEFAULT 0,
 favorite_modified_at INTEGER, version INTEGER NOT NULL DEFAULT 0,
 is_syncing INTEGER NOT NULL DEFAULT 0,
 notes TEXT NOT NULL DEFAULT '', memo BLOB NOT NULL DEFAULT '{}'
);
CREATE INDEX mangas_url_index ON mangas(url);
CREATE INDEX idx_mangas_source ON mangas(source);
CREATE TABLE chapters (
 _id INTEGER NOT NULL PRIMARY KEY, manga_id INTEGER NOT NULL,
 url TEXT NOT NULL, name TEXT NOT NULL, scanlator TEXT,
 read INTEGER NOT NULL, bookmark INTEGER NOT NULL,
 last_page_read INTEGER NOT NULL, chapter_number REAL NOT NULL,
 source_order INTEGER NOT NULL, date_fetch INTEGER NOT NULL,
 date_upload INTEGER NOT NULL, last_modified_at INTEGER NOT NULL DEFAULT 0,
 version INTEGER NOT NULL DEFAULT 0, is_syncing INTEGER NOT NULL DEFAULT 0,
 memo BLOB NOT NULL DEFAULT '{}',
 FOREIGN KEY(manga_id) REFERENCES mangas (_id) ON DELETE CASCADE
);
CREATE INDEX chapters_manga_id_index ON chapters(manga_id);
CREATE INDEX idx_chapters_url ON chapters(url);
CREATE TABLE history (
 _id INTEGER NOT NULL PRIMARY KEY, chapter_id INTEGER NOT NULL UNIQUE,
 last_read INTEGER, time_read INTEGER NOT NULL,
 FOREIGN KEY(chapter_id) REFERENCES chapters (_id) ON DELETE CASCADE
);
CREATE INDEX history_history_chapter_id_index ON history(chapter_id);
CREATE TABLE categories (
 _id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL,
 sort INTEGER NOT NULL, flags INTEGER NOT NULL
);
INSERT OR IGNORE INTO categories(_id,name,sort,flags) VALUES (0,'',-1,0);
CREATE TABLE mangas_categories (
 _id INTEGER NOT NULL PRIMARY KEY, manga_id INTEGER NOT NULL,
 category_id INTEGER NOT NULL,
 FOREIGN KEY(category_id) REFERENCES categories (_id) ON DELETE CASCADE,
 FOREIGN KEY(manga_id) REFERENCES mangas (_id) ON DELETE CASCADE
);
CREATE INDEX idx_mangas_categories_manga_id ON mangas_categories(manga_id);
CREATE TABLE manga_sync (
 _id INTEGER NOT NULL PRIMARY KEY, manga_id INTEGER NOT NULL,
 sync_id INTEGER NOT NULL, remote_id INTEGER NOT NULL,
 library_id INTEGER, title TEXT NOT NULL,
 last_chapter_read REAL NOT NULL, total_chapters INTEGER NOT NULL,
 status INTEGER NOT NULL, score REAL NOT NULL, remote_url TEXT NOT NULL,
 start_date INTEGER NOT NULL, finish_date INTEGER NOT NULL,
 private INTEGER DEFAULT 0 NOT NULL,
 UNIQUE (manga_id,sync_id) ON CONFLICT REPLACE,
 FOREIGN KEY(manga_id) REFERENCES mangas (_id) ON DELETE CASCADE
);
CREATE TABLE excluded_scanlators (
 manga_id INTEGER NOT NULL, scanlator TEXT NOT NULL,
 FOREIGN KEY(manga_id) REFERENCES mangas (_id) ON DELETE CASCADE
);
CREATE INDEX excluded_scanlators_manga_id_index ON excluded_scanlators(manga_id);
'''

def connect():
    conn=sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def columns(conn, table):
    return {row[1] for row in conn.execute(f'PRAGMA table_info({table})')}


def tables(conn):
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
