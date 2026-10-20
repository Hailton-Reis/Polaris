"""Kotlin emitted Prepared -> actual SQL statements -> physical readback."""
import json
import os
import pathlib
import sys
import unittest

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from physical_parent_writer import Batch,Edge,restore_fresh_parents
from test_full_parent_relational_writer import fixture,get,UUID_KEY


class KotlinToSQLiteBridge(unittest.TestCase):
    def test_kotlin_projected_rows_are_physically_written_and_verified(self):
        fixture_file=os.environ.get('POLARIS_TYPED_PROJECTION_FIXTURE')
        if not fixture_file:
            self.skipTest('Kotlin fixture requires run_tests.sh to compile Kotlin projection')
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
