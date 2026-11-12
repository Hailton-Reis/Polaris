"""Scoped wire-level PROXY for new v2 canonical admission envelope.

It uses Google's Python protobuf implementation, NOT the Android Kotlin
kotlinx.serialization ProtoBuf runtime. Do not treat this as release proof.
"""
from __future__ import annotations
import hashlib
import pathlib
import re
import unittest
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/'PolarisV2ProtoBufEnvelope.kt').read_text(encoding='utf-8')
GATE=(ROOT/'PolarisV2DecodedEnvelopeGateway.kt').read_text(encoding='utf-8')

F=descriptor_pb2.FieldDescriptorProto

def build():
    f=descriptor_pb2.FileDescriptorProto(name='polaris_v2_admission_host.proto',package='polaris.r001',syntax='proto2')
    types={}
    for name in ['Settings','Link','Work','Chapter','Manga','Parent','Category','Envelope']:
        types[name]=f.message_type.add();types[name].name=name
    def add(owner,name,number,typ,repeated=False,ref=None):
        field=types[owner].field.add(name=name,number=number,type=typ,
            label=F.LABEL_REPEATED if repeated else F.LABEL_OPTIONAL)
        if ref:field.type_name='.polaris.r001.'+ref
    add('Settings','infoManga',1,F.TYPE_BOOL);add('Settings','getChapterUpdates',2,F.TYPE_BOOL)
    add('Settings','chapterSortMode',3,F.TYPE_INT64);add('Settings','chapterPriority',4,F.TYPE_INT64)
    add('Settings','downloadChapters',5,F.TYPE_BOOL)
    add('Link','sourceId',1,F.TYPE_INT64);add('Link','sourceUrl',2,F.TYPE_STRING)
    add('Link','observedTitle',3,F.TYPE_STRING);add('Link','settings',4,F.TYPE_MESSAGE,ref='Settings')
    add('Link','isPending',5,F.TYPE_BOOL)
    add('Work','archiveWorkKey',1,F.TYPE_STRING);add('Work','displayTitle',2,F.TYPE_STRING)
    add('Work','rootSettings',3,F.TYPE_MESSAGE,ref='Settings');add('Work','links',4,F.TYPE_MESSAGE,True,'Link')
    add('Work','canonicalUuid',5,F.TYPE_STRING)
    add('Chapter','url',1,F.TYPE_STRING);add('Chapter','name',2,F.TYPE_STRING)
    add('Manga','source',1,F.TYPE_INT64);add('Manga','url',2,F.TYPE_STRING)
    add('Manga','title',3,F.TYPE_STRING);add('Manga','chapters',16,F.TYPE_MESSAGE,True,'Chapter')
    add('Manga','categories',17,F.TYPE_INT64,True);add('Manga','memo',112,F.TYPE_BYTES)
    add('Parent','archiveUuid',1,F.TYPE_STRING);add('Parent','manga',2,F.TYPE_MESSAGE,ref='Manga')
    add('Parent','originalOrdinal',3,F.TYPE_INT32)
    add('Category','name',1,F.TYPE_STRING);add('Category','order',2,F.TYPE_INT64)
    add('Category','id',3,F.TYPE_INT64);add('Category','flags',100,F.TYPE_INT64)
    add('Envelope','formatVersion',1,F.TYPE_INT32);add('Envelope','work',2,F.TYPE_MESSAGE,ref='Work')
    add('Envelope','parent',3,F.TYPE_MESSAGE,ref='Parent')
    add('Envelope','referencedCategories',4,F.TYPE_MESSAGE,True,'Category')
    pool=descriptor_pool.DescriptorPool();pool.Add(f)
    return message_factory.GetMessageClass(pool.FindMessageTypeByName('polaris.r001.Envelope'))

Envelope=build()
UUID='123e4567-e89b-42d3-a456-426614174000'
def example():
    a=Envelope();a.formatVersion=2
    a.work.archiveWorkKey=UUID;a.work.canonicalUuid=UUID;a.work.displayTitle='Coração de Jade'
    a.work.rootSettings.chapterPriority=10;a.work.rootSettings.infoManga=False
    link=a.work.links.add();link.sourceId=77;link.sourceUrl='/capitulo';link.observedTitle='第一卷'
    link.settings.infoManga=True;link.settings.chapterPriority=0;link.isPending=True
    a.parent.archiveUuid=UUID;a.parent.originalOrdinal=0
    a.parent.manga.source=6969;a.parent.manga.url='merged://old';a.parent.manga.title=a.work.displayTitle
    a.parent.manga.categories.append(9);a.parent.manga.memo=b'{"notes":"teste","nested":{"key":2}}'
    ch=a.parent.manga.chapters.add();ch.url='/chapter/1';ch.name='第三话'
    cat=a.referencedCategories.add();cat.name='Português';cat.order=9;cat.id=123;cat.flags=5
    return a

def hash_bytes(m):return hashlib.sha256(m.SerializeToString(deterministic=True)).hexdigest()

class WireContract(unittest.TestCase):
    def test_envelope_tag_numbers_are_unique_and_exact_in_kotlin(self):
        tags=re.findall(r'@ProtoNumber\((\d+)\) val (\w+)',SRC)
        self.assertEqual(tags,[('1','formatVersion'),('2','work'),('3','parent'),('4','referencedCategories')])
    def test_gateway_validates_original_bundle_before_materializing(self):
        self.assertLess(GATE.index('bundle.validateSnapshotCoverage(ordinaryManga)'),GATE.index('PolarisV2SnapshotAdmission.fromDecoded'))
    def test_gateway_never_takes_external_digest_or_bytes(self):
        sig=GATE.split('fun admitDecodedParent(',1)[1].split('): PolarisV2SnapshotAdmission',1)[0]
        self.assertNotRegex(sig,r'\b(digest|snapshotBytes|archiveDigest)\b')
    def test_actual_kt_proto_codec_uses_compiler_generated_serializer(self):
        self.assertIn('PolarisV2ProtoBufEnvelope.serializer()',SRC)
        self.assertIn('proto.decodeFromByteArray(',SRC)
        self.assertIn('proto.encodeToByteArray(',SRC)
    def test_real_parent_payload_and_portable_link_models_not_reinvented(self):
        self.assertIn('BackupPolarisParentPayload',SRC)
        self.assertIn('BackupPolarisWork',SRC)
        self.assertIn('List<BackupCategory>',SRC)
    def test_full_wire_proxy_roundtrip(self):
        x=example();raw=x.SerializeToString(deterministic=True)
        y=Envelope.FromString(raw)
        self.assertEqual(y.SerializeToString(deterministic=True),raw)
        self.assertEqual(y.parent.manga.chapters[0].name,'第三话')
        self.assertEqual(y.referencedCategories[0].name,'Português')
        self.assertEqual(y.work.links[0].isPending,True)
    def test_chapter_mutation_changes_parent_hash(self):
        a=example();b=example();b.parent.manga.chapters[0].name='Outra'
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_memo_mutation_changes_parent_hash(self):
        a=example();b=example();b.parent.manga.memo=b'{}'
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_link_settings_mutation_changes_parent_hash(self):
        a=example();b=example();b.work.links[0].settings.chapterPriority=3
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_pending_status_mutation_changes_parent_hash(self):
        a=example();b=example();b.work.links[0].isPending=False
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_original_category_name_mutation_changes_hash(self):
        a=example();b=example();b.referencedCategories[0].name='Renamed'
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_original_category_flags_mutation_changes_hash(self):
        a=example();b=example();b.referencedCategories[0].flags=99
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_ordinal_and_version_affect_hash(self):
        a=example();b=example();b.parent.originalOrdinal=4
        self.assertNotEqual(hash_bytes(a),hash_bytes(b));b=example();b.formatVersion=1
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_parent_title_mutation_affects_hash(self):
        a=example();b=example();b.parent.manga.title='Mutated'
        self.assertNotEqual(hash_bytes(a),hash_bytes(b))
    def test_local_dest_parent_id_not_serialized(self):
        s=SRC
        self.assertNotIn('parentLocalId',s)
        self.assertNotIn('destinationCategoryId',s)
    def test_no_premature_coordinator_unlock_or_migration(self):
        self.assertNotIn('PolarisRestoreCoordinator(',SRC+GATE)
        self.assertNotIn('migration15',SRC+GATE)

if __name__=='__main__':unittest.main()
