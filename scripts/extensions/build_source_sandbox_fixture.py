#!/usr/bin/env python3
"""Compile the synthetic current Source API fixture; no signing key or real provider is used."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'integration/reading-continuity/20261106/fixture/FixtureSource.kt'
GROUPS = [
    'org.jetbrains.kotlin/kotlin-stdlib', 'com.squareup.okhttp3/okhttp-jvm',
    'com.squareup.okhttp3/okhttp', 'com.squareup.okio/okio-jvm', 'io.reactivex/rxjava',
    'org.jetbrains.kotlinx/kotlinx-serialization-json-jvm',
    'org.jetbrains.kotlinx/kotlinx-serialization-core-jvm',
    'org.jetbrains.kotlinx/kotlinx-coroutines-core-jvm',
    'uy.kohesive.injekt/injekt-api', 'uy.kohesive.injekt/injekt-core',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('android-root', 'output', 'sdk', 'java-home', 'gradle-home', 'kotlinc'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--source', type=Path, default=SOURCE, help='Synthetic fixture Kotlin source')
    parser.add_argument('--android-jar', type=Path, help='Installed platform android.jar override')
    parser.add_argument('--write-asset', action='store_true',
                        help='Replace the synthetic Android test asset in android-root explicitly')
    args = parser.parse_args()
    output = args.output.resolve()
    android_root = args.android_root.resolve()
    if output == android_root or android_root in output.parents or output == ROOT or ROOT in output.parents:
        parser.error('Use an output outside the source checkouts')
    output.mkdir(parents=True, exist_ok=False)
    cache = args.gradle_home / 'caches/modules-2/files-2.1'
    android = args.android_jar or args.sdk / 'platforms/android-37.0/android.jar'
    if not android.is_file():
        parser.error('Installed android.jar is missing; use --android-jar for its actual location')
    java = args.java_home / 'bin/java'
    classpath = [android,
                 android_root / 'source-api/build/intermediates/compile_library_classes_jar/debug/bundleLibCompileToJarDebug/classes.jar',
                 android_root / 'core/common/build/intermediates/compile_library_classes_jar/debug/bundleLibCompileToJarDebug/classes.jar']
    for group in GROUPS:
        classpath += sorted((cache / group).rglob('*.jar'))
    # Preference schemas use AndroidX classes in the target app; no dependency is bundled in the fixture.
    preference_aar = next((cache / 'androidx.preference/preference').rglob('*.aar'))
    with zipfile.ZipFile(preference_aar) as archive:
        dependency = output / 'preference-classes.jar'
        dependency.write_bytes(archive.read('classes.jar'))
    classpath.append(dependency)
    compiler_args = output / 'compiler.args'
    # Kotlin compiler argfile quoting is independent of shell quoting.
    def quoted(value):
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'
    compiler_args.write_text('\n'.join(map(quoted, [
        '-jvm-target', '17', '-classpath', os.pathsep.join(map(str, classpath)),
        '-d', output / 'fixture.jar', args.source.resolve(),
    ])) + '\n')
    subprocess.run([str(args.kotlinc), '@' + str(compiler_args)], check=True,
                   env=dict(os.environ, JAVA_HOME=str(args.java_home)))
    dexer = next(cache.glob('com.android.tools.build/builder/9.3.1/*/builder-9.3.1.jar'))
    stdlib = args.kotlinc.parent.parent / 'lib/kotlin-stdlib.jar'
    dex_dir = output / 'dex'
    dex_dir.mkdir()
    subprocess.run([str(java), '-Xmx256m', '-cp', str(dexer) + os.pathsep + str(stdlib),
                    'com.android.tools.r8.D8', '--min-api', '26', '--lib', str(android),
                    '--output', str(dex_dir), str(output / 'fixture.jar')], check=True)
    apk = output / 'fixture.apk'
    with zipfile.ZipFile(apk, 'w') as archive:
        for dex in sorted(dex_dir.glob('*.dex')):
            archive.writestr(zipfile.ZipInfo(dex.name, date_time=(2026, 11, 6, 0, 0, 0)), dex.read_bytes())
    if args.write_asset:
        asset = android_root / 'app/src/androidTest/assets/polaris-sandbox/fixture.apk'
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(apk.read_bytes())
    provenance = {
        'scope': 'Synthetic current-Source-API implementation in a DEX zip; not a signed third-party extension or full-reader acceptance test.',
        'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
        'bytes': apk.stat().st_size,
        'dex_sha256': hashlib.sha256((dex_dir / 'classes.dex').read_bytes()).hexdigest(),
    }
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(provenance))


if __name__ == '__main__':
    main()
