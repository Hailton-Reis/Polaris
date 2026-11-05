from pathlib import Path
import json,time,math,unicodedata,os
import numpy as np,cv2,onnxruntime as ort,yaml
root=Path(__file__).parent;images=root/'android/app/src/main/assets/cases';cases=json.loads((images/'cases.json').read_text());opts=ort.SessionOptions();opts.intra_op_num_threads=1;opts.inter_op_num_threads=1
results={}
for name,path in [('paddle_small',Path(os.environ.get('POLARIS_PADDLE_MODELS',str(root/'models')))/'rec'),('paddle_tiny',Path(os.environ.get('POLARIS_TINY_MODELS',str(root/'tiny'))))]:
 session=ort.InferenceSession(str(path/'inference.onnx'),opts,providers=['CPUExecutionProvider']);dictionary=['']+yaml.safe_load((path/'inference.yml').read_text())['PostProcess']['character_dict']+[' '];rows=[]
 for case in cases:
  if case['kind']=='long':continue
  image=cv2.imread(str(images/case['file']));h,w=image.shape[:2];neww=min(3200,math.ceil(48*w/h));image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB);x=cv2.resize(image,(neww,48),interpolation=cv2.INTER_LINEAR).astype(np.float32)/127.5-1.;x=x.transpose(2,0,1)[None].copy();start=time.perf_counter()
  try:
   output=session.run(None,{session.get_inputs()[0].name:x})[0][0];indices=output.argmax(axis=-1);prev=-1;text=''
   for i in indices:
    i=int(i)
    if i!=prev and i!=0:text+=dictionary[i]
    prev=i
   rows.append(dict(id=case['id'],text=text,status='OK',elapsed_ms=(time.perf_counter()-start)*1000,input_shape=list(x.shape)))
  except Exception as e:rows.append(dict(id=case['id'],status='ERROR',error=str(e)))
  print(name,case['id'],rows[-1].get('text',rows[-1].get('error')),flush=True)
 results[name]=rows;(root/'paddle-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
