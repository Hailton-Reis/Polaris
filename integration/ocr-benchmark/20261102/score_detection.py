from pathlib import Path
from PIL import ImageFont
import json
root=Path(__file__).parent;manifest=json.loads((root/'long-strip-expected.json').read_text());font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',29);large=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',64);single=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',64);truth=[]
def add(text,x,y,font):
 a,b,c,d=font.getbbox(text);truth.append(dict(text=text,x=x+a,y=y+b,width=c-a,height=d-b))
add('POLARIS - LONG STRIP OCR',60,80,font);add('Synthetic control, not a quality score',60,125,font)
for item in manifest['expected_cases']:
 case=item['case'];y=item['page_y']
 if case.startswith('seam'):
  for i,t in enumerate(item['source_lines']):add(t,110,y-85+i*54,font)
 elif case=='single-character':add('I',165,605,single)
 elif case=='large-short-dialogue':add('NO!',410,975,large)
 elif case=='outside-caption':add(item['source_lines'][0],80,1400,font)
def iou(a,b):
 w=max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']));h=max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']));inter=w*h
 return inter/max(1,a['width']*a['height']+b['width']*b['height']-inter)
r=json.loads((root/'long-detector-results.json').read_text());whole=r['whole']['boxes'];tiled=[dict(b,y=b['y']+s['top']) for s in r['strips'] for b in s['boxes']]
result={'scope':'Detection-only, accepted pre-unclip boxes, synthetic line truth; no recognition quality implied','iou_threshold':.3,'expected_lines':len(truth),'whole':{'raw_boxes':len(whole),'matched_lines':sum(any(iou(t,b)>=.3 for b in whole) for t in truth)},'strips':{'raw_boxes':len(tiled),'matched_lines':sum(any(iou(t,b)>=.3 for b in tiled) for t in truth)},'ground_truth':truth}
(root/'detection-score.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='ground_truth'})
