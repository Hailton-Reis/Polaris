"""Reassemble reviewed release bytes from a disposable transport checkout.

This script executes no code from the transport checkout and never publishes a release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile


def safe_file(root, name):
    if not isinstance(name, str) or Path(name).name != name or name in ('', '.', '..'):
        raise ValueError('Unsafe release filename')
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing or symlinked release file: ' + name)
    return path


def check_file(path, expected):
    if path.stat().st_size != expected['bytes']:
        raise ValueError('Wrong byte count: ' + path.name)
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected['sha256']:
        raise ValueError('Wrong SHA-256: ' + path.name)


def prepare(plan, payload, output):
    if output.exists():
        raise ValueError('Output must be a new directory')
    if not re.fullmatch(r'v\d+\.\d+\.\d+-beta\.\d+', plan['tag']):
        raise ValueError('Only reviewed beta tags are accepted')
    if len(plan['artifacts']) != 2 or {a['abi'] for a in plan['artifacts']} != {'arm64-v8a', 'armeabi-v7a'}:
        raise ValueError('Expected one artifact per supported ARM architecture')
    names = [a['file'] for a in plan['artifacts']] + [a['file'] for a in plan['files']]
    if len(names) != len(set(names)):
        raise ValueError('Repeated asset name')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.release-', dir=output.parent) as directory:
        stage = Path(directory)
        for artifact in plan['artifacts']:
            expected_name = 'Polaris-' + plan['tag'][1:] + '-' + artifact['abi'] + '.apk'
            if artifact['file'] != expected_name or not artifact['parts']:
                raise ValueError('Unexpected APK name or empty parts')
            target = stage / expected_name
            with target.open('wb') as destination:
                for index, part in enumerate(artifact['parts'], 1):
                    if part['file'] != expected_name + f'.{index:03d}':
                        raise ValueError('Unordered APK parts')
                    source = safe_file(payload, part['file'])
                    check_file(source, part)
                    with source.open('rb') as stream:
                        shutil.copyfileobj(stream, destination, 1024 * 1024)
            check_file(target, artifact)
        for item in plan['files']:
            source = safe_file(payload, item['file'])
            check_file(source, item)
            shutil.copy2(source, stage / item['file'])
        manifest = json.loads((stage / 'manifest.json').read_text())
        for field in ['version_code', 'application_id', 'minimum_android_api', 'signer_sha256']:
            if manifest[field] != plan[field]:
                raise ValueError('Manifest identity mismatch: ' + field)
        if manifest['version'] != plan['tag'][1:] or manifest['source_commit'] != plan['source_commit']:
            raise ValueError('Manifest version/source mismatch')
        wanted = [{k: a[k] for k in ['abi', 'file', 'bytes', 'sha256']} for a in plan['artifacts']]
        if manifest['artifacts'] != wanted:
            raise ValueError('Manifest artifacts mismatch')
        # Atomic handoff only after all bytes and identities are verified.
        stage.rename(output)
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    names = prepare(json.loads(args.plan.read_text()), args.payload, args.output)
    print(json.dumps({'status': 'VERIFIED_RELEASE_ASSETS', 'files': names}))


if __name__ == '__main__':
    main()
