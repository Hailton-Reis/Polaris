"""Download only the official benchmark weights; verify archive and payload hashes."""
from pathlib import Path
import hashlib,io,json,tarfile,urllib.request
root=Path(__file__).parent
base='https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/'
archives=[('PP-OCRv6_small_det_onnx_infer.tar','d218f6fbf0f1c23d2161bd6ac7f5eaa6104fa89955c09290497e31008e2618e4','models/det'),('PP-OCRv6_small_rec_onnx_infer.tar','d267ab077a44a0eedb1ea8f8c542d263f211de8e9d7a029bf9fcfff7e5a88fb1','models/rec'),('PP-OCRv6_tiny_rec_onnx_infer.tar','1e13b22717b1edd89d4cde4fda272b6c17d5b505c97c2baea99da1a3a2d54b29','tiny')]
expected={}
for f in json.loads((root/'provenance.json').read_text())['files']:
 path=f['path'];key='tiny' if '/tiny/' in path else 'models/det' if '/models/det/' in path else 'models/rec' if '/models/rec/' in path else None
 if key:expected[(key,Path(path).name)]=f['sha256']
for name,digest,target in archives:
 print('Downloading',name,flush=True)
 with urllib.request.urlopen(base+name,timeout=120) as response:raw=response.read()
 if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Archive hash mismatch: '+name)
 destination=root/target;destination.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
  for (folder,filename),file_digest in expected.items():
   if folder!=target:continue
   members=[m for m in archive.getmembers() if m.isfile() and Path(m.name).name==filename]
   if len(members)!=1:raise ValueError('Missing or ambiguous model member: '+filename)
   payload=archive.extractfile(members[0]).read()
   if hashlib.sha256(payload).hexdigest()!=file_digest:raise ValueError('Model hash mismatch: '+filename)
   (destination/filename).write_bytes(payload)
print('Verified official weights ready. No weights added to the Polaris APK.')
