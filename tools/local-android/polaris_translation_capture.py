#!/usr/bin/env python3
"""Local evidence for a loaded chapter; never starts translation or targets phones."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import time
import uuid
import webbrowser
import zipfile

from polaris_emulator import AVDS, PACKAGE, EmulatorError, executable, find_device, sdk_location

COMPONENT = PACKAGE + '/eu.kanade.tachiyomi.polaris.TranslationCaptureReceiver'
MAX_SOURCE = 32 * 1024 * 1024
MAX_DISK = 512 * 1024 * 1024


def command(args, *, binary=False):
    result = subprocess.run([str(x) for x in args], capture_output=True, timeout=35)
    if result.returncode:
        raise EmulatorError('ADB falhou; confira se o emulador Polaris permanece aberto.')
    return result.stdout if binary else result.stdout.decode('utf-8', errors='replace')


def owned_device(workspace, adb):
    avd = AVDS['spike001']
    marker = workspace / 'emulador' / (avd + '.owner.txt')
    directory = workspace / 'emulador' / 'avd' / (avd + '.avd')
    if not marker.is_file() or marker.read_text(encoding='utf-8').strip() != avd or not directory.is_dir():
        raise EmulatorError('AVD Polaris sem identificacao de propriedade. Abra pela opcao 9 do CMD.')
    serial = find_device(adb, avd)
    if not serial:
        raise EmulatorError('Abra o emulador Polaris pela opcao 9. Celulares nao sao usados por esta ferramenta.')
    return serial


def parse_broadcast(output):
    match = re.search(r'Broadcast completed: result=(-?\d+)(?:, data="(.*)")?', output)
    if not match or match[1] != '0' or not match[2]:
        raise EmulatorError('Captura indisponivel. Instale o build de diagnostico e abra um capitulo carregado.')
    try:
        result = json.loads(match[2])
    except json.JSONDecodeError as exc:
        raise EmulatorError('Resposta de diagnostico invalida.') from exc
    if not isinstance(result, dict) or result.get('error'):
        raise EmulatorError('O leitor nao esta pronto para captura.')
    return result


class Bridge:
    def __init__(self, adb, serial):
        self.adb, self.serial = adb, serial

    def shell(self, *args):
        return command([self.adb, '-s', self.serial, 'shell', *args])

    def operation(self, name, **extras):
        args = ['am', 'broadcast', '--receiver-foreground', '-n', COMPONENT, '--es', 'operation', name]
        for key, value in extras.items():
            args.extend(['--ez' if isinstance(value, bool) else '--es', key,
                         str(value).lower() if isinstance(value, bool) else str(value)])
        return parse_broadcast(self.shell(*args))

    def binary(self, *args):
        return command([self.adb, '-s', self.serial, 'exec-out', *args], binary=True)


def png_size(data):
    if len(data) < 45 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR' or data[-8:-4] != b'IEND':
        raise EmulatorError('Captura PNG incompleta; arquivo rejeitado.')
    width, height = struct.unpack('>II', data[16:24])
    if not (100 <= width <= 8192 and 100 <= height <= 8192):
        raise EmulatorError('Dimensoes de captura invalidas.')
    return width, height


def checked_status(bridge, chapter, expected=None):
    status = bridge.operation('status')
    if status.get('chapterId') != chapter:
        raise ChapterBoundary()
    if not status.get('sourceReady'):
        raise EmulatorError('Pagina original ainda carregando. Aguarde e repita a coleta.')
    if expected and any(status.get(key) != expected.get(key) for key in ('pageIndex', 'translationHash')):
        raise EmulatorError('Pagina ou traducao mudou durante a comparacao; repita sem tocar no leitor.')
    return status


class ChapterBoundary(Exception):
    pass


def export_page(bridge, folder, chapter, expected):
    token = uuid.uuid4().hex
    relative = 'cache/translation-capture/' + token
    try:
        checked_status(bridge, chapter, expected)
        result = bridge.operation('export', request_token=token)
        if result.get('relativeDirectory') != relative:
            raise EmulatorError('Diretorio de exportacao inesperado.')
        if result.get('chapterId') != chapter or result.get('pageIndex') != expected['pageIndex']:
            raise EmulatorError('Exportacao mudou de pagina; comparacao descartada.')
        if result.get('status', {}).get('translationHash') != expected['translationHash']:
            raise EmulatorError('Traducao mudou durante a exportacao.')
        if not 0 < result.get('sourceBytes', 0) <= MAX_SOURCE:
            raise EmulatorError('Tamanho de pagina excede o limite de captura.')
        record_bytes = bridge.binary('run-as', PACKAGE, 'cat', relative + '/record.json')
        if len(record_bytes) > 512 * 1024:
            raise EmulatorError('Registro de traducao muito grande.')
        record = json.loads(record_bytes)
        source = bridge.binary('run-as', PACKAGE, 'cat', relative + '/source.bin')
        if len(source) != result['sourceBytes'] or hashlib.sha256(source).hexdigest() != result['sourceSha256']:
            raise EmulatorError('Original exportado com tamanho ou SHA-256 divergente.')
        # Deduplicate tall source images between overlapping screenshots.
        extension = '.png' if source.startswith(b'\x89PNG\r\n\x1a\n') else '.bin'
        if source.startswith(b'\xff\xd8\xff'):
            extension = '.jpg'
        elif source[:4] == b'RIFF' and source[8:12] == b'WEBP':
            extension = '.webp'
        name = result['sourceSha256'] + extension
        destination = folder.parent / 'sources' / name
        destination.parent.mkdir(exist_ok=True)
        if not destination.exists():
            destination.write_bytes(source)
        (folder / 'record.json').write_bytes(record_bytes)
        return record, '../sources/' + name
    finally:
        # Includes errors during export or transfer; temporary app cache is removed.
        bridge.operation('clear', request_token=token)


def write_report(root, report):
    (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    parts = ['<!doctype html><meta charset="utf-8"><title>Polaris — comparação</title>',
             '<style>body{font:16px system-ui;margin:24px;background:#101522;color:#edf3fc}',
             'img{width:48%;vertical-align:top}section{margin:40px 0}td{padding:8px;border:1px solid #667}',
             'table{border-collapse:collapse;width:100%}a{color:#84deef}pre{white-space:pre-wrap}</style>',
             '<h1>Polaris — evidências da leitura</h1>',
             '<p>Coleta: ' + html.escape(report['collection']) + '. Qualidade: AGUARDA ANÁLISE.</p>',
             '<p>Partindo da posição atual. Nenhuma tradução foi solicitada. O registro contém o OCR já salvo,',
             ' após filtros, e a tradução; não é uma nova execução do OCR. A configuração atual não comprova',
             ' qual motor produziu traduções anteriores. O original exportado é a página ativa;',
             ' a tela pode também mostrar fragmentos de páginas vizinhas.</p>']
    for frame in report['frames']:
        name = frame['name']
        record = json.loads((root / name / 'record.json').read_text(encoding='utf-8'))
        parts.extend(['<section><h2>' + html.escape(name) + '</h2>',
                      '<p>Esquerda: original. Direita: tradução.</p>',
                      f'<img src="{name}/original.png"><img src="{name}/translated.png">',
                      f'<p><a href="{name}/record.json">Registro salvo</a> · ',
                      f'<a href="{name}/{frame["source"]}">Imagem original integral</a></p>',
                      '<table><tr><th>Texto reconhecido salvo</th><th>Tradução salva</th></tr>'])
        for block in (record.get('page') or {}).get('blocks', []):
            parts.append('<tr><td><pre>' + html.escape(block.get('text', '')) + '</pre></td><td><pre>' +
                         html.escape(block.get('translation', '')) + '</pre></td></tr>')
        parts.append('</table></section>')
    (root / 'comparacao.html').write_text('\n'.join(parts), encoding='utf-8')


def capture(bridge, root, max_frames=60, pause=time.sleep):
    first = bridge.operation('status')
    if not first.get('vertical'):
        raise EmulatorError('Esta coleta automatica foi preparada para faixa longa. Ative o modo webtoon.')
    # A page with no translated blocks may be the defect being investigated.
    # Preserve it as evidence instead of refusing the very case we need.
    chapter = first['chapterId']
    initial_visibility = first['translationsVisible']
    report = {'collection': 'PARTIAL_LIMIT', 'quality': 'PENDING_REVIEW', 'frames': [], 'error': None}
    root.mkdir(parents=True, exist_ok=False)
    try:
        for number in range(1, max_frames + 1):
            status = checked_status(bridge, chapter)
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) > MAX_DISK - 3 * MAX_SOURCE:
                report['collection'] = 'PARTIAL_DISK_BUDGET'
                break
            name = f'frame-{number:03d}'
            folder = root / name
            folder.mkdir()
            for visible, filename in ((False, 'original.png'), (True, 'translated.png')):
                bridge.operation('visibility', visible=visible)
                pause(0.6)
                checked_status(bridge, chapter, status)
                image = bridge.binary('screencap', '-p')
                width, height = png_size(image)
                checked_status(bridge, chapter, status)
                (folder / filename).write_bytes(image)
            _, source = export_page(bridge, folder, chapter, status)
            report['frames'].append({'name': name, 'pageIndex': status['pageIndex'], 'source': source})
            status = checked_status(bridge, chapter)
            if not status.get('canScrollForward'):
                report['collection'] = 'REACHED_READER_END'
                break
            bridge.shell('input', 'swipe', str(width // 2), str(int(height * .80)),
                         str(width // 2), str(int(height * .25)), '450')
            pause(0.8)
    except ChapterBoundary:
        report['collection'] = 'STOPPED_AT_CHAPTER_BOUNDARY'
    except Exception:
        report['collection'] = 'PARTIAL_ERROR'
        report['error'] = 'Coleta interrompida; confira o leitor e repita a partir da pagina desejada.'
        raise
    finally:
        try:
            bridge.operation('visibility', visible=initial_visibility)
        finally:
            write_report(root, report)
    return report


def display_state(text, kind):
    values = dict(re.findall(r'(Physical|Override) (?:size|density):\s*([0-9x]+)', text))
    pattern = r'\d{2,5}x\d{2,5}' if kind == 'size' else r'\d{2,4}'
    if not values.get('Physical') or any(not re.fullmatch(pattern, value) for value in values.values()):
        raise EmulatorError('Nao foi possivel ler a configuracao de tela atual.')
    return values.get('Override', 'reset')


def change_display(bridge, backup, restore=False):
    if restore:
        if not backup.is_file():
            raise EmulatorError('Nao existe configuracao anterior salva por esta ferramenta.')
        state = json.loads(backup.read_text(encoding='utf-8'))
        for key in ('size', 'density'):
            pattern = r'(reset|\d{2,5}x\d{2,5})' if key == 'size' else r'(reset|\d{2,4})'
            if not re.fullmatch(pattern, state.get(key, '')):
                raise EmulatorError('Backup de tela invalido; nenhuma configuracao aplicada.')
    else:
        previous = {key: display_state(bridge.shell('wm', key), key) for key in ('size', 'density')}
        if not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(json.dumps(previous), encoding='utf-8')
        state = {'size': '1080x1920', 'density': '420'}
    try:
        for key in ('size', 'density'):
            bridge.shell('wm', key, state[key])
    except Exception:
        if not restore:
            for key in ('size', 'density'):
                bridge.shell('wm', key, previous[key])
        raise
    if restore:
        backup.unlink()


def package_frame(root, number):
    report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
    frame = next((f for f in report['frames'] if f['name'] == f'frame-{number:03d}'), None)
    if not frame:
        raise EmulatorError('Numero de quadro nao coletado.')
    folder = root / frame['name']
    files = [folder / n for n in ('original.png', 'translated.png', 'record.json')]
    files.append(folder / frame['source'])
    resolved = [p.resolve() for p in files]
    if any(not p.is_relative_to(root.resolve()) or not p.is_file() for p in resolved):
        raise EmulatorError('Arquivo fora da coleta ou ausente; pacote recusado.')
    if sum(p.stat().st_size for p in resolved) > 95 * 1024 * 1024:
        raise EmulatorError('Caso excede 95 MiB; selecione outro quadro.')
    target = root / (frame['name'] + '-caso.zip')
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in resolved:
            archive.write(path, path.relative_to(root.resolve()))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('capture', 'display', 'restore'))
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--consent', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--max-frames', type=int, default=60)
    args = parser.parse_args()
    if not args.consent or not 1 <= args.max_frames <= 300:
        parser.error('Selecione a acao explicitamente no CMD; limite entre 1 e 300 quadros.')
    try:
        adb = executable(sdk_location(), 'adb')
        serial = owned_device(args.workspace, adb)
        bridge = Bridge(adb, serial)
        if args.action != 'capture':
            change_display(bridge, args.workspace / 'emulador' / 'translation-display-backup.json', args.action == 'restore')
            print('Tela ajustada. Nenhum dado do aplicativo foi apagado.')
            return 0
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
        root = args.workspace / 'relatorios' / ('traducao-' + stamp)
        print('Coletando a partir da posicao atual; nao toque no leitor. Sem envio de arquivos ou chamadas de traducao.')
        report = capture(bridge, root, args.max_frames)
        print('Relatorio local: ' + str(root / 'comparacao.html'))
        print('Coleta: ' + report['collection'] + '; qualidade aguarda analise.')
        if args.interactive:
            webbrowser.open((root / 'comparacao.html').resolve().as_uri())
            answer = input('Quadro com defeito para gerar ZIP (ex.: 3), ou Enter para terminar: ').strip()
            if answer:
                if not answer.isdigit():
                    raise EmulatorError('Informe apenas o numero do quadro.')
                print('Caso para compartilhar manualmente: ' + str(package_frame(root, int(answer))))
        return 0
    except (EmulatorError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print('[ERRO] ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
