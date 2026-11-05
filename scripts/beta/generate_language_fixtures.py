"""Generate original OCR pages; requires Pillow and Noto Sans CJK (not needed by testers)."""
from pathlib import Path
import hashlib
import json
import textwrap
import zipfile
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2] / 'integration/internal-beta/language-fixtures'
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
TEXTS = {
 'en': ['The library opens tomorrow.', 'Sora will bring the blue book.', 'Please keep the name Sora unchanged.'],
 'ja': ['図書館は明日開きます。', 'ソラは青い本を持ってきます。', 'ソラという名前は変えないでください。'],
 'zh-CN': ['图书馆明天开放。', '小空会带来那本蓝色的书。', '请保留小空这个名字。'],
 'zh-TW': ['圖書館明天開放。', '小空會帶來那本藍色的書。', '請保留小空這個名字。'],
 'ko': ['도서관은 내일 문을 엽니다.', '소라는 파란 책을 가져올 것입니다.', '소라라는 이름은 바꾸지 마세요.'],
}

def main():
 ROOT.mkdir(parents=True, exist_ok=True)
 font = ImageFont.truetype(FONT, 44)
 small = ImageFont.truetype(FONT, 30)
 manifest = {'purpose': 'Authored script recognition and glossary smoke tests, not a native OCR quality PASS',
  'reference_pt': ['A biblioteca abre amanhã.', 'Sora trará o livro azul.', 'Mantenha o nome Sora.'],
  'human_source_language_review': 'PENDING', 'fixtures': []}
 for language, lines in TEXTS.items():
  font = ImageFont.truetype(FONT, 44, index={"ja":0,"ko":1,"zh-CN":2,"zh-TW":3}.get(language,0))
  page = Image.new('RGB', (1400, 2000), 'white'); draw = ImageDraw.Draw(page)
  draw.text((70, 60), 'Polaris beta OCR sample: ' + language, font=small, fill='black')
  for i, text in enumerate(lines):
   top = 200 + i * 340
   draw.rounded_rectangle((80, top, 1320, top + 280), radius=70, outline='black', width=4)
   wrapped = textwrap.wrap(text, width=42 if language == 'en' else 23)
   draw.multiline_text((150, top + 60), '\n'.join(wrapped), font=font, fill='black', spacing=14)
  if language == 'ja':
   draw.text((80, 1270), 'Vertical Japanese: columns read right to left', font=small, fill='black')
   for x, text in [(1150, '図書館は明日開きます。'), (1020, 'ソラは青い本を持ってきます。')]:
    for n, char in enumerate(text): draw.text((x, 1370 + 40*n), char, font=font, fill='black')
  png = ROOT / f'polaris-{language}.png'; page.save(png, optimize=True)
  cbz = ROOT / f'polaris-{language}.cbz'
  with zipfile.ZipFile(cbz, 'w', zipfile.ZIP_DEFLATED) as archive:
   archive.write(png, '001.png')
   archive.writestr('ComicInfo.xml', f'<ComicInfo><Title>Polaris {language} sample</Title><LanguageISO>{language}</LanguageISO></ComicInfo>')
  manifest['fixtures'].append({'language':language, 'source_lines':lines,
   'glossary_source': {'ja':'ソラ','ko':'소라','zh-CN':'小空','zh-TW':'小空'}.get(language,'Sora'),
   'glossary_target':'Sora','cbz':cbz.name,'cbz_bytes':cbz.stat().st_size,
   'sha256':hashlib.sha256(cbz.read_bytes()).hexdigest()})
 (ROOT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__': main()
