"""Inspect ZIP sizes and native ELF headers; this does not execute or certify an APK."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import zipfile


def inspect(apk, native_root="lib"):
    groups = defaultdict(lambda: {'compressed_bytes': 0, 'uncompressed_bytes': 0, 'files': 0})
    native = []
    with zipfile.ZipFile(apk) as archive, apk.open('rb') as raw:
        files = archive.infolist()
        for info in files:
            name = info.filename
            group = '/'.join(name.split('/')[:2]) if name.startswith(native_root + '/') else 'DEX' if name.endswith('.dex') else name.split('/')[0]
            groups[group]['compressed_bytes'] += info.compress_size
            groups[group]['uncompressed_bytes'] += info.file_size
            groups[group]['files'] += 1
            if not name.startswith(native_root + '/') or not name.endswith('.so'):
                continue
            with archive.open(info) as stream:
                data = stream.read(65536)
            if len(data) < 64 or data[:4] != b'\x7fELF' or data[5] != 1 or data[4] not in (1, 2):
                raise ValueError('Unsupported native ELF header: ' + name)
            bits = 64 if data[4] == 2 else 32
            if bits == 64:
                offset = struct.unpack_from('<Q', data, 32)[0]
                size, count = struct.unpack_from('<HH', data, 54)
                alignment_offset, alignment_format, minimum_size = 48, '<Q', 56
            else:
                offset = struct.unpack_from('<I', data, 28)[0]
                size, count = struct.unpack_from('<HH', data, 42)
                alignment_offset, alignment_format, minimum_size = 28, '<I', 32
            if size < minimum_size or offset + size * count > len(data):
                raise ValueError('Native program headers exceed inspection window: ' + name)
            alignments = [struct.unpack_from(alignment_format, data, offset + index * size + alignment_offset)[0]
                          for index in range(count) if struct.unpack_from('<I', data, offset + index * size)[0] == 1]
            if not alignments:
                raise ValueError('No native PT_LOAD headers: ' + name)
            machine = struct.unpack_from('<H', data, 18)[0]
            abi = name.split('/')[1]
            expected_machine = {'arm64-v8a': (64, 183), 'armeabi-v7a': (32, 40), 'x86': (32, 3), 'x86_64': (64, 62)}.get(abi)
            raw.seek(info.header_offset)
            local_header = raw.read(30)
            if len(local_header) != 30 or local_header[:4] != b'PK\x03\x04':
                raise ValueError('Invalid local ZIP header: ' + name)
            name_length, extra_length = struct.unpack_from('<HH', local_header, 26)
            start = info.header_offset + 30 + name_length + extra_length
            native.append({'path': name, 'elf_class_bits': bits, 'elf_machine': machine,
                           'abi_name_matches_elf': (bits, machine) == expected_machine if expected_machine else None,
                           'pt_load_alignments': alignments, 'elf_minimum_alignment': min(alignments),
                           'zip_data_offset_multiple_16384': start % 16384 == 0,
                           'stored_uncompressed': info.compress_type == zipfile.ZIP_STORED})
        largest = [{'path': f.filename, 'compressed_bytes': f.compress_size, 'uncompressed_bytes': f.file_size}
                   for f in sorted(files, key=lambda f: -f.compress_size)[:12]]
    with apk.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'scope': 'Static ZIP sizes, ARM ELF machine and PT_LOAD headers; not device execution, installed size or RAM',
            'apk_sha256': digest if native_root == 'lib' else None, 'apk_bytes': apk.stat().st_size if native_root == 'lib' else None,
            'artifact_sha256': digest, 'artifact_bytes': apk.stat().st_size, 'native_root': native_root,
            'groups': dict(sorted(groups.items(), key=lambda item: -item[1]['compressed_bytes'])),
            'largest_entries': largest, 'native_libraries': native,
            'arm64_elf_below_16k': [n['path'] for n in native if '/arm64-v8a/' in n['path'] and n['elf_minimum_alignment'] < 16384]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--native-root', choices=('lib', 'jni'), default='lib', help='Use jni for an AAR dependency')
    args = parser.parse_args()
    result = inspect(args.apk, args.native_root)
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')
