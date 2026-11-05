#!/usr/bin/env python3
"""Generate an original long-strip control fixture; Pillow is a developer-only dependency."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'integration/internal-beta/long-strip-fixture'
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    width, height = 720, 20_000
    image = Image.new('RGB', (width, height), '#cedae5')
    draw = ImageDraw.Draw(image)
    normal = ImageFont.truetype(str(FONT), 29)
    large = ImageFont.truetype(str(FONT), 64)
    single = ImageFont.truetype(str(FONT.with_name('DejaVuSerif.ttf')), 64)
    draw.text((60, 80), 'POLARIS - LONG STRIP OCR', font=normal, fill='black')
    draw.text((60, 125), 'Synthetic control, not a quality score', font=normal, fill='black')
    expected = []
    for index, boundary in enumerate(range(2048, height - 384, 1664), 1):
        box = (60, boundary - 130, 660, boundary + 160)
        draw.rounded_rectangle(box, radius=75, fill='white', outline='black', width=3)
        lines = [f'Scene {index:02d} begins here.', 'Keep every single word.', 'This is the final line.']
        for row, text in enumerate(lines):
            draw.text((110, boundary - 85 + row * 54), text, font=normal, fill='black')
        expected.append({'case': f'seam-{index:02d}', 'page_y': boundary, 'source_lines': lines,
                         'note': 'Phrase crosses a potential strip edge; compare completeness and duplicate counts.'})
    draw.ellipse((80, 540, 270, 760), fill='white', outline='black', width=3)
    draw.text((165, 605), 'I', font=single, fill='black')
    draw.ellipse((330, 900, 650, 1150), fill='white', outline='black', width=3)
    draw.text((410, 975), 'NO!', font=large, fill='black')
    draw.text((80, 1400), 'A caption outside the balloons.', font=normal, fill='black')
    expected += [
        {'case': 'single-character', 'page_y': 605, 'source_lines': ['I']},
        {'case': 'large-short-dialogue', 'page_y': 975, 'source_lines': ['NO!']},
        {'case': 'outside-caption', 'page_y': 1400, 'source_lines': ['A caption outside the balloons.'],
         'note': 'Recognition and safe automatic placement must be assessed separately.'},
    ]
    stream = BytesIO()
    image.save(stream, format='PNG', optimize=True)
    data = stream.getvalue()
    archive = OUTPUT / 'Polaris-faixa-longa-controle.cbz'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        item = zipfile.ZipInfo('001.png', date_time=(2026, 11, 2, 0, 0, 0))
        item.compress_type = zipfile.ZIP_DEFLATED
        output.writestr(item, data)
    manifest = {
        'fixture': archive.name, 'purpose': 'Synthetic long-strip control; Android OCR results remain unmeasured',
        'image': '001.png', 'width': width, 'height': height,
        'image_sha256': hashlib.sha256(data).hexdigest(),
        'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'font': 'DejaVu Sans and Serif (system fonts; no font file embedded)',
        'source_text_and_art': 'Original generated test material, CC0',
        'expected_cases': expected,
        'manual_test': 'Compare standard ML Kit and opt-in strips on this same image. This fixture cannot validate real manga fonts or CJK quality.',
    }
    (OUTPUT / 'expected.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(archive, archive.stat().st_size)


if __name__ == '__main__':
    main()
