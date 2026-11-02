from pathlib import Path
import cv2,numpy as np,onnxruntime as ort,json,time,os
root=Path(__file__).parent;image=cv2.imread(str(root/'android/app/src/main/assets/cases/long.png'));opts=ort.SessionOptions();opts.intra_op_num_threads=1;opts.inter_op_num_threads=1
session=ort.InferenceSession(str(Path(os.environ.get('POLARIS_PADDLE_MODELS',str(root/'models')))/'det/inference.onnx'),opts,providers=['CPUExecutionProvider'])
def detect(im):
 h,w=im.shape[:2];ratio=min(1,960/max(h,w));nh=max(32,round(int(h*ratio)/32)*32);nw=max(32,round(int(w*ratio)/32)*32)
 x=cv2.resize(im,(nw,nh)).astype(np.float32)/255.;x=(x-np.array([.485,.456,.406],np.float32))/np.array([.229,.224,.225],np.float32);x=x.transpose(2,0,1)[None].copy();start=time.perf_counter();out=session.run(None,{session.get_inputs()[0].name:x})[0][0,0];contours,_=cv2.findContours((out>.3).astype('uint8')*255,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE);boxes=[]
 for contour in contours[:3000]:
  rect=cv2.minAreaRect(contour)
  if min(rect[1])<3:continue
  points=cv2.boxPoints(rect);mask=np.zeros(out.shape,np.uint8);cv2.fillPoly(mask,[np.round(points).astype('int32')],1);score=cv2.mean(out,mask)[0]
  if score<.6:continue
  boxes.append(dict(x=float(points[:,0].min()*w/nw),y=float(points[:,1].min()*h/nh),width=float(np.ptp(points[:,0])*w/nw),height=float(np.ptp(points[:,1])*h/nh),score=float(score)))
 return dict(input_shape=list(x.shape),boxes=boxes,elapsed_ms=(time.perf_counter()-start)*1000)
whole=detect(image);rows=[];top=0
while True:
 bottom=min(top+2048,image.shape[0]);row=detect(image[top:bottom]);row['top']=top;rows.append(row)
 if bottom==image.shape[0]:break
 top=bottom-384
r=dict(engine='PP-OCRv6_small_det, actual bundled ONNX',scope='Detector only; pre-unclip accepted boxes, desktop transcription of SDK preprocessing/thresholds; not Android runtime',whole=whole,strips=rows)
(root/'long-detector-results.json').write_text(json.dumps(r,indent=2));print('whole',whole['input_shape'],len(whole['boxes']),'strips',len(rows),'raw boxes',sum(len(r['boxes']) for r in rows))
