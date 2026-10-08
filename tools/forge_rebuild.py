"""Drive this project's reconstruction through Tom's local Asset Forge API.

The Forge retains original concept plates, prepared crops, neural checkpoints,
candidate provenance and reviewed Blender exports. This bridge never labels an
old imported mesh as a neural reconstruction.
"""
from pathlib import Path
import argparse
import json
import shutil
import struct
import time
import urllib.request
import urllib.error
import uuid

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
OUT=ROOT/'blender/forge_rebuild'
REPORTS=ROOT/'docs/forge_rebuild'
API='http://127.0.0.1:8740/api'

def request(route,data=None,method=None):
    body=None if data is None else json.dumps(data).encode('utf-8')
    req=urllib.request.Request(API+route,data=body,method=method or ('POST' if body else 'GET'),headers={'x-forge-request':'1','Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{route}: {e.code}: {e.read().decode()}') from e

def upload(route,path,fields=None):
    boundary='ForgeBridge'+uuid.uuid4().hex
    parts=[]
    for key,value in (fields or {}).items():parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    mime='image/png' if path.suffix=='.png' else 'application/octet-stream'
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+path.read_bytes()+b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    req=urllib.request.Request(API+route,data=b''.join(parts),headers={'x-forge-request':'1','Content-Type':f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.writing')
    temp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    for attempt in range(40):
        try:temp.replace(path);break
        except PermissionError:
            if attempt==39:raise
            time.sleep(.25)

def glb_info(path):
    with path.open('rb') as fh:
        magic,version,length=struct.unpack('<4sII',fh.read(12))
        n,kind=struct.unpack('<II',fh.read(8));data=json.loads(fh.read(n).decode('utf-8'))
    return {'path':path.relative_to(ROOT).as_posix(),'triangles':sum(data['accessors'][p['indices']]['count']//3 if 'indices' in p else data['accessors'][p['attributes']['POSITION']]['count']//3 for m in data.get('meshes',[]) for p in m['primitives']),
            'skins':len(data.get('skins',[])),'bones':sorted(set(data.get('nodes',[])[j].get('name','') for s in data.get('skins',[]) for j in s['joints'])),
            'clips':[a.get('name','') for a in data.get('animations',[])],'meshes':[m.get('name','') for m in data.get('meshes',[])],'materials':[m.get('name','') for m in data.get('materials',[])]}

def initialize():
    OUT.mkdir(parents=True,exist_ok=True);REPORTS.mkdir(parents=True,exist_ok=True)
    original=[glb_info(p) for p in sorted((ROOT/'game/assets').rglob('*.glb')) if 'forge_rebuild' not in p.parts]
    atomic(REPORTS/'original_model_inventory.json',{'captured_on':'2026-10-03','models':original})
    backup=ROOT/'.local/forge_rebuild/baseline'
    for group in ['game/assets','game/scripts/visuals','game/scripts/world','game/data/visuals','game/scenes/visuals']:
        source=ROOT/group;dest=backup/group
        if not dest.exists():shutil.copytree(source,dest,ignore=shutil.ignore_patterns('*.import','*.uid'))
    plan=[]
    mobs=list(__import__('csv').DictReader((ROOT/'concepts_docs/tables/mobs.csv').open(encoding='utf-8-sig')))
    for m in mobs:
        panel=int(m['art_panel']);plate=m['art_sheet']
        if plate=='bestiary_remaining_variants.png':
            rect=[(.0,.0,.25,.43),(.245,.0,.49,.43),(.49,.0,.745,.43),(.745,.0,1,.43),(.0,.37,.34,1),(.34,.39,.65,1),(.65,.38,1,1)][panel-1]
        else:
            col=(panel-1)%3;row=(panel-1)//3
            rect=(col/3,row/2,(col+1)/3,(row+1)/2)
        if m['mob_id']=='young':rect=(0,0,.325,.46)
        if m['mob_id']=='bristle_boar':rect=(0,.505,.30,.99)
        plan.append({'key':'mob_'+m['mob_id'],'category':'mob','mob_id':m['mob_id'],'family':m['family'],'name':m['name'],'preset':'humanoid' if m['family']=='bandit' else 'creature','reference':'concepts_docs/art/'+plate,'rect':list(rect),'design':m['appearance'],'backend':'triposr','rig_source':'blender/creatures/'+m['family']+'.blend' if m['family'] in ['wolf','boar','spider','stonekin','wisp'] else 'blender/characters/warden_high.blend' if m['family']=='bandit' else 'blender/characters/briarling.blend','target':'game/assets/forge_rebuild/mobs/'+m['mob_id']+'.glb'})
    plan.insert(0,{'key':'weapon_jade','category':'weapon','name':'Concept jade sword','preset':'equipment','reference':'concepts_docs/art/gear_upgrades.png','rect':[.071,.059,.159,.55],'design':'Same straight blade, compact brass guard and wrapped jade grip as the +0 concept. Fit grip pivot and physical blade length to existing equipment sockets. No baked particles.','backend':'triposr','target':'game/assets/forge_rebuild/weapons/jade.glb'})
    atomic(OUT/'plan.json',{'schema':1,'generator_workspace':str(FORGE),'user_instruction':'Use this generator and the concept art to redo every 3D model and import into this project.','original_glb_count':len(original),'assets':plan})
    print(f'Preserved {len(original)} original GLBs; prepared {len(plan)} initial reconstruction tasks.',flush=True)

def register(entry):
    if entry.get('forge_asset_id'):return
    asset=request('/assets',{'name':'Metin2Clone rebuild / '+entry['name'],'preset':entry['preset'],'design_requirements':entry['design'],'license':'Project-owned generated concept art. Local neural reconstruction; source/model provenance retained by Asset Forge.'})
    aid=entry['forge_asset_id']=asset['id']
    source=ROOT/entry['reference']
    reference=upload(f'/assets/{aid}/references',source,{'role':'primary'})
    crop=None
    if entry.get('rect'):
        from PIL import Image
        with Image.open(source) as image:w,h=image.size
        l,t,r,b=entry['rect'];crop=[int(l*w),int(t*h),max(1,int((r-l)*w)),max(1,int((b-t)*h))]
        crop[2]=min(crop[2],w-crop[0]);crop[3]=min(crop[3],h-crop[1])
    prepared=request(f'/assets/{aid}/prepare',{'reference_id':reference['id'],'crop':crop,'remove_background':False,'role':'primary'})
    entry['prepared_reference']=str(FORGE/'data/assets'/aid/prepared['path'])
    settings=asset['settings']
    settings.update({'texture_resolution':2048 if entry['category'] in ['hero','horse'] else 1024,'mc_resolution':256 if entry['category'] in ['hero','horse'] else 128,'collision':'none','render_preview':False,'generate_lods':False,'repair_degenerate':True,'recalculate_normals':False,'bypass_rigging':True})
    request(f'/assets/{aid}/settings',settings,'PUT')
    entry['status']='registered'

def enqueue(keys):
    path=OUT/'plan.json';plan=json.loads(path.read_text())
    for e in plan['assets']:
        if keys and e['key'] not in keys:continue
        if e.get('generation_job'):continue
        register(e);atomic(path,plan)
        job=request(f"/assets/{e['forge_asset_id']}/jobs",{'operation':'generate','options':{'backend':e['backend']},'reason':'User requested complete concept-art reconstruction and import into Metin2Clone.'})
        e['generation_job']=job['id'];e['status']='queued';atomic(path,plan)
        print(e['key'],e['forge_asset_id'],job['id'],flush=True)

def status():
    path=OUT/'plan.json';plan=json.loads(path.read_text());jobs={j['id']:j for j in request('/jobs')}
    counts={}
    for e in plan['assets']:
        j=jobs.get(e.get('generation_job'))
        if j:
            e['status']=j['state'];e['generation_stage']=j.get('stage');e['elapsed_seconds']=j.get('elapsed_seconds',j.get('duration_seconds',0))
            if j['state']=='succeeded':
                asset=request('/assets/'+e['forge_asset_id'])
                candidate_id=e['candidate_id'] if e.get('archived_generation_job')==e['generation_job'] else asset['selected_candidate']
                candidate=next(c for c in asset['candidates'] if c['id']==candidate_id)
                e['generated_source']=str(FORGE/'data/assets'/e['forge_asset_id']/candidate['path']);e['candidate_id']=candidate['id']
            if j['state']=='failed':e['error']=j.get('message')
        counts[e.get('status','planned')]=counts.get(e.get('status','planned'),0)+1
    atomic(path,plan);print(json.dumps(counts),flush=True)
    for e in plan['assets']:
        if e.get('status') in ('running','failed'):print(e['key'],e.get('generation_stage'),e.get('elapsed_seconds'),e.get('error','')[-700:],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['initialize','enqueue','status']);parser.add_argument('--keys',nargs='*');args=parser.parse_args()
    {'initialize':initialize,'enqueue':lambda:enqueue(args.keys),'status':status}[args.command]()
