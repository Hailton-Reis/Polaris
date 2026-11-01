#!/usr/bin/env python3
"""Apply document support after the reviewed Spike001/debug/reader overlays."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = '0fb80c439ef816eeb50674f1b90af39918b176d8'
PATCH = Path(__file__).resolve().parents[2] / 'integration/document-reader/document-reader.patch'


def apply(root: Path) -> dict:
    root = root.resolve()
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if head != PIN:
        raise ValueError('Document support requires the pinned Yomotsu checkout')
    if (root / 'data/src/main/sqldelight/tachiyomi/migrations/15.sqm').exists():
        raise ValueError('Migration15 is outside document support')
    if not (root / 'app/src/main/java/eu/kanade/translation/presentation/TranslationImageCrop.kt').exists():
        raise ValueError('Apply the current reader translation overlay first')
    command = ['git', '-C', str(root), 'apply', '--whitespace=error']
    check = subprocess.run(command + ['--check', str(PATCH)], capture_output=True, text=True)
    if check.returncode == 0:
        subprocess.run(command + [str(PATCH)], check=True)
        status = 'APPLIED'
    else:
        reverse = subprocess.run(command + ['--reverse', '--check', str(PATCH)], capture_output=True, text=True)
        if reverse.returncode != 0:
            raise ValueError('Document source differs from the reviewed overlay:\n' + check.stderr)
        status = 'ALREADY_APPLIED'
    return {'status': status, 'patch_sha256': hashlib.sha256(PATCH.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    print(json.dumps(apply(parser.parse_args().root)))
