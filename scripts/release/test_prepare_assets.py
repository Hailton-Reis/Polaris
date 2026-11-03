import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prepare_assets import prepare
from upload_assets import release, upload


def record(name, data):
    return {'file': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


class ReleaseBytesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.payload = self.root / 'input'
        self.payload.mkdir()
        self.output = self.root / 'output'
        self.plan = {'repository': 'Hailton-Reis/Polaris', 'tag': 'v0.1.0-beta.8',
                     'source_commit': '1' * 40, 'version_code': 109,
                     'application_id': 'app.mihon.tachiyomiat.dev', 'minimum_android_api': 26,
                     'signer_sha256': 'a' * 64, 'artifacts': [], 'files': []}
        for abi in ['arm64-v8a', 'armeabi-v7a']:
            name = 'Polaris-0.1.0-beta.8-' + abi + '.apk'
            chunks = [b'reviewed first bytes ' + abi.encode(), b'reviewed final bytes']
            item = {'abi': abi, **record(name, b''.join(chunks)), 'parts': []}
            for index, data in enumerate(chunks, 1):
                part = name + f'.{index:03d}'
                (self.payload / part).write_bytes(data)
                item['parts'].append(record(part, data))
            self.plan['artifacts'].append(item)
        manifest = {k: self.plan[k] for k in ['source_commit', 'version_code', 'application_id', 'minimum_android_api', 'signer_sha256']}
        manifest.update(version='0.1.0-beta.8', artifacts=[{k: a[k] for k in ['abi', 'file', 'bytes', 'sha256']}
                                                       for a in self.plan['artifacts']])
        data = json.dumps(manifest).encode()
        (self.payload / 'manifest.json').write_bytes(data)
        self.plan['files'] = [record('manifest.json', data)]

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_bytes_and_identity_produce_the_reviewed_bundle(self):
        names = prepare(self.plan, self.payload, self.output)
        self.assertEqual(len(names), 3)
        for item in self.plan['artifacts']:
            self.assertEqual(hashlib.sha256((self.output / item['file']).read_bytes()).hexdigest(), item['sha256'])

    def test_corrupt_part_never_creates_a_partial_output(self):
        part = self.plan['artifacts'][0]['parts'][0]['file']
        (self.payload / part).write_bytes(b'corrupted')
        with self.assertRaises(ValueError):
            prepare(self.plan, self.payload, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        (self.output / 'keep').write_text('existing data')
        with self.assertRaises(ValueError):
            prepare(self.plan, self.payload, self.output)
        self.assertEqual((self.output / 'keep').read_text(), 'existing data')

    def test_path_traversal_and_symlinks_are_rejected(self):
        self.plan['files'][0]['file'] = '../manifest.json'
        with self.assertRaises(ValueError):
            prepare(self.plan, self.payload, self.output)
        self.plan['files'][0]['file'] = 'manifest.json'
        (self.payload / 'manifest.json').rename(self.root / 'elsewhere')
        (self.payload / 'manifest.json').symlink_to(self.root / 'elsewhere')
        with self.assertRaises(ValueError):
            prepare(self.plan, self.payload, self.output)

    def test_architecture_and_manifest_identity_mismatches_are_rejected(self):
        other = copy.deepcopy(self.plan)
        other['artifacts'][1]['abi'] = 'x86'
        with self.assertRaises(ValueError):
            prepare(other, self.payload, self.output)
        other = copy.deepcopy(self.plan)
        other['version_code'] = 999
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            prepare(other, self.payload, self.output)

    def test_a_single_missing_or_reordered_part_fails_closed(self):
        self.plan['artifacts'][0]['parts'].reverse()
        with self.assertRaises(ValueError):
            prepare(self.plan, self.payload, self.output)
        self.assertFalse(self.output.exists())

    def test_published_releases_cannot_receive_this_upload(self):
        with patch('upload_assets.gh', return_value=json.dumps([{'tag_name': self.plan['tag'], 'draft': False, 'prerelease': True}])):
            with self.assertRaisesRegex(ValueError, 'unpublished'):
                release(self.plan['repository'], self.plan['tag'])

    def test_repository_mismatch_never_calls_the_network(self):
        with patch('upload_assets.gh') as network:
            with self.assertRaisesRegex(ValueError, 'Repository mismatch'):
                upload('someone/else', self.plan, self.output)
            network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
