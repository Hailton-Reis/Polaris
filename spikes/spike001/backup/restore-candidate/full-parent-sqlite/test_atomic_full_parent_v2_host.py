"""Offline SQLite transactional field-preservation regression suite (NO Android)."""
import base64
import copy
import json
import sqlite3
import unittest
from atomic_full_parent_v2_host import (
    install_host_schema, restore_all_or_throw, memo_object, UUID_MEMO,
    MANGA_FIELDS, CHAPTER_FIELDS, HISTORY_FIELDS, TRACKING_FIELDS,
)

U1='123e4567-e89b-42d3-a456-426614174000'
U2='123e4567-e89b-42d3-a456-426614174001'

def enc(value):
    return base64.b64encode(json.dumps(value,ensure_ascii=False).encode()).decode()

def sample(uuid=U1):
    ch={'url':'/chapter1','name':'Chapter One','scanlator':'Translator','read':True,
       'bookmark':True,'lastPageRead':19,'dateFetch':10,'dateUpload':20,
       'chapterNumber':1.0,'sourceOrder':4,'lastModifiedAt':30,'version':1,
       'memo_b64':enc({'chapter.extra':'value','nested':{'x':[1,2]}})}
    h={'url':'/chapter1','lastRead':123456,'readDuration':99}
    tr={'syncId':2,'libraryId':11,'mediaIdInt':0,'trackingUrl':'/work','title':'Original',
        'lastChapterRead':2.5,'totalChapters':100,'score':8.5,'status':1,
        'startedReadingDate':10,'finishedReadingDate':0,'private':False,'mediaId':42}
    manga={'source':6969,'url':'merged://old-device/999','title':'Português 漫画',
        'artist':'A', 'author':'B','description':'Preserve original','genre':['Action','Drama'],
        'status':2,'thumbnailUrl':'https://example.invalid/cover','dateAdded':14,'viewer':5,
        'chapters':[ch],'categories':[4,7],'tracking':[tr],'favorite':True,
        'chapterFlags':8,'viewer_flags':9,'history':[h],'updateStrategy':'ALWAYS_UPDATE',
        'lastModifiedAt':22,'favoriteModifiedAt':23,'excludedScanlators':['Bad translator'],
        'version':4,'notes':'Keep this note!','initialized':True,
        'memo_b64':enc({'user.key':'important','nested':{'hello':'world'},'number':3})}
    return {'uuid':uuid,'snapshot':manga,'edges':[{'source':77,'url':'/source/1','real_id':101,
            'pending':False,'settings':{'priority':1,'info':True}},{'source':88,'url':'/not-available',
            'real_id':None,'pending':True,'settings':{'priority':5,'info':False}}]}


class AtomicV2ParentTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        install_host_schema(self.db)
        self.db.execute('INSERT INTO categories(_id,name) VALUES(91,\'Read\'),(92,\'Favorite\')')
        self.db.execute('INSERT INTO mangas(_id,source,url,title,payload_json,memo_json) VALUES(101,77,\'/source/1\',\'Real\',\'{}\',\'{}\')')
        self.db.commit()
        self.orders={4:'Read',7:'Favorite'}
        self.work=sample()

    def tearDown(self):
        self.db.close()

    def apply(self,works=None,orders=None,**kwargs):
        return restore_all_or_throw(self.db, [self.work] if works is None else works,
                                   self.orders if orders is None else orders,**kwargs)

    def assert_failure(self,works=None,orders=None):
        with self.assertRaises((ValueError,sqlite3.IntegrityError,RuntimeError)):
            self.apply(works,orders)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM chapters').fetchone()[0],0)

    def test_pinned_field_contract_covers_entire_snapshot(self):
        self.assertEqual(set(self.work['snapshot']),MANGA_FIELDS)
        self.assertEqual(set(self.work['snapshot']['chapters'][0]),CHAPTER_FIELDS)
        self.assertEqual(set(self.work['snapshot']['history'][0]),HISTORY_FIELDS)
        self.assertEqual(set(self.work['snapshot']['tracking'][0]),TRACKING_FIELDS)

    def test_create_stable_uuid_parent_not_old_archive_url(self):
        pid=self.apply()[0]
        self.assertEqual(self.db.execute('SELECT url FROM mangas WHERE _id=?',(pid,)).fetchone()[0],
                         'merged://polaris/'+U1)
        self.assertEqual(self.db.execute('SELECT json_extract(payload_json,\'$.url\') FROM mangas WHERE _id=?',(pid,)).fetchone()[0],
                         'merged://old-device/999')

    def test_original_metadata_fields_preserved_in_payload(self):
        pid=self.apply()[0]
        payload=json.loads(self.db.execute('SELECT payload_json FROM mangas WHERE _id=?',(pid,)).fetchone()[0])
        self.assertEqual(payload,self.work['snapshot'])
        self.assertEqual(payload['notes'],'Keep this note!')
        self.assertEqual(payload['viewer_flags'],9)

    def test_memo_keeps_all_opaque_user_keys_and_adds_uuid(self):
        pid=self.apply()[0]
        stored=json.loads(self.db.execute('SELECT memo_json FROM mangas WHERE _id=?',(pid,)).fetchone()[0])
        self.assertEqual(stored[UUID_MEMO],U1)
        self.assertEqual(stored['nested'],{'hello':'world'})
        self.assertEqual(stored['user.key'],'important')

    def test_categories_resolve_by_order_then_name_to_local_ids(self):
        pid=self.apply()[0]
        result=self.db.execute('SELECT category_id FROM mangas_categories WHERE manga_id=? ORDER BY category_id',(pid,)).fetchall()
        self.assertEqual(result,[(91,),(92,)])

    def test_categories_can_be_remapped_to_different_local_ids(self):
        self.db.execute("UPDATE categories SET _id=201 WHERE name='Read'")
        self.db.commit()
        pid=self.apply()[0]
        self.assertEqual(set(self.db.execute('SELECT category_id FROM mangas_categories WHERE manga_id=?',(pid,)).fetchall()),{(201,),(92,)})

    def test_chapter_payload_and_memo_bytes_exact(self):
        pid=self.apply()[0]
        stored=json.loads(self.db.execute('SELECT payload_json FROM chapters WHERE manga_id=?',(pid,)).fetchone()[0])
        self.assertEqual(stored,self.work['snapshot']['chapters'][0])
        self.assertEqual(memo_object(stored['memo_b64'])['chapter.extra'],'value')

    def test_history_binds_to_exact_new_chapter_id(self):
        pid=self.apply()[0]
        row=self.db.execute('SELECT c.url,h.payload_json FROM history h JOIN chapters c ON c._id=h.chapter_id WHERE c.manga_id=?',(pid,)).fetchone()
        self.assertEqual(row[0],'/chapter1')
        self.assertEqual(json.loads(row[1])['lastRead'],123456)

    def test_tracking_and_exclusions_preserved(self):
        pid=self.apply()[0]
        tr=self.db.execute('SELECT payload_json FROM tracking WHERE manga_id=?',(pid,)).fetchone()[0]
        self.assertEqual(json.loads(tr),self.work['snapshot']['tracking'][0])
        self.assertEqual(self.db.execute('SELECT scanlator FROM excluded_scanlators WHERE manga_id=?',(pid,)).fetchone()[0], 'Bad translator')

    def test_pending_remains_null_and_real_child_fk_is_valid(self):
        pid=self.apply()[0]
        edges=self.db.execute('SELECT source_id,real_manga_id FROM merged WHERE parent_id=? ORDER BY source_id',(pid,)).fetchall()
        self.assertEqual(edges,[(77,101),(88,None)])
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_replay_returns_same_id_and_never_inserts_duplicates(self):
        pid=self.apply()[0]; again=self.apply()[0]
        self.assertEqual(pid,again)
        for table in ['polaris_restore_ledger','chapters','history','tracking','merged']:
            self.assertEqual(self.db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],
                             {'merged':2}.get(table,1))

    def test_replay_detects_user_note_modified_in_payload(self):
        pid=self.apply()[0]
        payload=json.loads(self.db.execute('SELECT payload_json FROM mangas WHERE _id=?',(pid,)).fetchone()[0])
        payload['notes']='User edited locally'
        self.db.execute('UPDATE mangas SET payload_json=? WHERE _id=?',(json.dumps(payload),pid));self.db.commit()
        with self.assertRaisesRegex(ValueError,'unchanged full metadata replay'):self.apply()

    def test_replay_detects_child_progress_modified(self):
        pid=self.apply()[0]
        cid,data=self.db.execute('SELECT _id,payload_json FROM chapters WHERE manga_id=?',(pid,)).fetchone()
        ch=json.loads(data);ch['lastPageRead']=99
        self.db.execute('UPDATE chapters SET payload_json=? WHERE _id=?',(json.dumps(ch),cid));self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_replay_detects_deleted_history(self):
        self.apply();self.db.execute('DELETE FROM history');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_replay_detects_removed_category(self):
        self.apply();self.db.execute('DELETE FROM mangas_categories');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_replay_detects_modified_tracking(self):
        self.apply();self.db.execute('UPDATE tracking SET payload_json=\'{}\'');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_replay_detects_changed_memo_nested_value(self):
        self.apply();self.db.execute('UPDATE mangas SET memo_json=\'{}\' WHERE source=6969');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_replay_detects_detached_link_even_when_digest_unchanged(self):
        self.apply();self.db.execute('DELETE FROM merged WHERE source_id=77');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_replay_detects_real_source_changed_under_same_id(self):
        self.apply();self.db.execute('UPDATE mangas SET url=\'/different\' WHERE _id=101');self.db.commit()
        with self.assertRaises(ValueError):self.apply()

    def test_injected_failure_rolls_back_parent_and_all_relations(self):
        with self.assertRaises(RuntimeError):self.apply(fail_after_parent=0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas WHERE source=6969').fetchone()[0],0)
        for t in ['chapters','history','tracking','mangas_categories','merged','polaris_restore_ledger']:
            self.assertEqual(self.db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0],0)
        self.assertEqual(len(self.apply()),1)

    def test_second_parent_failure_rolls_back_first_parent(self):
        second=sample(U2);second['edges'][0]['url']='/source/2';second['edges'][0]['real_id']=102
        self.db.execute('INSERT INTO mangas(_id,source,url,title,payload_json,memo_json) VALUES(102,77,\'/source/2\',\'Two\',\'{}\',\'{}\')');self.db.commit()
        with self.assertRaises(RuntimeError):self.apply([self.work,second],fail_after_parent=1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM mangas WHERE source=6969').fetchone()[0],0)

    def test_two_distinct_parents_commit_atomically(self):
        second=sample(U2);second['edges'][0]['url']='/source/2';second['edges'][0]['real_id']=102
        self.db.execute('INSERT INTO mangas(_id,source,url,title,payload_json,memo_json) VALUES(102,77,\'/source/2\',\'Two\',\'{}\',\'{}\')');self.db.commit()
        ids=self.apply([self.work,second]);self.assertEqual(len(set(ids)),2)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM polaris_restore_ledger').fetchone()[0],2)

    def test_reject_missing_destination_category(self):
        self.assert_failure(orders={4:'Read',7:'Deleted'})

    def test_reject_missing_archived_category_order(self):
        self.assert_failure(orders={4:'Read'})

    def test_reject_duplicate_category_names(self):
        self.assert_failure(orders={4:'Read',7:'Read'})

    def test_reject_history_without_matching_chapter(self):
        w=copy.deepcopy(self.work);w['snapshot']['history'][0]['url']='/absent'
        self.assert_failure(works=[w])

    def test_reject_repeated_chapter_url(self):
        w=copy.deepcopy(self.work);w['snapshot']['chapters'].append(copy.deepcopy(w['snapshot']['chapters'][0]))
        self.assert_failure(works=[w])

    def test_reject_repeated_tracker(self):
        w=copy.deepcopy(self.work);w['snapshot']['tracking'].append(copy.deepcopy(w['snapshot']['tracking'][0]))
        self.assert_failure(works=[w])

    def test_reject_foreign_uuid_in_origin_memo(self):
        w=copy.deepcopy(self.work);w['snapshot']['memo_b64']=enc({UUID_MEMO:U2})
        self.assert_failure(works=[w])

    def test_reject_corrupt_memo(self):
        w=copy.deepcopy(self.work);w['snapshot']['memo_b64']='garbage'
        self.assert_failure(works=[w])

    def test_reject_missing_full_metadata_field(self):
        w=copy.deepcopy(self.work);del w['snapshot']['viewer_flags']
        self.assert_failure(works=[w])

    def test_reject_future_unknown_metadata_field(self):
        w=copy.deepcopy(self.work);w['snapshot']['new_unhandled']='data'
        self.assert_failure(works=[w])

    def test_reject_missing_source_child(self):
        self.db.execute('DELETE FROM mangas WHERE _id=101');self.db.commit()
        self.assert_failure()

    def test_reject_pending_resolved_identity_mismatch(self):
        w=copy.deepcopy(self.work);w['edges'][0]['pending']=True
        self.assert_failure(works=[w])

    def test_reject_duplicate_source_link(self):
        w=copy.deepcopy(self.work);w['edges'].append(copy.deepcopy(w['edges'][0]))
        self.assert_failure(works=[w])

    def test_reject_legacy_unledgered_uuid_collision(self):
        self.db.execute('INSERT INTO mangas(source,url,title,payload_json,memo_json) VALUES(?,?,?,?,?)',
                        (6969,'merged://legacy/one','Legacy','{}',json.dumps({UUID_MEMO:U1})));self.db.commit()
        self.assert_failure()

    def test_reject_uuid_stable_url_collision_without_ledger(self):
        self.db.execute('INSERT INTO mangas(source,url,title,payload_json,memo_json) VALUES(?,?,?,?,?)',
                        (6969,'merged://polaris/'+U1,'Hijack','{}','{}'));self.db.commit()
        self.assert_failure()

    def test_reject_same_uuid_with_altered_archive_payload(self):
        self.apply();w=copy.deepcopy(self.work);w['snapshot']['notes']='Different archive'
        with self.assertRaises(ValueError):self.apply([w])

    def test_reject_same_uuid_with_changed_source_association(self):
        self.apply();w=copy.deepcopy(self.work);w['edges'][1]['settings']['priority']=6
        with self.assertRaises(ValueError):self.apply([w])

    def test_missing_uuid_rejected(self):
        w=copy.deepcopy(self.work);w['uuid']='invalid'
        self.assert_failure(works=[w])

    def test_refuse_unknown_outer_transaction(self):
        self.db.execute('BEGIN')
        with self.assertRaises(RuntimeError):self.apply()
        self.db.rollback()

    def test_replay_category_remap_changed_rejected(self):
        self.apply()
        self.db.execute("INSERT INTO categories(_id,name) VALUES(98,'Changed')");self.db.commit()
        with self.assertRaises(ValueError):self.apply(orders={4:'Read',7:'Changed'})

if __name__=='__main__':unittest.main(verbosity=2)
