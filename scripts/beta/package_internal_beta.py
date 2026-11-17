"""Export a verified universal ARM beta APK and original fixtures; no keys or app data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
REVISION = 'P20261117.3'
VERSION = '0.1.0-beta.11'
VERSION_CODE = 112
ARM_ABIS = ['arm64-v8a', 'armeabi-v7a']
APPLICATION_ID = 'app.mihon.tachiyomiat.dev'
DEBUG_COMPONENTS = (
    'eu.kanade.tachiyomi.polaris.PolarisPersonalizationTestActivity',
    'eu.kanade.tachiyomi.polaris.PolarisWorkSearchTestActivity',
    'eu.kanade.tachiyomi.polaris.Spike001DebugActivity',
    'eu.kanade.tachiyomi.polaris.TranslationCaptureReceiver',
    'eu.kanade.translation.presentation.TranslationSurfaceTestActivity',
    'eu.kanade.translation.detection.DbnetCleanupMaskTestActivity',
    'eu.kanade.translation.detection.DbnetCrashTestService',
)


def dex_class_descriptors(data):
    """Read class definitions, not incidental strings, from a standard Android DEX."""
    if (len(data) < 112 or data[:4] != b'dex\n' or data[7] != 0
            or data[4:7] not in (b'035', b'037', b'038', b'039', b'040')):
        raise ValueError('Invalid or unsupported DEX header')
    if (struct.unpack_from('<I', data, 32)[0] != len(data)
            or struct.unpack_from('<I', data, 36)[0] != 112
            or struct.unpack_from('<I', data, 40)[0] != 0x12345678
            or data[12:32] != hashlib.sha1(data[32:]).digest()
            or struct.unpack_from('<I', data, 8)[0] != zlib.adler32(data[12:]) & 0xffffffff):
        raise ValueError('Invalid DEX size, encoding or checksum')
    def table(position, width):
        count, offset = struct.unpack_from('<II', data, position)
        if count and (offset < 112 or offset > len(data) or count > (len(data) - offset) // width):
            raise ValueError('DEX table exceeds file bounds')
        return count, offset
    strings, string_offset = table(56, 4)
    types, type_offset = table(64, 4)
    classes, class_offset = table(96, 32)
    result = set()
    for index in range(classes):
        type_index = struct.unpack_from('<I', data, class_offset + index * 32)[0]
        if type_index >= types:
            raise ValueError('Invalid DEX class type')
        string_index = struct.unpack_from('<I', data, type_offset + type_index * 4)[0]
        if string_index >= strings:
            raise ValueError('Invalid DEX class name')
        offset = struct.unpack_from('<I', data, string_offset + string_index * 4)[0]
        for length in range(5):
            if offset >= len(data):
                raise ValueError('Truncated DEX string')
            byte = data[offset]
            offset += 1
            if byte < 128:
                break
        else:
            raise ValueError('Invalid DEX string length')
        end = data.find(b'\0', offset, min(len(data), offset + 4096))
        descriptor = data[offset:end] if end >= 0 else b''
        if not descriptor.startswith(b'L') or not descriptor.endswith(b';') or descriptor in result:
            raise ValueError('Invalid or duplicate DEX class descriptor')
        result.add(descriptor)
    return result


def verify_production_classes(archive):
    classes = set()
    dex_files = [name for name in archive.namelist() if re.fullmatch(r'classes(?:[2-9]|[1-9][0-9]+)?\.dex', name)]
    if not dex_files:
        raise ValueError('APK has no standard DEX files')
    forbidden = {('L' + name.replace('.', '/') + ';').encode() for name in DEBUG_COMPONENTS}
    for name in dex_files:
        found = dex_class_descriptors(archive.read(name))
        if classes & found:
            raise ValueError('Duplicate class definitions across DEX files')
        if any(value in forbidden or value.startswith((b'Leu/kanade/tachiyomi/extension/sandbox/',
                b'Lorg/sqlite/', b'Lapp/cash/sqldelight/driver/jdbc/', b'Lorg/junit/', b'Landroidx/test/'))
                for value in found):
            raise ValueError('Experimental sandbox, debug harness or JVM test classes in production APK')
        classes.update(found)
    return {'dex_files': len(dex_files), 'class_definitions': len(classes), 'forbidden_classes': []}


def validate_compiled_build(badging, manifest, application_id):
    packages = re.findall(r'^package:(.*)$', badging, re.MULTILINE)
    if len(packages) != 1:
        raise ValueError('Expected one compiled package identity')
    values = dict(re.findall(r"(\w+)='([^']*)'", packages[0]))
    sdk = re.search(r"^(?:minSdkVersion|sdkVersion):'(\d+)'$", badging, re.MULTILINE)
    if (values.get('name') != application_id or application_id != APPLICATION_ID
            or values.get('versionCode') != str(VERSION_CODE) or values.get('versionName') != VERSION
            or not sdk or int(sdk.group(1)) != 26):
        raise ValueError('Compiled APK identity/version/minimum SDK differs from the beta contract')
    application = re.search(r'(?m)^[ \t]*E: application(?:[ \t]+[^\n]*)?\n', manifest)
    if not application:
        raise ValueError('Compiled manifest has no application element')
    attributes = re.split(r'(?m)^[ \t]*E:', manifest[application.end():], maxsplit=1)[0]
    def flag(text, name):
        matches = re.findall(r':' + name + r'\([^)]*\)=([^\n]+)', text)
        if not matches:
            return False
        if len(matches) != 1:
            raise ValueError('Ambiguous compiled application flag')
        match = re.fullmatch(r'(?:\(type 0x12\))?\s*(0x[0-9a-fA-F]+|true|false)', matches[0].strip())
        if not match:
            raise ValueError('Unverifiable compiled application flag')
        return match.group(1) == 'true' or (match.group(1) != 'false' and int(match.group(1), 16) != 0)
    profileable = re.findall(r'(?m)^[ \t]*E: profileable[^\n]*\n((?:[ \t]*A:[^\n]*\n?)*)', manifest)
    if (flag(attributes, 'debuggable') or flag(attributes, 'testOnly')
            or any(flag(text, 'shell') for text in profileable)
            or re.search(r'^application-debuggable\b', badging, re.MULTILINE)
            or re.search(r'(?m)^[ \t]*E: instrumentation\b', manifest)
            or any(name.rsplit('.', 1)[-1] in manifest for name in DEBUG_COMPONENTS)
            or 'extension.sandbox.' in manifest):
        raise ValueError('Debug, test, profileable or sandbox components in production beta')
    return {'variant': 'beta', 'debuggable': False, 'test_only': False,
            'profileable_by_shell': False, 'compiled_identity_verified': True}


def verify_universal_architectures(archive):
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError('Duplicate entries in universal APK')
    libraries = {abi: {name.split('/')[-1] for name in names if name.startswith(f'lib/{abi}/')}
                 for abi in ARM_ABIS}
    all_abis = {name.split('/')[1] for name in names if name.startswith('lib/') and name.endswith('.so')}
    if all_abis != set(ARM_ABIS):
        raise ValueError('Universal phone APK must contain exactly ARM32 and ARM64 native libraries')
    required = {'libimagedecoder.so', 'libarchive-jni.so', 'libsqliteJni.so',
                'libmlkit_google_ocr_pipeline.so', 'libtranslate_jni.so', 'liblanguage_id_l2c_jni.so',
                'libonnxruntime.so', 'libonnxruntime4j_jni.so', 'libopencv_java4.so'}
    if any(not required <= provided for provided in libraries.values()):
        raise ValueError('Missing required reader/OCR libraries for an ARM architecture')
    return libraries


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def signer_digest(output):
    # build-tools 36 prints "Signer #1"; 37 may print "V2 Signer".
    digests = set(re.findall(r'certificate SHA-256 digest:\s*([0-9a-fA-F]{64})', output))
    if len(digests) != 1:
        raise ValueError('Expected exactly one verified beta signing certificate')
    return digests.pop().lower()


def validate_branding(badging, resources, manifest):
    labels = re.findall(r"^application-label(?:-[^:]+)?:'([^']*)'$", badging, re.MULTILINE)
    if not labels or any(label != 'Polaris' for label in labels):
        raise ValueError('Compiled APK label must be Polaris in every locale')
    resource = re.search(r'resource\s+(0x[0-9a-fA-F]+)\s+(?:\S+:)?mipmap/ic_polaris_launcher\b', resources)
    application = re.search(r'(?m)^[ \t]*E: application(?:[ \t]+[^\n]*)?\n', manifest)
    if not application:
        raise ValueError('Compiled manifest has no application element')
    # aapt2 emits attributes before child elements. Reward launcher aliases have
    # their own icons; only the application's direct attributes establish these defaults.
    attributes = re.split(r'(?m)^[ \t]*E:', manifest[application.end():], maxsplit=1)[0]
    icons = re.findall(r':(?:icon|roundIcon)\([^)]*\)=@(0x[0-9a-fA-F]+)', attributes)
    if not resource or len(icons) != 2 or any(icon != resource.group(1) for icon in icons):
        raise ValueError('Compiled application icon and roundIcon must use the Polaris launcher')
    for name in ['ic_polaris_foreground', 'ic_polaris_monochrome', 'ic_polaris_logo', 'ic_polaris_splash']:
        if not re.search(r'drawable/' + name + r'\b', resources):
            raise ValueError('Missing compiled Polaris branding resource: ' + name)
    return {'label': 'Polaris', 'launcher': 'ic_polaris_launcher', 'compiled_resources_verified': True}


def verify_branding(apk, apksigner, application_id=None):
    tool = apksigner.parent / ('aapt2.exe' if os.name == 'nt' else 'aapt2')
    def dump(*arguments):
        return subprocess.run([str(tool), 'dump', *arguments, str(apk)], check=True,
                              capture_output=True, text=True, encoding='utf-8').stdout
    badging = dump('badging')
    manifest = dump('xmltree', '--file', 'AndroidManifest.xml')
    branding = validate_branding(badging, dump('resources', '--no-values'), manifest)
    if application_id is not None:
        branding['build_safety'] = validate_compiled_build(badging, manifest, application_id)
    return branding


def validate_update_identity(application_id, signer, previous):
    previous_id = previous.get('application_id')
    previous_signer = previous.get('signer_sha256')
    if not isinstance(previous_id, str) or not previous_id:
        raise ValueError('Previous manifest has no valid application ID')
    if not isinstance(previous_signer, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', previous_signer):
        raise ValueError('Previous manifest has no valid signing certificate')
    if application_id != previous_id:
        raise ValueError('Application ID differs from the previous installation')
    if signer.lower() != previous_signer.lower():
        raise ValueError('Signing certificate differs from the previous installation; do not uninstall to bypass this')
    previous_code = previous.get('version_code')
    if type(previous_code) is not int or not 0 < previous_code < VERSION_CODE:
        raise ValueError('Previous version code must be a positive integer below this beta')
    return {'status': 'SAME_ID_AND_SIGNER', 'previous_version': previous.get('version')}


def package(apks, output, comparison, apksigner, previous_manifest=None):
    if output.exists():
        raise ValueError('Choose a new beta output directory; existing files are never replaced')
    evidence = json.loads(comparison.read_text())
    if evidence.get('status') != 'NO_NEW_UNIT_REGRESSIONS':
        raise ValueError('A completed unit regression comparison is required')
    metadata = json.loads((apks / 'output-metadata.json').read_text())
    if metadata.get('variantName') != 'beta':
        raise ValueError('Expected the non-debug beta candidate')
    if previous_manifest is None:
        raise ValueError('Previous manifest is required to verify the installed update identity')
    previous = None
    compatibility = {'status': 'NOT_CHECKED'}
    if previous_manifest is not None:
        if previous_manifest.stat().st_size > 64 * 1024:
            raise ValueError('Previous manifest exceeds the update metadata limit')
        previous = json.loads(previous_manifest.read_text())
        if not isinstance(previous, dict):
            raise ValueError('Previous manifest must be an object')
    selected = []
    signer_hash = None
    entries = [e for e in metadata['elements'] if not e.get('filters')]
    if len(entries) != 1:
        raise ValueError('Expected exactly one universal APK in tested output metadata')
    for entry in entries:
        if entry['versionCode'] != VERSION_CODE or entry['versionName'] != VERSION:
            raise ValueError('Stale beta APK version metadata')
        name = entry['outputFile']
        if Path(name).name != name:
            raise ValueError('Unsafe APK filename')
        apk = apks / name
        result = subprocess.run([str(apksigner), 'verify', '--print-certs', str(apk)],
                                check=True, capture_output=True, text=True)
        cert = signer_digest(result.stdout)
        if signer_hash is not None and cert != signer_hash:
            raise ValueError('Beta APKs must use the same signing certificate')
        signer_hash = cert
        if previous is not None:
            compatibility = validate_update_identity(metadata['applicationId'], cert, previous)
        with zipfile.ZipFile(apk) as archive:
            if not any(REVISION.encode() in archive.read(n) for n in archive.namelist() if n.endswith('.dex')):
                raise ValueError('Beta revision missing from APK')
            verify_universal_architectures(archive)
            production_classes = verify_production_classes(archive)
        branding = verify_branding(apk, apksigner, metadata['applicationId'])
        selected.append(apk)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.polaris-beta-', dir=output.parent))
    try:
        artifacts = []
        for apk in selected:
            name = f'Polaris-{VERSION}-universal.apk'
            shutil.copy2(apk, temporary / name)
            digest = sha256(apk)
            # Older Polaris updaters select an exact ABI descriptor. Both entries deliberately
            # refer to the SAME asset; users download and install one APK, never two copies.
            artifacts.extend({'abi': abi, 'file': name, 'bytes': apk.stat().st_size, 'sha256': digest}
                             for abi in ARM_ABIS)
        shutil.copy2(ROOT / 'docs/COMECE_AQUI_BETA11.md', temporary / 'COMECE_AQUI.md')
        shutil.copy2(ROOT / 'docs/EXTENSOES_BETA11.md', temporary / 'ISOLAMENTO_DE_EXTENSOES.md')
        shutil.copytree(ROOT / 'integration/internal-beta/language-fixtures', temporary / 'testes/idiomas')
        shutil.copytree(ROOT / 'integration/document-reader/fixtures', temporary / 'testes/documentos')
        shutil.copytree(ROOT / 'integration/internal-beta/long-strip-fixture', temporary / 'testes/faixa-longa')
        manifest = {'status': 'INTERNAL_BETA_CANDIDATE', 'version': VERSION, 'version_code': VERSION_CODE,
                    'revision': REVISION, 'minimum_android_api': 26,
                    'application_id': metadata['applicationId'], 'signer_sha256': signer_hash,
                    'artifacts': artifacts, 'unit_comparison': evidence,
                    'display_name': 'Polaris', 'branding_verified': True,
                    'physical_device_acceptance': 'PENDING', 'cjk_ocr_quality': 'PENDING',
                    'distribution': 'universal-arm', 'apk_files': 1,
                    'update_compatibility': compatibility}
        manifest['build_safety'] = branding['build_safety']
        manifest['production_classes'] = production_classes
        (temporary / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        (temporary / 'SHA256SUMS.txt').write_text(''.join(
            f"{a['sha256']}  {a['file']}\n" for a in {a['file']: a for a in artifacts}.values()), encoding='utf-8')
        temporary.rename(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apks', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--apksigner', type=Path)
    parser.add_argument('--previous-manifest', type=Path, required=True,
                        help='Require the same application ID and signing certificate as this prior release')
    args = parser.parse_args()
    signer = args.apksigner
    if signer is None:
        sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if not sdk:
            parser.error('Set ANDROID_HOME or pass --apksigner')
        tool = 'apksigner.bat' if os.name == 'nt' else 'apksigner'
        candidates = list((Path(sdk) / 'build-tools').glob(f'*/{tool}'))
        if not candidates:
            parser.error('Android build-tools apksigner is missing')
        signer = sorted(candidates, key=lambda p: tuple(int(x) for x in re.findall(r'\d+', p.parent.name)))[-1]
    result = package(args.apks, args.output, args.comparison, signer, args.previous_manifest)
    print(f"INTERNAL_BETA_CANDIDATE_EXPORTED: {args.output} (one universal ARM32/ARM64 APK)")


if __name__ == '__main__':
    main()
