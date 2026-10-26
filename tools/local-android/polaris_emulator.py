#!/usr/bin/env python3
"""Polaris R001: independent, persistent Android Studio comparison emulators.

Only invoked after explicit confirmation in the main CMD. Never targets physical
Android devices or unrelated AVDs. Installation/launch is NOT runtime acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

IMAGE = 'system-images;android-35;google_apis;x86_64'
AVDS = {
    'baseline': 'Polaris_R001_Yomotsu_API35_x64',
    'spike001': 'Polaris_R001_Spike001_API35_x64',
}
PACKAGE = 'app.mihon.tachiyomiat.dev'
APK_RE = re.compile(r'^([0-9a-fA-F]{64})\s+\*?((?:baseline|spike001)/[^/\\]+\.apk)$')
VALID_STAGES = ('baseline', 'spike001', 'duo')


class EmulatorError(Exception):
    pass


def run(args, *, capture=True, input_text=None, timeout=120):
    try:
        return subprocess.run([str(v) for v in args], input=input_text, text=True,
                              capture_output=capture, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EmulatorError(f'Falha ao executar {Path(str(args[0])).name}: {exc}') from exc


def require_success(result, label):
    if result.returncode:
        detail = (result.stderr or result.stdout or '').strip()[-800:]
        raise EmulatorError(f'{label} falhou (exit={result.returncode}): {detail}')
    return result.stdout or ''


def sdk_location():
    for name in ('ANDROID_HOME', 'ANDROID_SDK_ROOT'):
        raw = os.getenv(name)
        if raw and Path(raw).is_dir():
            return Path(raw).resolve()
    raw = os.getenv('LOCALAPPDATA')
    if raw and (Path(raw) / 'Android' / 'Sdk').is_dir():
        return (Path(raw) / 'Android' / 'Sdk').resolve()
    raise EmulatorError('Android SDK nao encontrado. Use diagnostico do CMD.')


def executable(sdk, name):
    paths = {
        'sdkmanager': sdk / 'cmdline-tools' / 'latest' / 'bin' / 'sdkmanager.bat',
        'avdmanager': sdk / 'cmdline-tools' / 'latest' / 'bin' / 'avdmanager.bat',
        'emulator': sdk / 'emulator' / 'emulator.exe',
        'adb': sdk / 'platform-tools' / 'adb.exe',
    }
    result = paths[name]
    if name != 'emulator' and not result.is_file():
        raise EmulatorError(f'Ferramenta SDK ausente: {result}')
    return result


def check_acceleration(emulator):
    info = run([emulator, '-accel-check'], timeout=45)
    output = (info.stdout or '') + (info.stderr or '')
    if info.returncode or not re.search(r'(installed and usable|is usable|accel:\s*0)', output, re.I):
        raise EmulatorError('Virtualizacao/WHPX indisponivel. Confira BIOS e Plataforma de '
                            'Hipervisor do Windows. ' + output[-400:])


def find_device(adb, avd):
    listing = require_success(run([adb, 'devices'], timeout=20), 'adb devices')
    for line in listing.splitlines():
        match = re.match(r'^(emulator-\d+)\s+device(?:\s|$)', line.strip())
        if not match:
            continue  # physical devices, offline devices and unrelated serials are never targets
        serial = match.group(1)
        name_result = run([adb, '-s', serial, 'emu', 'avd', 'name'], timeout=20)
        if name_result.returncode == 0 and avd in [x.strip() for x in (name_result.stdout or '').splitlines()]:
            return serial
    return None


def select_x86_64_apk(paths, stage):
    """Upstream Gradle splits by ABI + universal: choose exact x86_64 deterministically."""
    if not paths:
        raise EmulatorError(f'Nenhum APK para {stage}')
    specific = [p for p in paths if 'x86_64' in p.name.lower()]
    universal = [p for p in paths if 'universal' in p.name.lower()]
    if len(specific) == 1:
        return specific[0]
    if not specific and len(universal) == 1:
        return universal[0]
    if len(paths) == 1:
        name = paths[0].name.lower()
        if all(abi not in name for abi in ('arm64', 'armeabi', 'x86-')):
            return paths[0]  # old universal builds without an explicit universal suffix
    raise EmulatorError(f'Escolha APK {stage} ambigua. Arquivos: ' + ', '.join(p.name for p in paths))


def find_apks(workspace):
    root = workspace / 'PolarisLocal' / 'evidence'
    if not root.is_dir():
        raise EmulatorError('Nenhum build local encontrado. Execute opcao 4 do CMD.')
    examined = []
    for folder in sorted(root.glob('issue002-*'), reverse=True):
        status = folder / 'build-status.txt'
        manifest = folder / 'apks' / 'SHA256SUMS.txt'
        if not status.is_file() or not manifest.is_file():
            continue
        if 'APK_BUILDS_PASS_NO_NEW_UNIT_REGRESSIONS' not in status.read_text(encoding='utf-8'):
            continue
        apk_dir = folder / 'apks'
        all_apks = {stage: sorted((apk_dir / stage).glob('*.apk')) for stage in ('baseline', 'spike001')}
        if any(not apks for apks in all_apks.values()):
            examined.append(f'{folder.name}: faltam APKs')
            continue
        hashes = {}
        for line in manifest.read_text(encoding='utf-8').splitlines():
            match = APK_RE.fullmatch(line)
            if not match:
                raise EmulatorError(f'Manifesto SHA-256 invalido em {manifest}: {line[:100]}')
            key = match.group(2)
            if key in hashes:
                raise EmulatorError(f'Hash SHA-256 duplicado: {key}')
            hashes[key] = match.group(1).lower()
        selected = {}
        for stage, apk_paths in all_apks.items():
            # Verify ALL listed built APKs, not only the one being installed.
            for apk in apk_paths:
                key = f'{stage}/{apk.name}'
                expected = hashes.get(key)
                if not expected or hashlib.sha256(apk.read_bytes()).hexdigest() != expected:
                    raise EmulatorError(f'Hash SHA-256 ausente ou divergente: {key}')
            selected[stage] = select_x86_64_apk(apk_paths, stage)
        if set(hashes) != {f'{stage}/{p.name}' for stage, apks in all_apks.items() for p in apks}:
            raise EmulatorError('Manifesto tem entradas extras ou arquivos ausentes.')
        for stage, apk in selected.items():
            print(f'[OK] APK {stage} x86_64: {apk.name}', flush=True)
        print(f'[OK] Manifesto SHA-256 validado: {manifest}', flush=True)
        return selected, folder
    raise EmulatorError('Nao encontrei build completo verificavel. ' + '; '.join(examined[-3:]) +
                        '. Use opcao 4 ou confira apks/SHA256SUMS.txt.')


def ensure_sdk_image(sdk):
    if os.getenv('PROCESSOR_ARCHITECTURE', '').upper() != 'AMD64':
        raise EmulatorError('Imagem x86_64 requer Windows x64. Em ARM64 use Device Manager.')
    manager = executable(sdk, 'sdkmanager')
    emulator = executable(sdk, 'emulator')
    if not emulator.is_file():
        print('Instalando componente oficial Android Emulator...', flush=True)
        require_success(run([manager, f'--sdk_root={sdk}', 'emulator'], capture=False, timeout=1800), 'Android Emulator')
    if not emulator.is_file():
        raise EmulatorError('Android Emulator nao instalado corretamente.')
    check_acceleration(emulator)
    image_props = sdk / 'system-images' / 'android-35' / 'google_apis' / 'x86_64' / 'source.properties'
    if not image_props.is_file():
        print('Instalando imagem Android 15 API 35 Google APIs x86_64...', flush=True)
        require_success(run([manager, f'--sdk_root={sdk}', IMAGE], capture=False, timeout=3600), 'Imagem API35')
    if not image_props.is_file():
        raise EmulatorError('Imagem API35 nao foi instalada corretamente.')


def ensure_avd(workspace, sdk, stage):
    """Each AVD owns its own userdata and installed apps, persisting across restarts."""
    avd = AVDS[stage]
    emulator = executable(sdk, 'emulator')
    avdmanager = executable(sdk, 'avdmanager')
    root = workspace / 'emulador'
    root.mkdir(parents=True, exist_ok=True)
    avd_path = root / 'avd' / f'{avd}.avd'
    marker = root / f'{avd}.owner.txt'
    registered = require_success(run([emulator, '-list-avds'], timeout=35), 'Listar AVDs')
    present = avd in [name.strip() for name in registered.splitlines()]
    if present:
        if not marker.is_file() or marker.read_text(encoding='utf-8-sig').strip() != avd or not avd_path.is_dir():
            raise EmulatorError(f'AVD {avd} existente sem comprovante de propriedade. Nao sera alterado.')
        return avd, avd_path
    if marker.exists() or avd_path.exists():
        raise EmulatorError(f'AVD {avd} parcialmente existente; preservado para revisao manual.')
    print(f'Criando AVD independente: {avd}', flush=True)
    require_success(run([avdmanager, 'create', 'avd', '-n', avd, '-k', IMAGE, '-p', avd_path],
                        input_text='no\n', timeout=180), 'Criacao do AVD')
    if not avd_path.is_dir():
        raise EmulatorError(f'AVD nao criou pasta esperada: {avd_path}')
    marker.write_text(avd + '\n', encoding='utf-8')
    return avd, avd_path


def start_avd(workspace, sdk, stage):
    avd, avd_path = ensure_avd(workspace, sdk, stage)
    adb, emulator = executable(sdk, 'adb'), executable(sdk, 'emulator')
    current = find_device(adb, avd)
    if current:
        return avd, current
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out = workspace / 'emulador' / f'{stage}-{stamp}.stdout.log'
    err = workspace / 'emulador' / f'{stage}-{stamp}.stderr.log'
    # Deliberately NOT -wipe-data, -read-only or -no-window: all app settings persist.
    # Snapshot loading is disabled for deterministic startup, but userdata persists.
    with out.open('wb') as stdout, err.open('wb') as stderr:
        subprocess.Popen([str(emulator), '-avd', avd, '-no-snapshot-load', '-no-snapshot-save'],
                         stdout=stdout, stderr=stderr,
                         creationflags=(0x00000200 if os.name == 'nt' else 0))
    return avd, None


def wait_for_boot(adb, avd, *, timeout_seconds=420):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        serial = find_device(adb, avd)
        if serial:
            boot = run([adb, '-s', serial, 'shell', 'getprop', 'sys.boot_completed'], timeout=20)
            if boot.returncode == 0 and (boot.stdout or '').strip() == '1':
                api = require_success(run([adb, '-s', serial, 'shell', 'getprop', 'ro.build.version.sdk']), 'Android API')
                if api.strip() != '35':
                    raise EmulatorError(f'AVD {avd} executa API {api.strip()}, esperada 35.')
                print(f'[OK] {avd} pronto no serial {serial}', flush=True)
                return serial
        time.sleep(5)
    raise EmulatorError(f'AVD {avd} nao iniciou. Confira logs em PolarisDev/emulador e WHPX.')


def install_and_launch(adb, serial, avd, apk, stage, workspace, build):
    if not re.fullmatch(r'emulator-\d+', serial) or find_device(adb, avd) != serial:
        raise EmulatorError('ADB nao corresponde ao AVD Polaris indicado; instalacao bloqueada.')
    if AVDS.get(stage) != avd:
        raise EmulatorError('Versao e AVD nao combinam; instalacao bloqueada.')
    # -r keeps app settings. Signature mismatch must FAIL, never uninstall automatically.
    print(f'Instalando {stage} em {avd} ({serial}), preservando dados...', flush=True)
    require_success(run([adb, '-s', serial, 'install', '-r', '-t', apk], timeout=300), 'Instalacao APK')
    installed = require_success(run([adb, '-s', serial, 'shell', 'pm', 'path', PACKAGE]), 'Confirmacao package')
    if 'package:' not in installed:
        raise EmulatorError(f'Pacote Android nao encontrado: {PACKAGE}')
    launched = require_success(run([adb, '-s', serial, 'shell', 'monkey', '-p', PACKAGE,
                                    '-c', 'android.intent.category.LAUNCHER', '1']), 'Solicitar abertura')
    if not re.search(r'Events injected:\s*1', launched):
        raise EmulatorError('Nao foi confirmada a entrega do comando de abertura.')
    evidence = workspace / 'relatorios' / f'emulador-{stage}-{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}'
    evidence.mkdir(parents=True, exist_ok=False)
    result = {
        'project': 'Polaris', 'stage': stage, 'avd': avd, 'serial': serial, 'android_api': 35,
        'apk': str(apk), 'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
        'build_evidence': str(build), 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'config_persistence': 'independent AVD userdata; persists across normal shutdowns',
        'verdict': 'INSTALLED_AND_LAUNCH_REQUESTED_NOT_VISUALLY_VERIFIED',
        'pending': ['visible UI', 'app remains open', 'extension/source setup', 'B01-B05'],
    }
    (evidence / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f'[OK] Pedido de abertura enviado ao {avd}; evidencia: {evidence}', flush=True)
    return evidence


def create_comparison_template(workspace, evidence):
    report = evidence / 'comparacao-fontes.json'
    payload = {
        'date': datetime.now().isoformat(timespec='seconds'),
        'baseline_avd': AVDS['baseline'],
        'polaris_avd': AVDS['spike001'],
        'test_items': [
            {'id': 'A01', 'description': 'baseline abre e permanece visivel', 'result': None},
            {'id': 'A02', 'description': 'Polaris abre e permanece visivel', 'result': None},
            {'id': 'B01', 'description': 'mesmo manga, duas fontes autorizadas', 'result': None},
            {'id': 'B02', 'description': 'correlacao e deduplicacao', 'result': None},
            {'id': 'B03', 'description': 'capitulos e leitura real', 'result': None},
            {'id': 'B04', 'description': 'estado offline/cache', 'result': None},
            {'id': 'B05', 'description': 'persistencia apos reinicio', 'result': None},
        ],
        'note': 'Preencha resultados manualmente; nenhum PASS foi presumido.',
    }
    report.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'[OK] Planilha JSON para anotacoes (sem resultados inventados): {report}', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=VALID_STAGES)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--consent', action='store_true')
    args = parser.parse_args(argv)
    if not args.consent:
        print('[INTERROMPIDO] A instalacao exige autorizacao pelo CMD.', file=sys.stderr)
        return 3
    try:
        workspace = args.workspace.expanduser().resolve()
        packages, build = find_apks(workspace)  # explain APK selection failures before SDK setup
        sdk = sdk_location()
        ensure_sdk_image(sdk)
        stages = ('baseline', 'spike001') if args.stage == 'duo' else (args.stage,)
        # Launch both windows before waiting, so the comparison starts side by side.
        avds = {}
        for stage in stages:
            avd, _ = start_avd(workspace, sdk, stage)
            avds[stage] = avd
        adb = executable(sdk, 'adb')
        records = []
        for stage in stages:
            serial = wait_for_boot(adb, avds[stage])
            records.append(install_and_launch(adb, serial, avds[stage], packages[stage], stage, workspace, build))
        if args.stage == 'duo':
            create_comparison_template(workspace, records[-1])
            print('Arraste Yomotsu para a metade esquerda e Polaris para a direita '
                  '(Windows+Seta Esquerda/Direita, com cada janela selecionada).', flush=True)
        print('As configuracoes e bibliotecas de cada app sao salvas no seu proprio AVD.', flush=True)
        print('Feche as janelas Android normalmente; nao use Wipe Data nem apague as pastas avd.', flush=True)
        print('Apenas instalar/abrir NAO significa PASS de runtime ou fontes reais.', flush=True)
        return 0
    except EmulatorError as exc:
        print('[ERRO EMULADOR]', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
