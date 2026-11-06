"""Upload verified assets to an existing draft using the runner's normal gh authentication."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from prepare_assets import check_file, safe_file, unique_artifacts


def gh(*arguments):
    return subprocess.check_output(['gh', *arguments], text=True)


def release(repo, tag):
    releases = json.loads(gh('api', f'repos/{repo}/releases?per_page=100'))
    found = [item for item in releases if item['tag_name'] == tag]
    if len(found) != 1:
        raise ValueError('Expected exactly one prepared draft')
    item = found[0]
    if not item['draft'] or not item['prerelease']:
        raise ValueError('Only an unpublished prerelease draft can receive this upload')
    return item


def upload(repo, plan, assets):
    if repo != plan['repository']:
        raise ValueError('Repository mismatch')
    current = release(repo, plan['tag'])
    if current['target_commitish'] != plan['source_commit']:
        raise ValueError('Draft points at a different source commit')
    expected = unique_artifacts(plan) + plan['files']
    for item in expected:
        path = safe_file(assets, item['file'])
        check_file(path, item)
        existing = [a for a in current['assets'] if a['name'] == item['file']]
        if existing:
            asset = existing[0]
            if asset['size'] != item['bytes'] or asset['state'] != 'uploaded':
                raise ValueError('Existing draft asset differs; refusing replacement')
            if asset.get('digest') != 'sha256:' + item['sha256']:
                with tempfile.TemporaryDirectory() as directory:
                    subprocess.run(['gh', 'release', 'download', plan['tag'], '--repo', repo,
                                    '--pattern', item['file'], '--dir', directory], check=True)
                    check_file(Path(directory) / item['file'], item)
            continue
        subprocess.run(['gh', 'release', 'upload', plan['tag'], str(path), '--repo', repo], check=True)
    current = release(repo, plan['tag'])
    observed = {a['name']: a for a in current['assets']}
    for item in expected:
        asset = observed.get(item['file'], {})
        if asset.get('size') != item['bytes'] or asset.get('state') != 'uploaded':
            raise ValueError('Upload verification failed: ' + item['file'])
        digest = asset.get('digest')
        if digest and digest != 'sha256:' + item['sha256']:
            raise ValueError('Uploaded checksum differs: ' + item['file'])
    print(json.dumps({'status': 'DRAFT_ASSETS_UPLOADED_NOT_PUBLISHED', 'release_id': current['id'],
                      'assets': [{'name': a['name'], 'bytes': a['size'], 'digest': a.get('digest')}
                                 for a in current['assets']]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True)
    args = parser.parse_args()
    upload(args.repository, json.loads(args.plan.read_text()), args.assets)


if __name__ == '__main__':
    main()
