#!/usr/bin/env python3
"""Require completed assembly and complete JUnit coverage for a combined Gradle run."""
import argparse
import json
from pathlib import Path
import re
import sys

from compare_android_unit_tests import ReportError, check_coverage, check_gradle, collect


def verify(root, log, exit_code):
    cases = collect(root)
    check_coverage(cases, {'domain': 58, 'app': 370}, 'combined build')
    check_gradle(log, exit_code, cases, 'combined build')
    if not re.search(r'^> Task :app:assembleDebug(?: UP-TO-DATE| FROM-CACHE)?\s*$',
                     log.read_text(errors='replace'), re.MULTILINE):
        raise ReportError('Combined run did not complete :app:assembleDebug')
    output = root / 'app/build/outputs/apk/debug'
    try:
        metadata = json.loads((output / 'output-metadata.json').read_text())
        if metadata['variantName'] != 'debug' or not metadata['elements']:
            raise ValueError('Not a debug APK listing')
        artifacts = []
        for entry in metadata['elements']:
            name = entry['outputFile']
            if not isinstance(name, str) or Path(name).name != name or not name.endswith('.apk'):
                raise ValueError('Invalid APK filename')
            artifact = output / name
            if not artifact.is_file() or not artifact.stat().st_size:
                raise ValueError(f'Missing/empty APK: {name}')
            artifacts.append(name)
        if 'app-x86_64-debug.apk' not in artifacts:
            raise ValueError('x86_64 test APK missing')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ReportError(f'Incomplete APK outputs: {exc}') from exc
    return {'status': 'ASSEMBLY_AND_UNIT_REPORTS_COMPLETE', 'apks': artifacts, 'unit_tests': len(cases)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--exit-code', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.root, args.log, args.exit_code)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(result['status'] + ' (test regression comparison still required)')
        return 0
    except ReportError as exc:
        print(f'ANDROID_BUILD_INCOMPLETE: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
