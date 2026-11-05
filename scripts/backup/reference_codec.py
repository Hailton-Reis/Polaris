#!/usr/bin/env python3
"""Generate synthetic archives with pinned upstream DTOs; verify Polaris exports with those readers.

Requires Kotlin's real serialization compiler plugin and kotlinx serialization runtime jars.
Does not compile Android/database mapping helpers or exercise app UI/database restore.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'integration/backup-interop/20261104'
DECLARATION = re.compile(r'@Serializable\s+(?:(?:data|sealed)\s+)?class\s+(\w+)')


def declarations(source):
    result = []
    for match in DECLARATION.finditer(source):
        pos = match.end()
        while pos < len(source) and source[pos].isspace():
            pos += 1
        end = pos
        if source[pos:pos + 1] == '(':
            level, state, index = 0, 'code', pos
            while index < len(source):
                char, pair = source[index], source[index:index + 2]
                if state == 'line':
                    if char == '\n':
                        state = 'code'
                elif state == 'block':
                    if pair == '*/':
                        state = 'code'
                        index += 1
                elif state == 'string':
                    if char == '\\':
                        index += 1
                    elif char == '"':
                        state = 'code'
                else:
                    if pair == '//':
                        state = 'line'
                        index += 1
                    elif pair == '/*':
                        state = 'block'
                        index += 1
                    elif char == '"':
                        state = 'string'
                    elif char == '(':
                        level += 1
                    elif char == ')':
                        level -= 1
                        if level == 0:
                            end = index + 1
                            break
                index += 1
            if end <= pos:
                raise ValueError('Unclosed constructor: ' + match.group(1))
        else:
            end = match.end()
        result.append(source[match.start():end])
    return '\n\n'.join(result) + '\n'


def verify_sources():
    for item in json.loads((FIXTURES / 'provenance.json').read_text()):
        data = (FIXTURES / 'reference' / item['reference'] / item['file']).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != item['git_blob_sha'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Pinned reference changed: ' + item['reference'] + '/' + item['file'])


def generate(label, args, classpath):
    folder = args.output / 'generated' / label
    folder.mkdir(parents=True, exist_ok=True)
    original = FIXTURES / 'reference' / label
    for file in sorted(original.glob('Backup*.kt')):
        source = file.read_text()
        # Preserve sealed subtype inheritance and original serial names verbatim.
        body = source[source.index('@Serializable'):] if file.name == 'BackupPreference.kt' else declarations(source)
        if not body.strip():
            raise ValueError('Missing DTO: ' + str(file))
        prefix = ('package eu.kanade.tachiyomi.data.backup.models\n'
                  'import kotlinx.serialization.Serializable\n'
                  'import kotlinx.serialization.protobuf.ProtoNumber\n'
                  'import eu.kanade.tachiyomi.source.model.UpdateStrategy\n')
        if label == 'mihon':
            prefix += 'import mihon.core.common.extensions.JsonObjectEmptyBytes\n'
        (folder / file.name).write_text(prefix + body)
    shutil.copy2(original / 'UpdateStrategy.kt', folder / 'UpdateStrategy.kt')
    if label == 'mihon':
        constant = re.search(r'^val JsonObjectEmptyBytes = .*$', (original / 'JsonObject.kt').read_text(), re.M).group()
        (folder / 'JsonObject.kt').write_text('package mihon.core.common.extensions\n' + constant + '\n')
    shutil.copy2(FIXTURES / 'harness' / (label + '-extras.kt'), folder / 'Extras.kt')
    jars = args.kotlinc.parent.parent / 'lib'
    jar = args.output / (label + '.jar')
    subprocess.run([str(args.kotlinc), *[str(f) for f in sorted(folder.glob('*.kt'))],
                    str(FIXTURES / 'harness/ReferenceCodec.kt'), '-cp', classpath,
                    '-Xplugin=' + str(jars / 'kotlinx-serialization-compiler-plugin.jar'),
                    '-opt-in=kotlinx.serialization.ExperimentalSerializationApi', '-include-runtime', '-d', str(jar)], check=True)
    target = args.output / 'fixtures'
    target.mkdir(exist_ok=True)
    subprocess.run([str(args.java), '-cp', str(jar) + os.pathsep + classpath, 'ReferenceCodecKt', 'generate', str(target / label)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--kotlinc', type=Path, required=True)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--serialization-dir', type=Path, required=True)
    parser.add_argument('--verify-exchange', type=Path)
    args = parser.parse_args()
    verify_sources()
    classpath = os.pathsep.join(str(f.resolve()) for f in sorted(args.serialization_dir.glob('*.jar')))
    if not classpath:
        parser.error('Serialization runtime jars are required')
    args.output.mkdir(parents=True, exist_ok=True)
    for label in ['mihon', 'tachiyomi']:
        if args.verify_exchange:
            jar = args.output / (label + '.jar')
            if not jar.is_file():
                parser.error('Run generation before verifying the exchange')
            subprocess.run([str(args.java), '-cp', str(jar) + os.pathsep + classpath, 'ReferenceCodecKt',
                            'verify', str(args.verify_exchange / (label + '-polaris.tachibk'))], check=True)
        else:
            generate(label, args, classpath)


if __name__ == '__main__':
    main()
