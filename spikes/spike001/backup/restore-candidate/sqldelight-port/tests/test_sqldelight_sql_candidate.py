"""Check proposed SQLDelight statements against real SQLite. NOT Kotlin code generation."""
from pathlib import Path
import re
import sqlite3
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'sql-candidate/polarisRestore.sq').read_text()
pieces=re.split(r'(?m)^([a-zA-Z]\w*):\s*\n',SOURCE)
DDL=pieces[0]
Q={pieces[i].strip():pieces[i+1].strip() for i in range(1,len(pieces),2)}
BASE="""
CREATE TABLE mangas(_id INTEGER NOT NULL PRIMARY KEY,source INTEGER NOT NULL,url TEXT NOT NULL,
 title TEXT NOT NULL,status INTEGER NOT NULL,favorite INTEGER NOT NULL,initialized INTEGER NOT NULL,
 viewer INTEGER NOT NULL,chapter_flags INTEGER NOT NULL,cover_last_modified INTEGER NOT NULL,
 date_added INTEGER NOT NULL,memo BLOB NOT NULL DEFAULT '{}');
CREATE TABLE merged(_id INTEGER NOT NULL PRIMARY KEY,info_manga INTEGER NOT NULL,
 get_chapter_updates INTEGER NOT NULL,chapter_sort_mode INTEGER NOT NULL,chapter_priority INTEGER NOT NULL,
 download_chapters INTEGER NOT NULL,merge_id INTEGER NOT NULL,merge_url TEXT NOT NULL,
 manga_id INTEGER,manga_url TEXT NOT NULL,manga_source INTEGER NOT NULL,
 FOREIGN KEY(manga_id) REFERENCES mangas(_id) ON DELETE SET NULL,
 FOREIGN KEY(merge_id) REFERENCES mangas(_id) ON DELETE CASCADE);
"""
def db(indexes=True):
    c=sqlite3.connect(':memory:');c.execute('PRAGMA foreign_keys=ON');c.executescript(BASE)
    if indexes:c.executescript(DDL)
    for id,source,url in [(101,11,'/a'),(202,12,'/b')]:
        c.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(id,source,url,'source',0,0,1,0,0,0,0))
    c.commit();return c
def parent(c):
    return c.execute(Q['insertNewRestoredParent'],dict(parentUrl='merged://polaris/u',parentTitle='Work',memo=b'{"polaris.merge.work.uuid":"u"}')).fetchone()[0]
def edge(c,p=203,source=11,url='/a',manga=101):
    args=dict(infoManga=0,getChapterUpdates=1,chapterSortMode=2,chapterPriority=7,
              downloadChapters=1,parentId=p,parentUrl='merged://polaris/u',mangaId=manga,
              mangaUrl=url,mangaSource=source)
    return c.execute(Q['insertRestoredEdge'],args)

class SqlDelightSqlCandidateTests(unittest.TestCase):
    def setUp(self):self.c=db();self.addCleanup(self.c.close)
    def test_nine_named_queries_exist(self):
        self.assertEqual(len(Q),9)
        self.assertIn('selectRestoredParentEdges',Q)
    def test_insert_parent_preserves_pin_schema_defaults(self):
        self.assertEqual(parent(self.c),203)
        self.assertEqual(self.c.execute('SELECT source,favorite,initialized FROM mangas WHERE _id=203').fetchone(),(6969,1,1))
    def test_ledger_roundtrip_via_named_selector(self):
        p=parent(self.c)
        self.c.execute(Q['insertArchiveLedger'],dict(archiveUuid='u',parentId=p,archiveDigest='fingerprint'))
        self.assertEqual(self.c.execute(Q['selectLedgerForUuid'],dict(archiveUuid='u')).fetchone(),(p,'fingerprint'))
    def test_exact_lookup_returns_all_ambiguous_source_rows(self):
        self.c.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(303,11,"/a","dup",0,0,1,0,0,0,0)')
        self.assertEqual(self.c.execute(Q['selectAllExactSourceChildIds'],dict(sourceId=11,sourceUrl='/a')).fetchall(),[(101,),(303,)])
    def test_pending_link_preserves_full_settings(self):
        parent(self.c);edge(self.c,source=12,url='/pending',manga=None)
        self.assertEqual(self.c.execute(Q['selectRestoredParentEdges'],dict(parentId=203)).fetchone(),
                        (0,1,2,7,1,None,'/pending',12,'merged://polaris/u'))
    def test_unique_real_manga_index_prevents_forged_second_identity(self):
        parent(self.c);edge(self.c)
        with self.assertRaises(sqlite3.IntegrityError):edge(self.c,source=42,url='/forged',manga=101)
    def test_source_identity_index_handles_resolved_and_pending_duplicates(self):
        parent(self.c);edge(self.c)
        with self.assertRaises(sqlite3.IntegrityError):edge(self.c,source=11,url='/a',manga=None)
    def test_foreign_key_deletes_ledger_and_edges_with_parent(self):
        parent(self.c)
        self.c.execute(Q['insertArchiveLedger'],dict(archiveUuid='u',parentId=203,archiveDigest='a'))
        edge(self.c,p=203,source=6969,url='merged://polaris/u',manga=203)
        self.c.execute('DELETE FROM mangas WHERE _id=203')
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone()[0],0)
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM merged').fetchone()[0],0)
    def test_preledger_virtual_parent_uuid_is_visible(self):
        self.c.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added,memo) VALUES(900,6969,"merged://legacy","old",0,1,1,0,0,0,0,?)',(b'{"polaris.merge.work.uuid":"legacy"}',))
        self.assertEqual([r[0] for r in self.c.execute(Q['selectAllVirtualUuidMemos'])],[900])
    def test_existing_duplicate_links_abort_index_creation(self):
        c=db(False);self.addCleanup(c.close)
        c.execute('INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(900,6969,"merged://old","old",0,1,1,0,0,0,0)')
        args=(0,0,2,1,0,900,'merged://old',101,'/a',11)
        c.executemany('INSERT INTO merged(info_manga,get_chapter_updates,chapter_sort_mode,chapter_priority,download_chapters,merge_id,merge_url,manga_id,manga_url,manga_source) VALUES(?,?,?,?,?,?,?,?,?,?)',[args,args])
        c.commit()
        with self.assertRaises(sqlite3.IntegrityError):c.executescript(DDL)

if __name__=='__main__':unittest.main()
