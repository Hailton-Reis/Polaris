"""Shared reversible display overrides for an already verified emulator."""
import json
import re


def display_state(text, kind):
    values = dict(re.findall(r'(Physical|Override) (?:size|density):\s*([0-9x]+)', text))
    pattern = r'\d{2,5}x\d{2,5}' if kind == 'size' else r'\d{2,4}'
    if not values.get('Physical') or any(not re.fullmatch(pattern, value) for value in values.values()):
        raise ValueError('Nao foi possivel ler a configuracao de tela atual.')
    return values.get('Override', 'reset')


def change_display(bridge, backup, restore=False):
    if restore:
        if not backup.is_file():
            raise ValueError('Nao existe configuracao anterior salva por esta ferramenta.')
        state = json.loads(backup.read_text(encoding='utf-8'))
        for key in ('size', 'density'):
            pattern = r'(reset|\d{2,5}x\d{2,5})' if key == 'size' else r'(reset|\d{2,4})'
            if not re.fullmatch(pattern, state.get(key, '')):
                raise ValueError('Backup de tela invalido; nenhuma configuracao aplicada.')
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

