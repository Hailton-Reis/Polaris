"""Kotlin emitted Prepared -> actual SQL statements -> physical readback."""
import json
import os
import subprocess
import pathlib
import sys
import unittest
from dataclasses import replace

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from physical_parent_writer import Batch,Edge,restore_fresh_parents,SQL,QUERY_FILE
from test_full_parent_relational_writer import fixture,get,UUID_KEY


class KotlinToSQLiteBridge(unittest.TestCase):
    def projected_batch(self,env='POLARIS_TYPED_PROJECTION_FIXTURE'):
        file = os.environ.get(env)
        self.assertTrue(file and pathlib.Path(file).is_file(),
                        'POLARIS_KOTLIN_BRIDGE_NOT_EXECUTED: use run_tests.sh')
        payload=json.loads(pathlib.Path(file).read_text(encoding='utf-8'))
        return Batch(uuid=payload['uuid'],digest=payload['digest'],parent=payload['parent'],
            chapters=payload['chapters'],categories=payload['categories'],history=payload['history'],
            tracking=payload['tracking'],exclusions=payload['exclusions'],
            edges=[Edge(**e) for e in payload['edges']])

    def with_previous_202(self,con):
        con.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(202,79,'/real/202','An Existing Real Manga',0,1,1,0,0,0,0)")
        con.commit()

    def test_70_allocator_is_named_staged_sq_query(self):
        self.assertIn('selectPolarisNextFreshParentId',SQL)
        self.assertIn('COALESCE(MAX(_id), 0) + 1',SQL['selectPolarisNextFreshParentId'])

    def test_71_kotlin_can_prepare_nondefault_reserved_203(self):
        batch=self.projected_batch('POLARIS_TYPED_PROJECTION_FIXTURE_203')
        self.assertEqual(batch.parent['reservedParentId'],203)
        self.assertEqual([c['parentId'] for c in batch.chapters],[203])

    def test_72_kotlin_203_written_with_true_allocator_203(self):
        batch=self.projected_batch('POLARIS_TYPED_PROJECTION_FIXTURE_203')
        con=fixture();self.addCleanup(con.close);self.with_previous_202(con)
        self.assertEqual(con.execute(SQL['selectPolarisNextFreshParentId']).fetchone()[0],203)
        self.assertEqual(restore_fresh_parents(con,[batch]),[203])
        self.assertEqual(get(con,'SELECT _id FROM mangas WHERE source=6969'),[(203,)])
        self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_73_stale_kotlin_103_refused_for_allocator_203(self):
        batch=self.projected_batch();con=fixture();self.addCleanup(con.close);self.with_previous_202(con)
        with self.assertRaisesRegex(ValueError,'POLARIS_PREPARED_ID_MISMATCH'):
            restore_fresh_parents(con,[batch])
        self.assertEqual(get(con,'SELECT COUNT(*) FROM polaris_restore_ledger'),[(0,)])
        self.assertEqual(get(con,'SELECT COUNT(*) FROM merged'),[(0,)])
        self.assertFalse(con.in_transaction)

    def test_74_stale_kotlin_203_refused_for_allocator_103(self):
        batch=self.projected_batch('POLARIS_TYPED_PROJECTION_FIXTURE_203')
        con=fixture();self.addCleanup(con.close)
        with self.assertRaisesRegex(ValueError,'POLARIS_PREPARED_ID_MISMATCH'):
            restore_fresh_parents(con,[batch])
        self.assertEqual(get(con,'SELECT COUNT(*) FROM polaris_restore_ledger'),[(0,)])

    def test_75_altered_chapter_id_still_refused_even_for_correct_parent_203(self):
        batch=self.projected_batch('POLARIS_TYPED_PROJECTION_FIXTURE_203')
        con=fixture();self.addCleanup(con.close);self.with_previous_202(con)
        chapters=[dict(c, parentId=200) for c in batch.chapters]
        with self.assertRaisesRegex(ValueError,'POLARIS_PREPARED_ID_MISMATCH'):
            restore_fresh_parents(con,[replace(batch,chapters=chapters)])
        self.assertEqual(get(con,'SELECT COUNT(*) FROM chapters'),[(0,)])

    def test_76_midwrite_failure_with_reserved_203_rolls_back_everything(self):
        batch=self.projected_batch('POLARIS_TYPED_PROJECTION_FIXTURE_203')
        con=fixture();self.addCleanup(con.close);self.with_previous_202(con)
        def fault(stage,pid,conn):
            if stage=='before_parent':raise RuntimeError('SIMULATED_WRITE_FAILURE')
        with self.assertRaisesRegex(RuntimeError,'SIMULATED_WRITE_FAILURE'):
            restore_fresh_parents(con,[batch],fault)
        self.assertEqual(get(con,'SELECT COUNT(*) FROM mangas WHERE source=6969'),[(0,)])
        self.assertEqual(get(con,'SELECT COUNT(*) FROM mangas_categories'),[(0,)])
        self.assertEqual(get(con,'SELECT COUNT(*) FROM polaris_restore_ledger'),[(0,)])
        self.assertFalse(con.in_transaction)

    def test_77_preexisting_real_202_preserved_after_success(self):
        batch=self.projected_batch('POLARIS_TYPED_PROJECTION_FIXTURE_203')
        con=fixture();self.addCleanup(con.close);self.with_previous_202(con)
        restore_fresh_parents(con,[batch])
        self.assertEqual(get(con,'SELECT source,url,title FROM mangas WHERE _id=202'),
                         [(79,'/real/202','An Existing Real Manga')])

    def test_78_kotlin_fixture_invokes_projection_with_reserved_id_not_literal(self):
        body=(HERE/'ProjectionSqlBridgeFixture.kt').read_text()
        self.assertIn('PolarisBackupMangaSqlProjection.prepare(archive, UUID, targetId,',body)
        self.assertIn('fun main(args: Array<String>)',body)

    def invoke(self, *args):
        jar = os.environ.get('POLARIS_KOTLIN_BRIDGE_JAR')
        self.assertTrue(jar and pathlib.Path(jar).is_file(), 'Kotlin compilation missing')
        return subprocess.run(['java','-jar',jar,*args],text=True,capture_output=True,check=False)

    def test_80_zero_reserved_parent_arg_is_rejected(self):
        p=self.invoke('0')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('POLARIS_BAD_TEST_RESERVED_ID',p.stderr)

    def test_81_malformed_reserved_parent_arg_is_not_silently_defaulted(self):
        p=self.invoke('not-an-id')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('POLARIS_INVALID_RESERVED_ID_ARGUMENT',p.stderr)

    def test_82_multiple_reserved_parent_args_are_rejected(self):
        p=self.invoke('203','204')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('POLARIS_EXTRA_RESERVED_ID_ARGUMENTS',p.stderr)

    def test_83_kotlin_projected_204_matches_allocator_204(self):
        p=self.invoke('204')
        self.assertEqual(p.returncode,0,p.stderr)
        b=json.loads(p.stdout)
        con=fixture();self.addCleanup(con.close);self.with_previous_202(con)
        con.execute("INSERT INTO mangas(_id,source,url,title,status,favorite,initialized,viewer,chapter_flags,cover_last_modified,date_added) VALUES(203,79,'/real/203','Preexisting',0,1,1,0,0,0,0)")
        con.commit()
        self.assertEqual(con.execute(SQL['selectPolarisNextFreshParentId']).fetchone()[0],204)
        batch=Batch(uuid=b['uuid'],digest=b['digest'],parent=b['parent'],chapters=b['chapters'],
            categories=b['categories'],history=b['history'],tracking=b['tracking'],
            exclusions=b['exclusions'],edges=[Edge(**e) for e in b['edges']])
        self.assertEqual(restore_fresh_parents(con,[batch]),[204])

    def test_79_legacy_batch_fixture_103_still_works(self):
        b=self.projected_batch();con=fixture();self.addCleanup(con.close)
        self.assertEqual(b.parent['reservedParentId'],103)
        self.assertEqual(restore_fresh_parents(con,[b]),[103])
    def test_kotlin_projected_rows_are_physically_written_and_verified(self):
        fixture_file=os.environ.get('POLARIS_TYPED_PROJECTION_FIXTURE')
        if not fixture_file:
            self.fail('POLARIS_KOTLIN_BRIDGE_NOT_EXECUTED: use run_tests.sh')
        payload=json.loads(pathlib.Path(fixture_file).read_text(encoding='utf-8'))
        batch=Batch(uuid=payload['uuid'],digest=payload['digest'],parent=payload['parent'],
            chapters=payload['chapters'],categories=payload['categories'],history=payload['history'],
            tracking=payload['tracking'],exclusions=payload['exclusions'],
            edges=[Edge(**e) for e in payload['edges']])
        con=fixture();self.addCleanup(con.close)
        ids=restore_fresh_parents(con,[batch])
        self.assertEqual(len(ids),1)
        self.assertEqual(get(con,'SELECT title,notes,last_modified_at,version FROM mangas WHERE _id=?',(ids[0],)),
            [('Projected Parent','Kotlin projected into SQLite',4444,12)])
        self.assertEqual(get(con,'SELECT c.url,h.time_read FROM history h JOIN chapters c ON c._id=h.chapter_id'),[('/ch-proj',88)])
        self.assertEqual(json.loads(get(con,'SELECT memo FROM mangas WHERE _id=?',(ids[0],))[0][0])['preserved'],'yes')
        self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])
        print('POLARIS_KOTLIN_SQL_BRIDGE_PASS')
