#!/usr/bin/env python3
"""Compile production session, space and backup safety policies and their JVM tests, without an Android runtime.

Supply a Gradle lib directory containing Kotlin compiler/stdlib/serialization and a dependency
folder with okhttp-jvm.jar (5.4.0), okio-jvm.jar (3.18.1), junit-console.jar (1.14.0).
This intentionally does not certify Android UI, WebView or Keystore.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def run(checkout: Path, kotlin_libs: Path, deps: Path, java: str, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    source = checkout / 'app/src/main/java/eu/kanade/tachiyomi/extension/sandbox'
    tests = checkout / 'app/src/test/java/eu/kanade/tachiyomi'
    store = (source / 'SandboxCookieStore.kt').read_text()
    core = output / 'CookieCore.kt'
    core.write_text(
        'package eu.kanade.tachiyomi.extension.sandbox\n'
        'import java.io.IOException\nimport kotlinx.serialization.json.*\nimport okhttp3.*\n'
        + store[store.index('internal interface RevocableCookieJar'):store.index('internal class EncryptedCookieStorage')]
    )
    files = [core, source / 'BrowserCookieSession.kt', source / 'SandboxNetworkPolicy.kt',
             tests / 'extension/sandbox/BrowserCookieSessionTest.kt', tests / 'extension/sandbox/CookieBankTest.kt',
             checkout / 'app/src/main/java/eu/kanade/tachiyomi/ui/documents/DocumentImportSpace.kt',
             tests / 'ui/documents/DocumentImportSpaceTest.kt',
             checkout / 'app/src/main/java/eu/kanade/tachiyomi/data/backup/create/BackupRetention.kt',
             checkout / 'app/src/main/java/eu/kanade/tachiyomi/data/backup/create/BackupArchiveWriter.kt',
             checkout / 'app/src/main/java/eu/kanade/tachiyomi/data/backup/restore/restorers/SourcePreferenceNamespace.kt',
             tests / 'data/backup/create/BackupRetentionTest.kt',
             tests / 'data/backup/create/BackupArchiveWriterTest.kt',
             tests / 'data/backup/restore/SourcePreferenceNamespaceTest.kt']
    dependencies = [deps / name for name in ('okhttp-jvm.jar', 'okio-jvm.jar', 'junit-console.jar')]
    assert all(p.is_file() for p in dependencies)
    import os
    classpath = os.pathsep.join(str(p.resolve()) for p in [*kotlin_libs.glob('*.jar'), *dependencies])
    manifest = {'scope': 'JVM policies only; Android UI/Keystore/WebView not tested',
                'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                'dependencies': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}}
    (output / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
    commands = [
        [java, '-cp', classpath, 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect',
         '-classpath', classpath, '-d', str(output / 'tests.jar'), *map(str, files)],
        [java, '-cp', str(output / 'tests.jar') + os.pathsep + classpath,
         'org.junit.platform.console.ConsoleLauncher', 'execute', '--disable-banner', '--disable-ansi-colors',
         '--select-class', 'eu.kanade.tachiyomi.extension.sandbox.BrowserCookieSessionTest',
         '--select-class', 'eu.kanade.tachiyomi.extension.sandbox.CookieBankTest',
         '--select-class', 'eu.kanade.tachiyomi.ui.documents.DocumentImportSpaceTest',
         '--select-class', 'eu.kanade.tachiyomi.data.backup.create.BackupRetentionTest',
         '--select-class', 'eu.kanade.tachiyomi.data.backup.create.BackupArchiveWriterTest',
         '--select-class', 'eu.kanade.tachiyomi.data.backup.restore.SourcePreferenceNamespaceTest'],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True, text=True)
        (output / f'{index}.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'Command {index} failed; inspect {output / f"{index}.log"}')
    print((output / '1.log').read_text())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--kotlin-libs', type=Path, required=True)
    parser.add_argument('--deps', type=Path, required=True)
    parser.add_argument('--java', default='java')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.checkout.resolve(), args.kotlin_libs.resolve(), args.deps.resolve(), args.java, args.output.resolve())
