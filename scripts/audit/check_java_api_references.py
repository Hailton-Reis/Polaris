"""Check referenced public JVM members against replacement JARs; does not execute native code."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


def check(consumer, old, new, javap):
    def run(jar, *classes, verbose=False):
        args = [javap, '-classpath', str(jar), '-v' if verbose else '-s']
        if not verbose:
            args += ['-public']
        return subprocess.check_output(args + list(classes), text=True)
    with zipfile.ZipFile(consumer) as archive:
        classes = [n[:-6].replace('/', '.') for n in archive.namelist() if n.endswith('.class')]
    listing = run(consumer, *classes, verbose=True)
    references = set()
    for line in listing.splitlines():
        if 'Methodref' not in line and 'Fieldref' not in line:
            continue
        match = re.search(r'// (org/opencv/[\w/$]+)\.([^:]+):(\S+)', line)
        if match:
            owner, name, descriptor = match.groups()
            references.add((owner.replace('/', '.'), name.strip('"'), descriptor))
    if not references:
        raise ValueError('No OpenCV member references found in the consumer')
    @lru_cache(None)
    def definition(jar, owner):
        text = run(Path(jar), owner)
        parent = None if owner == 'java.lang.Object' else 'java.lang.Object'
        members = {}
        previous = ''
        for line in text.splitlines():
            line = line.strip()
            if ' class ' in line:
                match = re.search(r'\bextends ([\w.$]+)', line)
                if match:
                    parent = match.group(1)
            if line.startswith('descriptor:'):
                descriptor = line.split(':', 1)[1].strip()
                if previous.startswith('public '):
                    token = previous.split('(', 1)[0].split()[-1].rstrip(';')
                    name = '<init>' if token == owner else token
                    members[name, descriptor] = 'static' in previous.split()
            previous = line
        return members, parent
    def resolve(jar, owner, name, descriptor):
        visited = set()
        while owner and owner not in visited:
            visited.add(owner)
            members, parent = definition(str(jar), owner)
            if (name, descriptor) in members:
                return {'found': True, 'static': members[name, descriptor], 'declaring_class': owner}
            owner = None if name == '<init>' else parent
        return {'found': False}
    results = []
    for owner, name, descriptor in sorted(references):
        original = resolve(old, owner, name, descriptor)
        candidate = resolve(new, owner, name, descriptor)
        results.append({'class': owner, 'member': name, 'descriptor': descriptor,
                        'baseline': original, 'candidate': candidate,
                        'present_with_same_static_kind': original['found'] and candidate['found'] and original['static'] == candidate['static']})
    def sha(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'scope': 'Public member presence/descriptors/static kind used by compiled OCR SDK; not full ABI, JNI or inference execution',
            'consumer_sha256': sha(consumer), 'baseline_classes_sha256': sha(old), 'candidate_classes_sha256': sha(new),
            'consumer_classes': len(classes), 'references_checked': len(results), 'members': results,
            'missing_or_changed': [m for m in results if not m['present_with_same_static_kind']]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', required=True, type=Path)
    parser.add_argument('--old', required=True, type=Path)
    parser.add_argument('--new', required=True, type=Path)
    parser.add_argument('--javap', default='javap')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = check(args.consumer, args.old, args.new, args.javap)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'references_checked': result['references_checked'], 'missing_or_changed': len(result['missing_or_changed'])}))
    raise SystemExit(bool(result['missing_or_changed']))
