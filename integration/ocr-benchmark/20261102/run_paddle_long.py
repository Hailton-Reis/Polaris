from run_paddle_pipeline import *
allrows={};image=cv2.imread(str(assets/'long.png'))
for name,path in [('paddle_pipeline_small',models/'rec'),('paddle_pipeline_tiny',Path(os.environ.get('POLARIS_TINY_MODELS',str(root/'tiny'))))]:
 rec=ort.InferenceSession(str(path/'inference.onnx'),opts,providers=['CPUExecutionProvider']);dictionary=['']+yaml.safe_load((path/'inference.yml').read_text())['PostProcess']['character_dict']+[' '];rows=[]
 start=time.perf_counter();lines=recognize(image,rec,dictionary);rows.append(dict(id='en-long-full',text='\n'.join(l['text'] for l in sorted(lines,key=lambda l:(l['y'],l['x']))),lines=lines,status='OK',elapsed_ms=(time.perf_counter()-start)*1000));print(name,'full',len(lines),'regions',flush=True)
 top=0;region=0;merged=[];start=time.perf_counter()
 while True:
  bottom=min(top+2048,image.shape[0]);tile=image[top:bottom];lines=recognize(tile,rec,dictionary)
  for line in lines:
   line['edge']=max(0,min(line['y'],bottom-top-line['y']-line['height']));line['y']+=top;line['region']=region;merged.append(line)
  print(name,'strip',region,len(lines),'regions',flush=True);region+=1
  if bottom==image.shape[0]:break
  top=bottom-384
 rows.append(dict(id='en-long-strips',text='Raw overlapping lines; deduplicate geometrically on host',lines=merged,regions=region,status='OK',elapsed_ms=(time.perf_counter()-start)*1000));allrows[name]=rows;(root/'paddle-long-results.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2))
