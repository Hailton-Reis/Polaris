#!/usr/bin/env python3
"""Non-destructive A01/A02 smoke diagnostic of two *already-running* Polaris AVDs.

No app installation, UI taps, onboarding, app-data changes, emulator creation,
reboots, ADB log clearing, or network actions. Source tests B01-B05 stay pending.
Reports and screenshots remain exclusively under the user's local PolarisDev tree.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

import polaris_emulator as emulator

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
STAGES = ('baseline', 'spike001')


class SmokeError(Exception):
    pass


def adb_text(adb: Path, serial: str, *command: str, timeout=40) -> str:
    result = emulator.run([adb, '-s', serial, *command], timeout=timeout)
    if result.returncode:
        err = (result.stderr or result.stdout or '').strip()[-300:]
        raise SmokeError(f'ADB {command[0]} falhou no emulador {serial}: {err}')
    return result.stdout or ''


def screenshot(adb: Path, serial: str, dest: Path) -> None:
    """Save PNG directly on host, not on Android storage."""
    try:
        p = subprocess.run([str(adb), '-s', serial, 'exec-out', 'screencap', '-p'],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SmokeError(f'Falha na captura PNG {serial}: {exc}') from exc
    if p.returncode or not p.stdout.startswith(PNG_SIGNATURE) or len(p.stdout) < 24:
        raise SmokeError(f'Captura PNG invalida do emulador {serial}')
    dest.write_bytes(p.stdout)


def foreground_matches(package: str, windows: str, activities: str) -> bool:
    lines = windows.splitlines() + activities.splitlines()
    patterns = ('mCurrentFocus=', 'mFocusedApp=', 'topResumedActivity=', 'mResumedActivity:', 'ResumedActivity:')
    return any(package in line and any(p in line for p in patterns) for line in lines)


def check_stage(adb: Path, stage: str, directory: Path, *, capture=True) -> dict:
    avd = emulator.AVDS[stage]
    result = {'stage': stage, 'avd': avd, 'serial': None, 'checks': {},
              'warnings': [], 'screenshot': None, 'verdict': 'PENDING'}
    serial = emulator.find_device(adb, avd)   # verifies emulator-NNNN AND exact AVD name
    if not serial:
        result['checks']['avd_connected'] = False
        result['warnings'].append('Emulador ainda nao esta conectado. Use opcao 10 primeiro.')
        result['verdict'] = 'DEVICE_NOT_FOUND'
        return result
    result['serial'] = serial
    result['checks']['avd_connected'] = True
    try:
        boot = adb_text(adb, serial, 'shell', 'getprop', 'sys.boot_completed').strip()
        api = adb_text(adb, serial, 'shell', 'getprop', 'ro.build.version.sdk').strip()
        result['checks']['boot_completed'] = boot == '1'
        result['checks']['android_api_35'] = api == '35'
        pkg = emulator.PACKAGE
        installed = adb_text(adb, serial, 'shell', 'pm', 'path', pkg)
        result['checks']['package_installed'] = any(x.strip().startswith('package:') for x in installed.splitlines())
        process = emulator.run([adb, '-s', serial, 'shell', 'pidof', pkg], timeout=20)
        result['checks']['app_process_running'] = process.returncode == 0 and bool((process.stdout or '').strip())
        windows = adb_text(adb, serial, 'shell', 'dumpsys', 'window', timeout=40)
        activities = adb_text(adb, serial, 'shell', 'dumpsys', 'activity', 'activities', timeout=40)
        result['checks']['app_in_foreground'] = foreground_matches(pkg, windows, activities)
        # Only AndroidRuntime ERROR tags, do not collect full user logcat.
        runtime = adb_text(adb, serial, 'logcat', '-d', '-t', '300', '-s', 'AndroidRuntime:E', timeout=40)
        # Historical log lines are not a real-time crash verdict; record as advisory only.
        result['checks']['android_runtime_crash_seen_in_recent_logs'] = bool(
            'FATAL EXCEPTION' in runtime and (pkg in runtime or 'Process: '+pkg in runtime)
        )
        if result['checks']['android_runtime_crash_seen_in_recent_logs']:
            result['warnings'].append('Mensagem de crash no log AndroidRuntime (pode ser historica).')
        if capture:
            dest = directory / f'{stage}.png'
            try:
                screenshot(adb, serial, dest)
                result['screenshot'] = dest.name
                result['checks']['screenshot_captured'] = True
            except SmokeError as exc:
                result['checks']['screenshot_captured'] = False
                result['warnings'].append(str(exc))
        vital = ('avd_connected', 'boot_completed', 'android_api_35', 'package_installed',
                 'app_process_running', 'app_in_foreground')
        result['verdict'] = ('DIAGNOSTIC_OBSERVED_B01_B05_PENDING' if
                             all(result['checks'].get(x) for x in vital) else
                             'DIAGNOSTIC_FAILED_B01_B05_PENDING')
    except (SmokeError, emulator.EmulatorError) as exc:
        result['warnings'].append(str(exc))
        result['verdict'] = 'DIAGNOSTIC_ERROR_B01_B05_PENDING'
    return result


def report_html(payload: dict) -> str:
    """Human-readable, offline report, no script, no external requests."""
    cards=[]
    for r in payload['devices']:
        badges=''.join('<li>'+html.escape(k)+': <b>'+html.escape(str(v))+'</b></li>'
                       for k,v in r['checks'].items())
        warnings=''.join('<p>'+html.escape(w)+'</p>' for w in r['warnings'])
        src=html.escape(r['screenshot'] or '', quote=True)
        image = f'<img src="{src}" alt="Screenshot {html.escape(r["stage"])}" />' if src else '<p>Sem captura.</p>'
        cards.append('<article><h2>'+html.escape(r['avd'])+'</h2><p>'+html.escape(r['verdict'])+'</p>'+
                     image+'<ul>'+badges+'</ul>'+warnings+'</article>')
    return ('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
            '<title>Polaris - comparacao automatica A01/A02</title>'
            '<style>body{font:15px system-ui;margin:24px;background:#f6f7fb;color:#1e293b}'
            'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:18px}'
            'article{background:white;padding:18px;border-radius:16px;border:1px solid #ddd}'
            'img{display:block;width:100%;max-width:430px;margin:auto;border:1px solid #ccc}'
            'li{margin:.3em}p{overflow-wrap:anywhere}</style>'
            '<h1>Polaris - teste automatico sem fontes</h1>'
            '<p>Apenas AVD, boot, instalacao, processo, primeiro plano e screenshot. '
            'Nenhum assistente foi avancado; nenhuma fonte ou capitulo foi testado.</p>'
            '<main>'+''.join(cards)+'</main><p>B01-B05: PENDENTES DE CONFIGURACAO MANUAL.</p></html>')


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--consent',action='store_true')
    parser.add_argument('--no-screenshots',action='store_true')
    args=parser.parse_args(argv)
    if not args.consent:
        print('[CANCELADO] Execute a opcao 11 do CMD e confirme o teste.',file=sys.stderr)
        return 3
    workspace=args.workspace.expanduser().resolve()
    try:
        adb=emulator.executable(emulator.sdk_location(),'adb')
    except emulator.EmulatorError as exc:
        print('[ERRO] '+str(exc),file=sys.stderr)
        return 2
    target=workspace/'relatorios'/('smoke-A01-A02-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    target.mkdir(parents=True, exist_ok=False)
    results=[check_stage(adb,stage,target,capture=not args.no_screenshots) for stage in STAGES]
    data={'project':'Polaris','mode':'non_destructive_pre_configuration',
          'timestamp_utc':datetime.now(timezone.utc).isoformat(),
          'app_package':emulator.PACKAGE,'devices':results,
          'sources':'NOT_CONFIGURED_NOT_TESTED',
          'B01_B05':'PENDING_MANUAL_SOURCE_SETUP',
          'writes_to_android':'NONE','uploads':'NONE',
          'note':'Diagnostics do not prove functional reader acceptance; screenshots may contain private content.'}
    (target/'report.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (target/'report.html').write_text(report_html(data),encoding='utf-8')
    for item in results:
        print(f"[{item['stage']}] {item['avd']} {item['verdict']}; "
              f"serial={item['serial']}; screenshot={item['screenshot']}",flush=True)
        for w in item['warnings']:
            print('   Aviso: '+w,flush=True)
    print('Relatorio local: '+str(target/'report.html'),flush=True)
    print('Nenhuma fonte, login, biblioteca ou configuracao foi alterada.',flush=True)
    return 0 if all(x['verdict']=='DIAGNOSTIC_OBSERVED_B01_B05_PENDING' for x in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
