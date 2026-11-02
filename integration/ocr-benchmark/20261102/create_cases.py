from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,shutil,zipfile,io,os
root=Path(__file__).parent;repo=Path(os.environ.get('POLARIS_ENGINEERING_REPO',str(root.parents[2])));native=Path(os.environ.get('POLARIS_NATIVE_REPO','/workspace/polaris-documents'));out=root/'android/app/src/main/assets/cases';cases=[]
texts=['I','NO!','Keep the final line.','Sora will bring the blue book.','I will return tomorrow.','The library opens tomorrow.','Do not leave the last line behind.','Please keep the name Sora unchanged.']
fonts={'sans':'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','anime':str(native/'app/src/main/res/font/animeace.ttf'),'balsamiq':str(native/'app/src/main/res/font/balsamiq_sans.ttf')}
for style,path in fonts.items():
 for i,text in enumerate(texts):
  font=ImageFont.truetype(path,30);box=font.getbbox(text);im=Image.new('RGB',(box[2]-box[0]+36,box[3]-box[1]+30),'white');ImageDraw.Draw(im).text((18-box[0],15-box[1]),text,font=font,fill='black');name=f'en-{style}-{i}';im.save(out/(name+'.png'));cases.append(dict(id=name,file=name+'.png',lang='en',kind='line',expected=text))
base=repo/'integration/internal-beta/language-fixtures';m=json.loads((base/'manifest.json').read_text())
for item in m['fixtures']:
 im=Image.open(base/('polaris-'+item['language']+'.png'))
 for i,text in enumerate(item['source_lines']):
  top=200+i*340;font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',44,index={'ja':0,'ko':1,'zh-CN':2,'zh-TW':3}.get(item['language'],0));bbox=ImageDraw.Draw(im).textbbox((150,top+60),text,font=font);crop=im.crop((bbox[0]-8,bbox[1]-8,bbox[2]+8,bbox[3]+8));name=item['language']+'-panel-'+str(i);crop.save(out/(name+'.png'));cases.append(dict(id=name,file=name+'.png',lang=item['language'],kind='panel',expected=text))
base=repo/'integration/internal-beta/long-strip-fixture';m=json.loads((base/'expected.json').read_text())
with zipfile.ZipFile(base/m['fixture']) as z:(out/'long.png').write_bytes(z.read('001.png'))
expected=['POLARIS - LONG STRIP OCR','Synthetic control, not a quality score']
for c in sorted(m['expected_cases'],key=lambda c:c['page_y']):expected+=c['source_lines']
cases.append(dict(id='en-long-full',file='long.png',lang='en',kind='long',expected='\n'.join(expected)))
(out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2));print('Cases',len(cases))
