"""Check actual merged ARM libraries and prior C++ imports; does not execute Android/JNI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def elf(path, readelf):
    with path.open('rb') as stream:
        header = stream.read(64)
    if len(header) < 64 or header[:4] != b'\x7fELF' or header[5] != 1 or header[4] not in (1, 2):
        raise ValueError('Unsupported ELF header: ' + path.name)
    listing = subprocess.check_output(
        [readelf, '--program-headers', '--dynamic', '--dyn-syms', '--wide', str(path)], text=True,
    )
    alignments, congruent, exports, imports = [], [], set(), set()
    for line in listing.splitlines():
        fields = line.split()
        if fields and fields[0] == 'LOAD':
            alignments.append(int(fields[-1], 16))
            congruent.append(int(fields[1], 16) % 16384 == int(fields[2], 16) % 16384)
        if len(fields) < 8 or not fields[0].endswith(':') or not fields[0][:-1].isdigit():
            continue
        _, _, _, _, binding, visibility, index, name = fields[:8]
        name = name.split('@', 1)[0]
        if index == 'UND' and binding == 'GLOBAL':
            imports.add(name)
        elif index != 'UND' and binding in ('GLOBAL', 'WEAK') and visibility in ('DEFAULT', 'PROTECTED'):
            exports.add(name)
    if not alignments:
        raise ValueError('No ELF PT_LOAD headers: ' + path.name)
    return {
        'elf_class_bits': 64 if header[4] == 2 else 32,
        'elf_machine': struct.unpack_from('<H', header, 18)[0],
        'pt_load_alignments': alignments,
        'load_offset_vaddr_congruent_16k': all(congruent),
        'needed': re.findall(r'\(NEEDED\).*Shared library: \[([^\]]+)\]', listing),
    }, exports, imports


def check(merged, candidate, previous_apk, previous_manifest, readelf):
    abis = {'arm64-v8a': (64, 183), 'armeabi-v7a': (32, 40)}
    replace = {'libopencv_java4.so', 'libc++_shared.so'}
    paths = {p.relative_to(merged).as_posix(): p for p in merged.rglob('*.so')}
    baseline = {entry['path']: entry for entry in json.loads(previous_manifest.read_text())}
    errors = []
    if set(paths) != set(baseline):
        errors.append('Merged library paths differ from the baseline')
    if {name.split('/')[0] for name in paths} != set(abis):
        errors.append('Expected exactly ARM32 and ARM64')
    inspections, exports_by_path, imports_by_path = {}, {}, {}
    libraries, unchanged, expected_replacements = [], [], []
    with zipfile.ZipFile(candidate) as aar:
        for name, path in sorted(paths.items()):
            abi, filename = name.split('/')
            info, exports, imports = elf(path, readelf)
            info.update(path=name, bytes=path.stat().st_size, sha256=file_digest(path))
            info['abi_matches_elf'] = (info['elf_class_bits'], info['elf_machine']) == abis.get(abi)
            if not info['abi_matches_elf']:
                errors.append('ELF machine/class mismatch: ' + name)
            if abi == 'arm64-v8a' and min(info['pt_load_alignments']) < 16384:
                errors.append('ARM64 PT_LOAD below 16 KiB: ' + name)
            if abi == 'arm64-v8a' and not info['load_offset_vaddr_congruent_16k']:
                errors.append('ARM64 LOAD offset/address mismatch for 16 KiB: ' + name)
            if filename in replace:
                matches = info['sha256'] == digest(aar.read('jni/' + name))
                expected_replacements.append({'path': name, 'matches_official_aar': matches})
                if not matches:
                    errors.append('Merged binary differs from the official AAR: ' + name)
            else:
                matches = name in baseline and info['sha256'] == baseline[name]['sha256']
                unchanged.append({'path': name, 'unchanged': matches})
                if not matches:
                    errors.append('Unrelated native binary changed: ' + name)
            libraries.append(info)
            inspections[name], exports_by_path[name], imports_by_path[name] = info, exports, imports
    expected_paths = {abi + '/' + name for abi in abis for name in replace}
    if {entry['path'] for entry in expected_replacements} != expected_paths:
        errors.append('Missing OpenCV/C++ pair for an ARM ABI')
    cpp = []
    with zipfile.ZipFile(previous_apk) as previous, tempfile.TemporaryDirectory() as temp:
        for abi in abis:
            relative = abi + '/libc++_shared.so'
            old = Path(temp) / (abi + '.so')
            old.write_bytes(previous.read('lib/' + relative))
            _, previous_exports, _ = elf(old, readelf)
            current_exports = exports_by_path.get(relative, set())
            consumers = []
            for name, info in sorted(inspections.items()):
                if not name.startswith(abi + '/') or name == relative:
                    continue
                # Only imports previously supplied by this shared runtime are in scope.
                required = imports_by_path[name] & previous_exports
                if not required and 'libc++_shared.so' not in info['needed']:
                    continue
                missing = sorted(required - current_exports)
                consumers.append({'path': name, 'previous_cpp_imports': len(required),
                                  'required_names_sha256': digest('\n'.join(sorted(required)).encode()),
                                  'missing_symbols': missing})
                if missing:
                    errors.append('C++ imports missing from the selected runtime: ' + name)
            cpp.append({'abi': abi, 'previous_cpp_exports': len(previous_exports),
                        'selected_cpp_exports': len(current_exports), 'consumers': consumers})
    return {
        'status': 'STATIC_MERGE_CHECK_PASS' if not errors else 'STATIC_MERGE_CHECK_FAILED',
        'scope': 'Actual merged ELF headers, AAR hashes, unchanged peers and strong imports supplied by the prior C++ runtime. No Android linker namespaces/API/relocations, JNI or OCR execution.',
        'official_aar_sha256': file_digest(candidate),
        'previous_apk_sha256': file_digest(previous_apk),
        'native_libraries': libraries, 'official_replacements': expected_replacements,
        'unrelated_libraries': unchanged, 'cpp_import_compatibility': cpp,
        'total_merged_native_bytes': sum(entry['bytes'] for entry in libraries),
        'errors': errors, 'android_runtime_verified': False, 'final_apk_verified': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--merged', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--previous-apk', type=Path, required=True)
    parser.add_argument('--previous-manifest', type=Path, required=True)
    parser.add_argument('--readelf', default='llvm-readelf')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.merged, args.candidate, args.previous_apk, args.previous_manifest, args.readelf)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'libraries': len(result['native_libraries']),
                      'errors': result['errors']}))
    raise SystemExit(bool(result['errors']))
