"""Process isolated comparison candidates through the live, updated Forge API."""
import argparse,hashlib,json,time,urllib.request,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
BASE='http://127.0.0.1:8741/api'
def request(path,value=None,method=None):
 data=None if value is None else json.dumps(value).encode()
 req=urllib.request.Request(BASE+path,data,{'x-forge-request':'1','Content-Type':'application/json'},method=method)
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
def upload(aid,path,note):
 boundary=uuid.uuid4().hex
 body=(f'--{boundary}\r\nContent-Disposition: form-data; name="license_note"\r\n\r\n{note}\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
 req=urllib.request.Request(BASE+f'/assets/{aid}/import',body,{'x-forge-request':'1','Content-Type':f'multipart/form-data; boundary={boundary}'})
 with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
def main():
 p=argparse.ArgumentParser();p.add_argument('--asset',required=True);p.add_argument('--mode',choices=['simplify','balanced','retopology'],required=True);p.add_argument('--budget',type=int,required=True);p.add_argument('--normal-map',action='store_true');p.add_argument('--revision',default='');a=p.parse_args()
 original=next(e for e in json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets'] if e['key']==a.asset)
 if a.revision and not a.revision.isalnum():p.error('Revision must be alphanumeric')
 name=f'{a.asset}_{a.mode}_{a.budget}'+('_'+a.revision if a.revision else '');out=ROOT/'docs/asset_optimization/studies'/name;out.mkdir(parents=True,exist_ok=True)
 receipt=out/'receipt.json'
 if receipt.exists():
  record=json.loads(receipt.read_text());aid=record['asset_id'];job=record['job']
 else:
  source=ROOT/original['target'];source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
  asset=request('/assets',{'name':'Optimization / '+name,'preset':original['preset'],'design_requirements':'Retain source silhouette, joints, animations and material detail. Compare front/side/three-quarter in Godot before adoption.','license':'Derivative of local concept reconstruction; source asset '+original['forge_asset_id']});aid=asset['id']
  imported=upload(aid,source,'Optimization study: retained local neural derivative from '+original['forge_asset_id']+'; SHA256 '+source_hash)
  settings=asset['settings'];settings.update(optimization_mode=a.mode,triangle_budget=a.budget,texture_resolution=1024,bake_normal_map=a.normal_map,collision='none',generate_lods=False,render_preview=False)
  request(f'/assets/{aid}/settings',settings,'PUT')
  job=request(f'/assets/{aid}/jobs',{'operation':'process','reason':'Measure surface-preserving quality/performance balance in the real game.'})
  record={'name':name,'asset_id':aid,'source_key':a.asset,'source':original['target'],'source_asset_id':original['forge_asset_id'],'source_sha256':source_hash,'imported_candidate':imported['id'],'settings':settings,'job':job,'visual_status':'pending'}
  receipt.write_text(json.dumps(record,indent=2))
 print('STUDY',name,aid,job['id'],flush=True)
 end=time.monotonic()+1800;stage=''
 while time.monotonic()<end:
  job=next(j for j in request('/jobs') if j['id']==job['id'])
  if job['stage']!=stage:stage=job['stage'];print(stage,job.get('progress'),flush=True)
  if job['state'] not in ('running','queued'):break
  time.sleep(2)
 if job['state']!='succeeded':
  record['job']=job;receipt.write_text(json.dumps(record,indent=2));raise RuntimeError(job)
 asset=request(f'/assets/{aid}');files=asset['artifacts']['files'];record['artifacts']=files;record['job']=job
 for file in ['runtime.glb','optimization.json','processing.json','inspection_before.json','animation_contract.json']:
  if file in files:shutil.copy2(FORGE/'data/assets'/aid/files[file],out/file)
 dest=ROOT/'game/review_assets/optimization';dest.mkdir(parents=True,exist_ok=True);shutil.copy2(out/'runtime.glb',dest/(name+'.glb'))
 record['review_path']='res://review_assets/optimization/'+name+'.glb';receipt.write_text(json.dumps(record,indent=2));print('FINISHED',name,flush=True)
if __name__=='__main__':main()
