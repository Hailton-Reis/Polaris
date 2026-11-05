#!/usr/bin/env python3
"""Apply the reviewed reader UX overlay to the pinned, Spike001-patched Android tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = '0fb80c439ef816eeb50674f1b90af39918b176d8'
PATCH = Path(__file__).resolve().parents[2] / 'integration/reader-translation-ux/reader-translation-ux.patch'


def apply(root: Path) -> dict:
    root = root.resolve()
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if head != PIN:
        raise ValueError('Reader UX requires the pinned Yomotsu checkout')
    if (root / 'data/src/main/sqldelight/tachiyomi/migrations/15.sqm').exists():
        raise ValueError('Migration15 is outside this reader UX change')
    command = ['git', '-C', str(root), 'apply', '--whitespace=error']
    check = subprocess.run(command + ['--check', str(PATCH)], capture_output=True, text=True)
    if check.returncode == 0:
        subprocess.run(command + [str(PATCH)], check=True)
        status = 'APPLIED'
    else:
        reverse = subprocess.run(command + ['--reverse', '--check', str(PATCH)], capture_output=True, text=True)
        if reverse.returncode != 0:
            raise ValueError('Reader UX source differs from the reviewed patch:\n' + check.stderr)
        status = 'ALREADY_APPLIED'
    return {'status': status, 'patch_sha256': hashlib.sha256(PATCH.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(apply(args.root)))
