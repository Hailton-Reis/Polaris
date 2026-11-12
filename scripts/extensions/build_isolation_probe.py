"""Build an independent Android isolation probe. Never installs it or uses a distribution key."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def build(output, sdk, java_home, gradle_home):
    if output.exists() or any((p / '.git').exists() for p in [output.resolve(), *output.resolve().parents]):
        raise ValueError('Choose a new output directory outside version-controlled checkouts')
    sources = ROOT / 'integration/extension-isolation/20261106/probe'
    android = sdk / 'platforms/android-37.0/android.jar'
    toolchain = sdk / 'build-tools/37.0.0'
    def cached(group, artifact, version):
        found = list((gradle_home / 'caches/modules-2/files-2.1' / group / artifact / version).rglob('*.jar'))
        if len(found) != 1:
            raise ValueError('Expected one cached artifact: ' + artifact)
        return found[0]
    dexer = cached('com.android.tools.build', 'builder', '9.3.1')
    stdlib = cached('org.jetbrains.kotlin', 'kotlin-stdlib', '2.4.10')
    env = dict(os.environ, JAVA_HOME=str(java_home))
    def run(*args):
        subprocess.run([str(x) for x in args], check=True, env=env)
    output.mkdir(parents=True)
    for name in ['classes', 'dex']:
        (output / name).mkdir()
    for path in sources.iterdir():
        shutil.copy2(path, output / path.name)
    run(java_home / 'bin/javac', '-source', '8', '-target', '8', '-classpath', android,
        '-d', output / 'classes', *list(output.glob('*.java')))
    runner = output / 'runner.jar'
    with zipfile.ZipFile(runner, 'w') as archive:
        for path in (output / 'classes').rglob('*.class'):
            archive.write(path, path.relative_to(output / 'classes'))
    run(java_home / 'bin/java', '-Xmx256m', '-cp', os.pathsep.join(map(str, [dexer, stdlib])),
        'com.android.tools.r8.D8', '--min-api', '26', '--lib', android, '--output', output / 'dex', runner)
    unsigned = output / 'unsigned.apk'
    run(toolchain / 'aapt2', 'link', '--manifest', output / 'AndroidManifest.xml', '-I', android, '-o', unsigned)
    with zipfile.ZipFile(unsigned, 'a') as archive:
        for path in (output / 'dex').glob('*.dex'):
            archive.write(path, path.name)
    key = output / 'synthetic-probe-only.p12'
    run(java_home / 'bin/keytool', '-genkeypair', '-keystore', key, '-storetype', 'PKCS12',
        '-storepass', 'synthetic-test-only', '-keypass', 'synthetic-test-only', '-alias', 'synthetic',
        '-keyalg', 'RSA', '-keysize', '2048', '-dname', 'CN=Polaris isolated component test only', '-validity', '3650')
    run(toolchain / 'apksigner', 'sign', '--ks', key, '--ks-pass', 'pass:synthetic-test-only',
        '--key-pass', 'pass:synthetic-test-only', '--out', output / 'probe.apk', unsigned)
    provenance = dict(
        scope='Android isolated-process component proof; no integrated third-party extension executor or reader acceptance.',
        sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources.iterdir()},
        apk_sha256=hashlib.sha256((output / 'probe.apk').read_bytes()).hexdigest(),
        apk_bytes=(output / 'probe.apk').stat().st_size,
        dexer_sha256=hashlib.sha256(dexer.read_bytes()).hexdigest(),
    )
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('ISOLATION_PROBE_BUILT', output / 'probe.apk')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['output', 'sdk', 'java-home', 'gradle-home']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.sdk, args.java_home, args.gradle_home)
