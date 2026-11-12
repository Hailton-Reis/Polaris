from pathlib import Path
import json,unicodedata,collections
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s).casefold() if not c.isspace())
def distance(a,b):
 row=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  current=[i]
  for j,y in enumerate(b,1):current.append(min(current[-1]+1,row[j]+1,row[j-1]+(x!=y)))
  row=current
 return row[-1]
def same(a,b):
 w=max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']));h=max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']));inter=w*h;aa=a['width']*a['height'];ab=b['width']*b['height']
 if min(aa,ab)<=0:return False
 if inter/max(1,aa+ab-inter)>=.72:return True
 x=norm(a['text']);y=norm(b['text'])
 return x and y and (x in y or y in x) and inter/min(aa,ab)>=.9 and abs(a['y']+a['height']/2-b['y']-b['height']/2)<=min(a['height'],b['height'])*.25
def deduplicate(lines):
 kept=[]
 for line in sorted(lines,key=lambda l:(-l.get('edge',0),-len(l['text']))):
  if not any(l.get('region')!=line.get('region') and same(l,line) for l in kept):kept.append(line)
 return sorted(kept,key=lambda l:(l['y'],l['x']))

def main():
 root=Path(__file__).parent
 cases=json.loads((root/'android/app/src/main/assets/cases/cases.json').read_text())
 lookup={x['id']:x for x in cases};lookup['en-long-strips']=dict(lookup['en-long-full'],id='en-long-strips')
 results=json.loads((root/'paddle-results.json').read_text())
 if (root/'paddle-pipeline-results.json').exists():
  results.update(json.loads((root/'paddle-pipeline-results.json').read_text()))
 if (root/'paddle-long-results.json').exists():
  for engine,rows in json.loads((root/'paddle-long-results.json').read_text()).items():
   results[engine].extend(rows)
 if (root/'mlkit-results.json').exists():
  results['mlkit']=json.loads((root/'mlkit-results.json').read_text())
 for rows in results.values():
  for row in rows:
   if row['id']=='en-long-strips':
    kept=deduplicate(row['lines'])
    row['text']='\n'.join(l['text'] for l in kept);row['deduplicated_lines']=kept
   elif row['id']=='en-long-full' and row.get('status')=='OK':
    row['text_sdk']=row.get('text','')
    row['text']='\n'.join(l['text'] for l in sorted(row['lines'],key=lambda l:(l['y'],l['x'])))
 summary=[];details=[]
 unsupported={'paddle_small':{'ko'},'paddle_tiny':{'ko','ja'},'paddle_pipeline_small':{'ko'},'paddle_pipeline_tiny':{'ko','ja'},'mlkit':set()}
 for engine,rows in results.items():
  totals=collections.defaultdict(lambda:dict(cases=0,characters=0,errors=0,exact=0,api_errors=0))
  for row in rows:
   c=lookup[row['id']];expected=norm(c['expected']);actual=norm(row.get('text',''));ok=row.get('status')=='OK';errors=distance(expected,actual) if ok else None;key=c['lang'] if c['kind']!='long' else row['id'];t=totals[key];t['cases']+=1
   if ok:t['characters']+=len(expected);t['errors']+=errors;t['exact']+=int(errors==0)
   else:t['api_errors']+=1
   details.append(dict(engine=engine,id=row['id'],lang=c['lang'],kind=c['kind'],expected=c['expected'],actual=row.get('text',''),errors=errors,characters=len(expected),exact=errors==0 if ok else False,status=row.get('status'),runtime_error=row.get('error')))
  for lang,t in totals.items():summary.append(dict(engine=engine,language=lang,**t,script_supported=lang not in unsupported[engine],cer=t['errors']/t['characters'] if t['characters'] else None))
 out=dict(summary=summary,details=details,metric='Levenshtein CER: Unicode NFKC, casefold, whitespace excluded, punctuation retained. Unsupported scripts reported separately; runtime errors are not OCR errors.',scope='Synthetic prepared text regions. Android ML Kit when available; Paddle ONNX CPU. Not an ARM speed/memory benchmark.',raw_results=results)
 (root/'scored-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 for s in summary:print(s['engine'],s['language'],s['exact'],'/',s['cases'],'CER',None if s['cer'] is None else round(100*s['cer'],2),'supported',s['script_supported'],'API errors',s['api_errors'])

if __name__=='__main__':main()
