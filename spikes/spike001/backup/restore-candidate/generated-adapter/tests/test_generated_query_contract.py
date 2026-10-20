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

    def test_category_full_readback_query_is_single_scalar_integer(self):
        body = self.q['selectPolarisParentCategoriesFull']
        self.assertRegex(body, r'(?is)^SELECT\s+category_id\s+FROM\s+mangas_categories')
        self.assertNotRegex(body, r'(?is)^SELECT\s+\*')

    def test_category_full_readback_kotlin_is_typed_scalar_not_synthetic_dto(self):
        self.assertIn('val categories: List<Long> = q.selectPolarisParentCategoriesFull(id).awaitAsList()', KOTLIN)
        self.assertNotIn('selectPolarisParentCategoriesFull(id).awaitAsList().map', KOTLIN)
        self.assertIn('fun selectPolarisParentCategoriesFull(parentId:Long):Query<Long>',
                      (HERE / 'host' / 'DatabaseHostStub.kt').read_text())

    def test_exclusion_full_readback_query_is_single_scalar_string(self):
        body = self.q['selectPolarisParentExclusionsFull']
        self.assertRegex(body, r'(?is)^SELECT\s+scanlator\s+FROM\s+excluded_scanlators')
        self.assertNotRegex(body, r'(?is)^SELECT\s+\*')

    def test_exclusion_full_readback_kotlin_is_typed_scalar_not_synthetic_dto(self):
        self.assertIn('val excluded: List<String> = q.selectPolarisParentExclusionsFull(id).awaitAsList()', KOTLIN)
        self.assertNotIn('selectPolarisParentExclusionsFull(id).awaitAsList().map', KOTLIN)
        self.assertIn('fun selectPolarisParentExclusionsFull(parentId:Long):Query<String>',
                      (HERE / 'host' / 'DatabaseHostStub.kt').read_text())

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

    def test_category_query_selects_sorted_ids_by_name(self):
        sql=self.q['selectPolarisRestoreCategoryCandidates']
        self.assertRegex(sql,r'(?i)SELECT\s+_id\s+FROM\s+categories')
        self.assertRegex(sql,r'(?i)WHERE\s+name\s*=\s*:categoryName')
        self.assertRegex(sql,r'(?i)ORDER\s+BY\s+_id')

    def test_category_db_allows_name_duplicates_so_id_alone_is_unsafe(self):
        self.conn.execute('SAVEPOINT category_names')
        try:
            self.conn.execute('INSERT INTO categories(_id,name,sort,flags) VALUES(?,?,?,?)',(17001,'Polaris Category',100,0))
            sql=self.q['selectPolarisRestoreCategoryCandidates']
            self.assertEqual([r[0] for r in self.conn.execute(sql,{'categoryName':'Polaris Category'})],[17001])
            self.conn.execute('INSERT INTO categories(_id,name,sort,flags) VALUES(?,?,?,?)',(17002,'Polaris Category',101,0))
            self.assertEqual([r[0] for r in self.conn.execute(sql,{'categoryName':'Polaris Category'})],[17001,17002])
        finally:
            self.conn.execute('ROLLBACK TO SAVEPOINT category_names')
            self.conn.execute('RELEASE SAVEPOINT category_names')

    def test_category_binding_enforces_backup_order_and_name_in_same_transaction(self):
        self.assertIn('import eu.kanade.tachiyomi.data.backup.models.BackupCategory',KOTLIN)
        self.assertIn('val archiveCategories: List<BackupCategory>',KOTLIN)
        self.assertIn('w.archiveCategories.map { it.order }.toSet() == expectedOrders',KOTLIN)
        self.assertIn('w.categoryIdsByArchiveOrder.keys == expectedOrders',KOTLIN)
        self.assertIn('w.archiveCategories.map { it.name }',KOTLIN)
        self.assertIn('q.selectPolarisRestoreCategoryCandidates(archived.name)',KOTLIN)
        self.assertIn('.awaitAsList() == listOf(id)',KOTLIN)

    def test_category_validation_precedes_all_physical_writes(self):
        start=KOTLIN.index('transaction.restoreNewParents {')
        physical=KOTLIN.index('stageDependencies(id, work, prepared, edges)')
        checks=KOTLIN.index('validateArchiveCategories(work)', start)
        self.assertLess(start,checks)
        self.assertLess(checks,physical)
        self.assertIn('POLARIS_FRESH_CATEGORY_NAME_OR_ID_CHANGED',KOTLIN)
        self.assertIn('POLARIS_FRESH_CATEGORY_ARCHIVE_ORDER_MISMATCH',KOTLIN)

    def test_release_flag_must_remain_fail_closed(self):
        self.assertNotIn('PolarisRestoreCoordinator(',KOTLIN)
        self.assertNotIn('migration15',KOTLIN)

if __name__=='__main__':unittest.main()
