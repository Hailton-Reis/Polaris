from pathlib import Path
import json,math,time,os
import numpy as np,cv2,onnxruntime as ort,yaml
root=Path(__file__).parent;assets=root/'android/app/src/main/assets/cases';cases=json.loads((assets/'cases.json').read_text());opts=ort.SessionOptions();opts.intra_op_num_threads=1;opts.inter_op_num_threads=1
models=Path(os.environ.get('POLARIS_PADDLE_MODELS',str(root/'models')));det=ort.InferenceSession(str(models/'det/inference.onnx'),opts,providers=['CPUExecutionProvider'])
def order(q):
 q=sorted(q.tolist(),key=lambda p:p[0]);left=sorted(q[:2],key=lambda p:p[1]);right=sorted(q[2:],key=lambda p:p[1]);return np.array([left[0],right[0],right[1],left[1]],np.float32)
def expand(q):
 area=cv2.contourArea(q,oriented=True);per=cv2.arcLength(q,True);distance=abs(area)*1.5/per
 normals=[]
 for a,b in zip(q,np.roll(q,-1,axis=0)):
  dx,dy=b-a;length=np.hypot(dx,dy);normals.append((dy/length,-dx/length) if area>0 else (-dy/length,dx/length))
 points=[];step=2*math.acos(max(-1,min(1,1-.25/distance)))
 for i,center in enumerate(q):
  a=math.atan2(normals[i-1][1],normals[i-1][0]);b=math.atan2(normals[i][1],normals[i][0])
  if area>0:
   while b<a:b+=2*math.pi
  else:
   while b>a:b-=2*math.pi
  n=max(1,math.ceil(abs(b-a)/step))
  for j in range(n+1):angle=a+(b-a)*j/n;points.append(center+distance*np.array([math.cos(angle),math.sin(angle)]))
 return np.array(points,np.float32)
def detect(im):
 h,w=im.shape[:2];scale=min(1,960/max(h,w));nh=max(32,round(int(h*scale)/32)*32);nw=max(32,round(int(w*scale)/32)*32);x=cv2.resize(im,(nw,nh)).astype(np.float32)/255.;x=(x-np.array([.485,.456,.406],np.float32))/np.array([.229,.224,.225],np.float32);prob=det.run(None,{det.get_inputs()[0].name:x.transpose(2,0,1)[None].copy()})[0][0,0];contours,_=cv2.findContours((prob>.3).astype('uint8')*255,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE);boxes=[]
 for contour in contours[:3000]:
  rect=cv2.minAreaRect(contour)
  if min(rect[1])<3:continue
  q=order(cv2.boxPoints(rect));mask=np.zeros(prob.shape,np.uint8);cv2.fillPoly(mask,[q.astype('int32')],1)
  if cv2.mean(prob,mask)[0]<.6:continue
  exp=cv2.minAreaRect(expand(q))
  if min(exp[1])<5:continue
  q=order(cv2.boxPoints(exp));q[:,0]=np.clip(np.rint(q[:,0]*w/nw),0,w);q[:,1]=np.clip(np.rint(q[:,1]*h/nh),0,h)
  if np.linalg.norm(q[1]-q[0])<=3 or np.linalg.norm(q[3]-q[0])<=3:continue
  boxes.append(q)
 # Single-line crops: use horizontal ordering within the one known source line.
 return sorted(boxes,key=lambda q:q[:,0].min())
def crop(im,q):
 q=order(cv2.boxPoints(cv2.minAreaRect(q)));w=max(1,int(max(np.linalg.norm(q[0]-q[1]),np.linalg.norm(q[2]-q[3]))));h=max(1,int(max(np.linalg.norm(q[0]-q[3]),np.linalg.norm(q[1]-q[2]))));target=np.array([[0,0],[w,0],[w,h],[0,h]],np.float32);out=cv2.warpPerspective(im,cv2.getPerspectiveTransform(q,target),(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
 if h/w>=1.5:out=cv2.rotate(out,cv2.ROTATE_90_COUNTERCLOCKWISE)
 return out
def recognize(image,rec,dictionary):
 boxes=detect(image);lines=[]
 for box in boxes:
  im=crop(image,box);h,w=im.shape[:2];im=cv2.resize(cv2.cvtColor(im,cv2.COLOR_BGR2RGB),(min(3200,math.ceil(48*w/h)),48)).astype(np.float32)/127.5-1;out=rec.run(None,{rec.get_inputs()[0].name:im.transpose(2,0,1)[None].copy()})[0][0];indices=out.argmax(axis=-1);previous=-1;text=''
  for value in indices:
   value=int(value)
   if value and value!=previous:text+=dictionary[value]
   previous=value
  x,y=box.min(axis=0);right,bottom=box.max(axis=0)
  lines.append(dict(text=text,x=float(x),y=float(y),width=float(right-x),height=float(bottom-y)))
 return lines
if __name__=='__main__':
 allrows={}
 for name,path in [('paddle_pipeline_small',models/'rec'),('paddle_pipeline_tiny',Path(os.environ.get('POLARIS_TINY_MODELS',str(root/'tiny'))))]:
  rec=ort.InferenceSession(str(path/'inference.onnx'),opts,providers=['CPUExecutionProvider']);dictionary=['']+yaml.safe_load((path/'inference.yml').read_text())['PostProcess']['character_dict']+[' '];rows=[]
  for c in cases:
   if c['kind']=='long':continue
   image=cv2.imread(str(assets/c['file']));start=time.perf_counter();lines=recognize(image,rec,dictionary)
   row=dict(id=c['id'],text=' '.join(l['text'] for l in lines),status='OK',detected_regions=len(lines),lines=lines,elapsed_ms=(time.perf_counter()-start)*1000);rows.append(row);print(name,c['id'],row['text'],flush=True)
  allrows[name]=rows;(root/'paddle-pipeline-results.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2))
