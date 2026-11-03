"""Export verified ARM beta APKs and original fixtures; no keys or app data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REVISION = 'P20261103.1'


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
    icons = re.findall(r':(?:icon|roundIcon)\([^)]*\)=@(0x[0-9a-fA-F]+)', manifest)
    if not resource or len(icons) != 2 or any(icon != resource.group(1) for icon in icons):
        raise ValueError('Compiled application icon and roundIcon must use the Polaris launcher')
    for name in ['ic_polaris_foreground', 'ic_polaris_monochrome', 'ic_polaris_logo', 'ic_polaris_splash']:
        if not re.search(r'drawable/' + name + r'\b', resources):
            raise ValueError('Missing compiled Polaris branding resource: ' + name)
    return {'label': 'Polaris', 'launcher': 'ic_polaris_launcher', 'compiled_resources_verified': True}


def verify_branding(apk, apksigner):
    tool = apksigner.parent / ('aapt2.exe' if os.name == 'nt' else 'aapt2')
    def dump(*arguments):
        return subprocess.run([str(tool), 'dump', *arguments, str(apk)], check=True,
                              capture_output=True, text=True, encoding='utf-8').stdout
    return validate_branding(dump('badging'), dump('resources', '--no-values'),
                             dump('xmltree', '--file', 'AndroidManifest.xml'))


def package(apks, output, comparison, apksigner):
    if output.exists():
        raise ValueError('Choose a new beta output directory; existing files are never replaced')
    evidence = json.loads(comparison.read_text())
    if evidence.get('status') != 'NO_NEW_UNIT_REGRESSIONS':
        raise ValueError('A completed unit regression comparison is required')
    metadata = json.loads((apks / 'output-metadata.json').read_text())
    if metadata.get('variantName') != 'debug':
        raise ValueError('Expected the tested debug candidate')
    selected = []
    signer_hash = None
    for abi in ['arm64-v8a', 'armeabi-v7a']:
        entry = next(e for e in metadata['elements'] if any(
            f.get('filterType') == 'ABI' and f.get('value') == abi for f in e['filters']))
        if entry['versionCode'] != 109 or entry['versionName'] != '0.1.0-beta.8':
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
        with zipfile.ZipFile(apk) as archive:
            if not any(REVISION.encode() in archive.read(n) for n in archive.namelist() if n.endswith('.dex')):
                raise ValueError('Beta revision missing from APK')
        verify_branding(apk, apksigner)
        selected.append((abi, apk))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.polaris-beta-', dir=output.parent))
    try:
        artifacts = []
        for abi, apk in selected:
            name = f'Polaris-0.1.0-beta.8-{abi}.apk'
            shutil.copy2(apk, temporary / name)
            artifacts.append({'abi': abi, 'file': name, 'bytes': apk.stat().st_size, 'sha256': sha256(apk)})
        shutil.copy2(ROOT / 'integration/internal-beta/README.md', temporary / 'COMECE_AQUI.md')
        shutil.copytree(ROOT / 'integration/internal-beta/language-fixtures', temporary / 'testes/idiomas')
        shutil.copytree(ROOT / 'integration/document-reader/fixtures', temporary / 'testes/documentos')
        shutil.copytree(ROOT / 'integration/internal-beta/long-strip-fixture', temporary / 'testes/faixa-longa')
        manifest = {'status': 'INTERNAL_BETA_CANDIDATE', 'version': '0.1.0-beta.8', 'version_code': 109,
                    'revision': REVISION, 'minimum_android_api': 26,
                    'application_id': metadata['applicationId'], 'signer_sha256': signer_hash,
                    'artifacts': artifacts, 'unit_comparison': evidence,
                    'display_name': 'Polaris', 'branding_verified': True,
                    'physical_device_acceptance': 'PENDING', 'cjk_ocr_quality': 'PENDING'}
        (temporary / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        (temporary / 'SHA256SUMS.txt').write_text(''.join(
            f"{a['sha256']}  {a['file']}\n" for a in artifacts), encoding='utf-8')
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
    result = package(args.apks, args.output, args.comparison, signer)
    print(f"INTERNAL_BETA_CANDIDATE_EXPORTED: {args.output} ({len(result['artifacts'])} ARM APKs)")


if __name__ == '__main__':
    main()
