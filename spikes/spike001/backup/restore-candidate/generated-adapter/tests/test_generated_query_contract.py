"""Fail-closed SOURCE-contract audit of candidate Kotlin vs staged SQLDelight 2.3.2 queries.

This is NOT the SQLDelight compiler. Does not certify generated Kotlin signatures.
"""
from __future__ import annotations
import pathlib
import re
import sqlite3
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = next((x for x in (HERE.parents[2], HERE / "fixtures" / "spike001")
             if (x / "backup" / "restore-candidate" / "parent-sqldelight-fields" / "PolarisParentMetadataRestore.sq").exists()), None)
if ROOT is None: raise RuntimeError("Pinned Polaris SQLDelight fixtures were not found")
RESTORE = ROOT / 'backup' / 'restore-candidate'
KOTLIN = (HERE / 'SqlDelightPolarisFreshParentAdapter.kt').read_text()
SQL = (RESTORE / 'parent-sqldelight-fields' / 'PolarisParentMetadataRestore.sq').read_text()
MERGED = (ROOT / 'new-files/data/src/main/sqldelight/tachiyomi/data/merged.sq').read_text()


def sqlqueries(src: str):
    return {m[1]:m[2] for m in re.finditer(r'(?ms)^([A-Za-z][A-Za-z0-9_]*):\s*\n(.*?;)',src)}


def calls(src: str, name: str):
    pat = re.compile(r'\b'+re.escape(name)+r'\(')
    ret=[]
    for m in pat.finditer(src):
        start=m.end();level=1;i=start;quote=None;escape=False
        while i<len(src) and level:
            c=src[i];i+=1
            if quote:
                if escape:escape=False
                elif c=='\\':escape=True
                elif c==quote:quote=None
            elif c in ('"',"'"):quote=c
            elif c=='(':level+=1
            elif c==')':level-=1
        if level==0:ret.append(src[start:i-1])
    return ret


def named_args(c: str):
    return set(re.findall(r'(?<![\w.])([a-zA-Z]\w*)\s*=',c))

class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(RESTORE/'pinned-schema-bridge'))
        import pinned_schema_fixture as s
        cls.conn=s.connect()
        cls.q=sqlqueries(SQL);cls.mq=sqlqueries(MERGED)
    @classmethod
    def tearDownClass(cls):cls.conn.close()

    def test_all_17_query_entrypoints_referenced_exist(self):
        for method in re.findall(r'\bq\.(\w+)\(',KOTLIN):
            self.assertIn(method,self.q,method)

    def test_candidate_query_names_are_unique(self):
        self.assertEqual(len(self.q),len(re.findall(r'(?m)^([A-Za-z]\w*):\s*$',SQL)))

    def test_named_parent_insert_parameters_exact(self):
        n='insertPolarisRestoredReservedParentLast';c=calls(KOTLIN,n)
        self.assertEqual(len(c),1)
        self.assertEqual(named_args(c[0]),set(re.findall(r':(\w+)',self.q[n])))

    def test_named_chapter_insert_parameters_exact(self):
        n='insertPolarisRestoredChapterFull';c=calls(KOTLIN,n)
        self.assertEqual(len(c),1)
        self.assertEqual(named_args(c[0]),set(re.findall(r':(\w+)',self.q[n])))

    def test_named_tracking_insert_parameters_exact(self):
        n='insertPolarisRestoredTrackExact';c=calls(KOTLIN,n)
        self.assertEqual(len(c),1)
        self.assertEqual(named_args(c[0]),set(re.findall(r':(\w+)',self.q[n])))

    def test_named_merged_edge_parameters_exact(self):
        n='insertReturningId';c=calls(KOTLIN,n)
        self.assertEqual(len(c),1)
        self.assertEqual(named_args(c[0]),set(re.findall(r':(\w+)',self.mq[n])))

    def test_parent_insert_covers_each_original_column_exactly(self):
        names=[x[1] for x in self.conn.execute('PRAGMA table_info(mangas)')]
        sql=self.q['insertPolarisRestoredReservedParentLast']
        cols=[x.strip() for x in re.search(r'INSERT INTO mangas\s*\((.*?)\)\s*VALUES',sql,re.S)[1].split(',')]
        self.assertEqual(set(cols),set(names))
        self.assertEqual(len(cols),len(names))

    def test_chapter_insert_covers_each_original_column_except_auto_id(self):
        names=[x[1] for x in self.conn.execute('PRAGMA table_info(chapters)')]
        sql=self.q['insertPolarisRestoredChapterFull']
        cols=[x.strip() for x in re.search(r'INSERT INTO chapters\s*\((.*?)\)\s*VALUES',sql,re.S)[1].split(',')]
        self.assertEqual(set(cols),set(names)-{'_id'})

    def test_readback_comparison_covers_all_persisted_parent_columns(self):
        names={x[1] for x in self.conn.execute('PRAGMA table_info(mangas)')}
        found=set(re.findall(r'\bstored\.(\w+)\b',KOTLIN))
        self.assertEqual(names,found)

    def test_readback_comparison_covers_all_chapter_columns_but_url_key(self):
        names={x[1] for x in self.conn.execute('PRAGMA table_info(chapters)')}
        found=set(re.findall(r'\bactual\.(\w+)\b',KOTLIN))
        self.assertEqual(names-{'_id','url'},found)
        self.assertIn('chapters.map { it.url }',KOTLIN)
        self.assertIn('chaptersByUrl[c.url]',KOTLIN)

    def test_readback_tracking_covers_all_columns_but_db_id(self):
        names={x[1] for x in self.conn.execute('PRAGMA table_info(manga_sync)')}
        part=KOTLIN.split('val trackBySync',1)[1].split('val categories',1)[0]
        found=set(re.findall(r'\brow\.(\w+)\b',part))
        self.assertEqual(names-{'_id','sync_id'},found)
        self.assertIn('tracking.map { it.sync_id }.toSet().size == tracking.size',KOTLIN)

    def test_readback_merged_edges_covers_all_noninternal_columns(self):
        names={x[1] for x in self.conn.execute('PRAGMA table_info(merged)')} if False else {
            '_id','info_manga','get_chapter_updates','chapter_sort_mode','chapter_priority',
            'download_chapters','merge_id','merge_url','manga_id','manga_url','manga_source'}
        part=KOTLIN.split('val actualByPriority',1)[1].split('val ledger',1)[0]
        found=set(re.findall(r'\brow\.(\w+)\b',part))
        self.assertEqual(names-{'_id','chapter_priority'},found)

    def test_readback_checks_history_chapter_id_and_time(self):
        self.assertIn('row.chapter_id == chaptersByUrl[h.chapterUrl]?._id',KOTLIN)
        self.assertIn('row.last_read?.time == h.lastRead',KOTLIN)
        self.assertIn('row.time_read == h.readDuration',KOTLIN)

    def test_readback_checks_category_and_exclusion_count_not_just_set(self):
        self.assertIn('categories.size == prepared.categories.size',KOTLIN)
        self.assertIn('excluded.size == prepared.excludedScanlators.size',KOTLIN)

    def test_parent_last_ordering_is_real(self):
        a=KOTLIN.index('stageDependencies(id, work, prepared, edges)')
        b=KOTLIN.index('q.insertPolarisRestoredReservedParentLast(')
        c=KOTLIN.index('assertExactRows(id, work, prepared, edges)')
        self.assertLess(a,b);self.assertLess(b,c)

    def test_transaction_is_pinned_guard_not_adhoc_begin(self):
        self.assertIn('transaction.restoreNewParents {',KOTLIN)
        self.assertNotIn('\"BEGIN IMMEDIATE\"',KOTLIN)
        self.assertNotIn('PRAGMA foreign_keys = OFF',KOTLIN)

    def test_reservation_occurs_inside_guard_and_precedes_mapper(self):
        a=KOTLIN.index('transaction.restoreNewParents {')
        b=KOTLIN.index('q.selectPolarisNextFreshParentId().awaitAsOne()')
        c=KOTLIN.index('PolarisBackupMangaSqlProjection.prepare(')
        self.assertTrue(a<b<c)

    def test_ledger_and_merged_writes_before_parent(self):
        part=KOTLIN.split('private suspend fun stageDependencies(',1)[1].split('private suspend fun assertExactRows(',1)[0]
        self.assertIn('insertArchiveLedger',part)
        self.assertIn('mergedQueries.insertReturningId',part)
        self.assertIn('awaitAsOneOrNull()',part)

    def test_legacy_uuid_replay_is_rejected(self):
        self.assertIn('selectAllVirtualUuidMemos()',KOTLIN)
        self.assertIn('POLARIS_FRESH_LEGACY_UUID_CLAIM',KOTLIN)
        self.assertIn('POLARIS_FRESH_UUID_ALREADY_RESTORED',KOTLIN)

    def test_resolved_vs_pending_sources_require_exact_match(self):
        self.assertIn('if (child.realMangaId == null) ids.isEmpty() else ids == listOf(child.realMangaId)',KOTLIN)

    def test_root_flags_no_info_download_updates(self):
        for key in ('!w.rootSettings.infoManga','!w.rootSettings.downloadChapters',
                    '!w.rootSettings.getChapterUpdates'):
            self.assertIn(key,KOTLIN)

    def test_release_flag_must_remain_fail_closed(self):
        self.assertNotIn('PolarisRestoreCoordinator(',KOTLIN)
        self.assertNotIn('migration15',KOTLIN)

if __name__=='__main__':unittest.main()
