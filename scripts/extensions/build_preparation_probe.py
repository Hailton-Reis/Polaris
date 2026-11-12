"""Build a small self-targeted Android probe from actual reader class files; never install or publish it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def build(android_build, output, sdk, java_home, gradle_home):
    if any((parent / '.git').exists() for parent in [output.resolve(), *output.resolve().parents]):
        raise ValueError('Keep generated probe APKs and their test key outside version-controlled checkouts')
    if output.exists():
        raise ValueError('Choose a new output directory; existing files are preserved')
    classes = android_build / 'app/build/intermediates/built_in_kotlinc/debug/compileDebugKotlin/classes'
    selected = []
    for name in ['PrivateExtensionFiles', 'PrivateExtensionSignature']:
        found = list((classes / 'eu/kanade/tachiyomi/extension/util').glob(name + '*.class'))
        if not found:
            raise ValueError('Compile the reader first: missing ' + name)
        selected.extend(found)
    def cached(group, artifact, version):
        jars = list((gradle_home / 'caches/modules-2/files-2.1' / group / artifact / version).rglob('*.jar'))
        if len(jars) != 1:
            raise ValueError('Expected one cached artifact: ' + artifact + ':' + version)
        return jars[0]
    apksig = cached('com.android.tools.build', 'apksig', '9.3.1')
    dexer = cached('com.android.tools.build', 'builder', '9.3.1')
    stdlib = cached('org.jetbrains.kotlin', 'kotlin-stdlib', '2.4.10')
    android_jar = sdk / 'platforms/android-37.0/android.jar'
    toolchain = sdk / 'build-tools/37.0.0'
    env = dict(os.environ, JAVA_HOME=str(java_home))
    def run(*args):
        subprocess.run([str(x) for x in args], check=True, env=env)
    output.mkdir(parents=True)
    for name in ['classes', 'dex', 'assets']:
        (output / name).mkdir()
    for name in ['Probe.java', 'AndroidManifest.xml']:
        shutil.copy2(ROOT / 'integration/source-preparation/20261104/android-probe' / name, output / name)
    for name in ['signed.apk', 'tampered.apk']:
        shutil.copy2(android_build / 'app/src/test/resources/extension-preparation' / name, output / 'assets' / name)
    hashes = {str(f.relative_to(classes)): hashlib.sha256(f.read_bytes()).hexdigest() for f in selected}
    helpers = output / 'production-helpers.jar'
    with zipfile.ZipFile(helpers, 'w') as archive:
        for path in selected:
            archive.write(path, path.relative_to(classes))
    run(java_home / 'bin/javac', '-source', '8', '-target', '8', '-classpath',
        os.pathsep.join(map(str, [android_jar, helpers, apksig, stdlib])), '-d', output / 'classes', output / 'Probe.java')
    runner = output / 'runner.jar'
    with zipfile.ZipFile(runner, 'w') as archive:
        for path in (output / 'classes').rglob('*.class'):
            archive.write(path, path.relative_to(output / 'classes'))
    run(java_home / 'bin/java', '-Xmx384m', '-cp', os.pathsep.join(map(str, [dexer, stdlib])),
        'com.android.tools.r8.D8', '--min-api', '26', '--lib', android_jar, '--output', output / 'dex',
        runner, helpers, apksig, stdlib)
    unsigned = output / 'unsigned.apk'
    run(toolchain / 'aapt2', 'link', '--manifest', output / 'AndroidManifest.xml', '-I', android_jar,
        '-A', output / 'assets', '-o', unsigned)
    with zipfile.ZipFile(unsigned, 'a') as archive:
        for path in (output / 'dex').glob('*.dex'):
            archive.write(path, path.name)
    # Generated local test key; never use a reader/distribution signing key for this probe.
    key = output / 'synthetic-probe-only.p12'
    run(java_home / 'bin/keytool', '-genkeypair', '-keystore', key, '-storetype', 'PKCS12',
        '-storepass', 'synthetic-test-only', '-keypass', 'synthetic-test-only', '-alias', 'synthetic',
        '-keyalg', 'RSA', '-keysize', '2048', '-dname', 'CN=Polaris component test only', '-validity', '3650')
    run(toolchain / 'apksigner', 'sign', '--ks', key, '--ks-pass', 'pass:synthetic-test-only',
        '--key-pass', 'pass:synthetic-test-only', '--out', output / 'probe.apk', unsigned)
    (output / 'provenance.json').write_text(json.dumps({
        'scope': 'Actual compiled signature/file helpers only; no full-reader, wizard UI, real-extension or database acceptance.',
        'classes': hashes, 'apksig_sha256': hashlib.sha256(apksig.read_bytes()).hexdigest(),
        'dexer_sha256': hashlib.sha256(dexer.read_bytes()).hexdigest(),
        'apk_sha256': hashlib.sha256((output / 'probe.apk').read_bytes()).hexdigest(),
        'apk_bytes': (output / 'probe.apk').stat().st_size,
    }, indent=2) + '\n')
    print('PROBE_BUILT', output / 'probe.apk')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--android-build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--gradle-home', type=Path, required=True)
    args = parser.parse_args()
    build(args.android_build, args.output, args.sdk, args.java_home, args.gradle_home)
