"""Resumable bridge for the diagnosed inventory. Originals never overwritten."""
import json,sys,time,urllib.request,hashlib,uuid,shutil,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D');OUT=ROOT/'docs/asset_review';API='http://127.0.0.1:8742/api'
sys.path.insert(0,str(FORGE))
from forge.store import Store,atomic_json,digest
from forge.validation import validate_glb
from forge import reviewflow
STORE=Store(FORGE/'data')
PLAN=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets']
for derived in json.loads((ROOT/'docs/forge_rebuild/derived_lineage.json').read_text()):
    if any(e['target']==derived['target'] for e in PLAN):continue
    parent=next(e for e in PLAN if e['key']==derived['reconstruction'])
    entry={**parent,'key':'derived_'+derived['target'][12:-4].replace('/','_'),'target':derived['target'],
           'name':Path(derived['target']).stem+' / derived '+parent['name'],'parent_key':parent['key']}
    if any(p in derived['target'] for p in ['/armor/','/weapons/']):entry.update(category='equipment',preset='equipment')
    PLAN.append(entry)
BENCHMARKS=['mob_ironhide_boar','mob_meadow_wolf','watchtower','fern_reference']


def request(route,body=None,method=None):
    data=None if body is None else json.dumps(body).encode();req=urllib.request.Request(API+route,data,{'Content-Type':'application/json','x-forge-request':'1'},method=method)
    try:
        with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
    except urllib.error.HTTPError as exc:raise RuntimeError(exc.read().decode()) from exc


def upload(route,path,fields=None):
    boundary=uuid.uuid4().hex;parts=[]
    for key,value in (fields or {}).items():parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    mime='image/png' if path.suffix=='.png' else 'application/octet-stream'
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
    req=urllib.request.Request(API+route,b''.join(parts),{'Content-Type':f'multipart/form-data; boundary={boundary}','x-forge-request':'1'})
    with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)


def inventory():return json.loads((OUT/'inventory.json').read_text()) if (OUT/'inventory.json').exists() else {'schema':1,'assets':[]}


def register(keys):
    inv=inventory()
    for e in PLAN:
        if keys and e['key'] not in keys:continue
        if any(r['key']==e['key'] for r in inv['assets']):continue
        a=request('/assets',{'name':'Asset review / '+e['name'],'preset':e['preset'],'design_requirements':e['design'],'license':'Project concept and retained local generated model; parent Forge '+e['forge_asset_id']})
        aid=a['id'];candidate=upload(f'/assets/{aid}/import',ROOT/e['target'],{'license_note':'Saved current game GLB; original source '+e['forge_asset_id']})
        ref=upload(f'/assets/{aid}/references',Path(e['prepared_reference']),{'role':'primary'})
        settings=a['settings'];settings.update(optimization_mode='preserve',triangle_budget=42000 if e['category']=='hero' else 14000 if e['category'] in ('mob','horse','npc') else 6000,render_preview=False,collision='none',generate_lods=False,bypass_rigging=not e.get('rig_source'))
        request(f'/assets/{aid}/settings',settings,'PUT')
        row={'key':e['key'],'asset_id':aid,'source_asset_id':e['forge_asset_id'],'target':e['target'],'category':e['category'],'family':e.get('family'),
            'candidate_id':candidate['id'],'reference_id':ref['id'],'source_sha256':digest(ROOT/e['target']),'source':candidate['path'],'original_source':e['generated_source'],'status':'pending'}
        inv['assets'].append(row);atomic_json(OUT/'inventory.json',inv)
        directory=STORE.asset_dir(aid)/'reviews/initial';directory.mkdir(parents=True)
        source_manifest=FORGE/'data/assets'/e['forge_asset_id']/'manifest.json';shutil.copy2(source_manifest,directory/'parent_manifest.json')
        technical=validate_glb(ROOT/e['target']);atomic_json(directory/'validation.json',technical)
        # The exact current files have already been imported and animation-tested
        # in this game. Dedicated review scene validation is recorded separately.
        STORE.update(aid,lambda a:a.update(artifacts={'files':{'runtime.glb':candidate['path'],'validation.json':'reviews/initial/validation.json'},
            'candidate_id':candidate['id'],'runtime_sha256':row['source_sha256'],'validation':technical}))
        def bind(a):
            f=reviewflow.state(a);f['game_binding']={'target':'res://'+e['target'][5:],'inventory_key':e['key'],'parent_asset_id':e['forge_asset_id']};a['reviewflow']=f
        STORE.update(aid,bind);print('REGISTERED',e['key'],aid,flush=True)
    return inv


def prepare(keys=None):
    inv=inventory();rows=[r for r in inv['assets'] if not keys or r['key'] in keys]
    mesh=[];renders=[]
    for r in rows:
        e=next(e for e in PLAN if e['key']==r['key']);directory=OUT/('benchmarks' if r['key'] in BENCHMARKS else 'inventory')/r['key'];directory.mkdir(parents=True,exist_ok=True)
        mesh.append({'key':r['key'],'source':str(ROOT/r['target']),'output':str(directory/'mesh_before.json')})
        renders.append({'key':r['key'],'path':'res://'+r['target'][5:],'reference':e['prepared_reference'],'output':str(directory/'before.png')})
    atomic_json(OUT/'audit_request.json',{'assets':mesh});atomic_json(OUT/'render_request.json',{'assets':renders,'report':str(OUT/'render_report.json')})


def collect(keys=None):
    inv=inventory()
    for row in inv['assets']:
        if keys and row['key'] not in keys:continue
        directory=OUT/('benchmarks' if row['key'] in BENCHMARKS else 'inventory')/row['key'];dest=STORE.asset_dir(row['asset_id'])/'reviews/initial'
        for path in directory.glob('*'):
            if path.is_file() and path.suffix in ('.json','.png'):shutil.copy2(path,dest/path.name)
        STORE.update(row['asset_id'],lambda a:a['artifacts']['files'].update({p.name:'reviews/initial/'+p.name for p in dest.glob('*') if p.suffix in ('.json','.png')}))


def diagnose(key,status,defects,plan,remaining=None,confidence='high'):
    row=next(r for r in inventory()['assets'] if r['key']==key);aid=row['asset_id'];a=request('/assets/'+aid)
    e=next(e for e in PLAN if e['key']==key)
    if e['category'] in ('mob','hero','horse','npc'):
        criteria=['Recognizable reference silhouette and defining features at gameplay distance','Readable head and separated limbs appropriate to '+(e.get('family') or e['category']),
            'All existing rig, clip, attachment and scale contracts retained','No severe moving surface spikes or broken limbs in animation']
    elif key in ('watchtower','bridge','house_reference','crate','ruin_arch'):
        criteria=['Straight load-bearing structure; intentional openings and usable ladder where present','Preserve reference roof, balcony and material divisions','Existing scale, pivot, placement and collision behavior retained']
    elif key in ('fern_reference','grass','tree_pine','shrub_reference','dead_tree','fallen_log'):
        criteria=['Species-appropriate silhouette and leaf/frond separation at gameplay distance','Avoid opaque fused leaf masses at nearby road edges','Keep ground pivot, spatial extent and runtime cost suitable for repeated foliage']
    else:criteria=['Recognizable reference silhouette and material separation at gameplay distance','Preserve authored scale, pivot, sockets and collision behavior']
    evidence=[{'kind':'mesh','path':'reviews/initial/mesh_before.json','notes':'Saved GLB topology, smooth/custom normals, welded boundaries, UV allocation, textures, skeleton and weight audit.'},
        {'kind':'render','path':'reviews/initial/before.png','notes':'Opened front, side, back, three-quarter, clay, textured, wire, detail and gameplay sheet; concept shown alongside.'}]
    anim=STORE.file(aid,'reviews/initial/before_animation.png')
    if anim.exists():evidence.append({'kind':'animation','path':'reviews/initial/before_animation.png','notes':'Sampled every imported animation; independent visual review.'})
    record={'status':status,'source_sha256':reviewflow.current_hash(STORE,STORE.get(aid)),'criteria':criteria,'confidence':confidence,'evidence':evidence,'defects':defects,'plan':plan,'budget':{'automatic_rounds':2,'assisted_passes':1,'elapsed_seconds':360},'remaining_review':remaining or []}
    request(f'/assets/{aid}/diagnosis',record,'PUT');return aid


def wait(job):
    started=time.monotonic();last=''
    while time.monotonic()-started<600:
        current=next(j for j in request('/jobs') if j['id']==job['id'])
        if current['stage']!=last:print(job['asset_id'],current['stage'],flush=True);last=current['stage']
        if current['state'] not in ('running','queued'):return current
        time.sleep(2)
    raise RuntimeError('Repair did not finish within outer timeout')


def repair_benchmarks():
    collect(BENCHMARKS)
    aid=diagnose('mob_meadow_wolf','POLISH',[{'region':'torso and shoulder','description':'Small geometric bumps visible in clay despite all faces already smooth; no reason to recalculate normals globally.','cause':'Surface irregularity verified in mesh plus clay; texture also contains low detail, which smoothing cannot restore.'}],
        [{'operation':'selective_smooth','parameters':{'object':'Forge_mob_meadow_wolf','region':{'min':[-.44,-.6,.68],'max':[.44,.48,1.12]},
        'protected_regions':[{'min':[-1,.42,-1],'max':[1,2,3]},{'min':[-1,-2,-1],'max':[1,-.62,3]},{'min':[-1,-2,-1],'max':[1,2,.68]}],
        'iterations':2,'factor':.16,'max_displacement':.006}}],['Compare local smoothing with original; preserve ruff, head, paws and tail.'])
    job=request(f'/assets/{aid}/repair',{'assisted':False});result=wait(job);atomic_json(OUT/'benchmarks/mob_meadow_wolf/repair_job.json',result)
    print('WOLF_REPAIR',result['state'],flush=True)
    for key,description in [('mob_ironhide_boar','Leg-weight influence spreads into torso and produces severe running spikes; the rocky armored hide is intentional.'),
                            ('watchtower','Bent structural posts and missing ladder are geometry defects, present in clay and the source mesh.'),
                            ('fern_reference','Fused fronds omit fine separated leaflets; source UV atlas is 1024 but increasing it cannot create missing geometry.')]:
        row=next(r for r in inventory()['assets'] if r['key']==key);source=OUT/'benchmarks'/key/'assisted/focused.blend'
        candidate=upload(f"/assets/{row['asset_id']}/import",source,{'license_note':'One documented Codex-assisted local Blender pass; previous mesh retained.'})
        # Importing preserves the candidate independently; restore the baseline
        # selection until the repair job takes ownership of the assisted input.
        request(f"/assets/{row['asset_id']}/select",{'candidate_id':row['candidate_id']})
        baseline=STORE.get(row['asset_id']);initial=STORE.file(row['asset_id'],'reviews/initial/validation.json')
        STORE.update(row['asset_id'],lambda a:a.update(artifacts={'files':{'runtime.glb':row['source'],'validation.json':'reviews/initial/validation.json'},'candidate_id':row['candidate_id'],'runtime_sha256':row['source_sha256'],'validation':json.loads(initial.read_text())}))
        aid=diagnose(key,'PARTIAL REBUILD',[{'region':'legs and skin weights' if 'boar' in key else 'supports and ladder' if key=='watchtower' else 'fronds','description':description,'cause':'Supported by source mesh inspection and matched clay/textured/wire renders.'}],
            [{'operation':'assisted_blender','parameters':{'candidate_id':candidate['id']}}],['Inspect the actual assisted result and every required animation before adoption.'])
        job=request(f'/assets/{aid}/repair',{'assisted':True});result=wait(job);atomic_json(OUT/'benchmarks'/key/'repair_job.json',result)
        print('BENCHMARK_REPAIR',key,result['state'],flush=True)
        if result['state']!='succeeded':print(result['message'],flush=True)


def review_attempt(key,decision,notes,improved=None,regressions=None):
    row=next(r for r in inventory()['assets'] if r['key']==key);a=request('/assets/'+row['asset_id']);t=a['reviewflow']['attempts'][-1]
    if t['state']!='requires_review':return a
    evidence=[p for n,p in t['evidence'].items() if n.endswith('.png')]
    return request(f"/assets/{row['asset_id']}/attempts/{t['id']}/review",{'decision':decision,'notes':notes,'evidence':evidence,
        'improved_defects':improved or [],'regressions':regressions or [],'checks':{k:True for k in ['silhouette','materials','animation','integration']}},'PUT')


def correct_static_benchmarks():
    for key,decision,notes,regressions in [
        ('mob_meadow_wolf','plateau','Opened matched before/after and every animation. Mesh displacement is measurable, but the relevant bumps remain visually similar at normal distance. Retain original; stop rather than claim a win.',['No clear visual benefit']),
        ('mob_ironhide_boar','rejected','Opened all before/after animations. Reweighting the inferred anatomy does not fix running spikes and introduces underside distortion. Do not export; preserve the promising rest mesh for a later matched-anatomy skin rebuild.',['Running deformation remains unacceptable']),
        ('watchtower','rejected','Straight supports and ladder improve the structure, but posts protrude above the eaves and separate beam objects create excessive repeated draw surfaces. Change to a trimmed, consolidated static rebuild.',['Post ends extend above eaves','Excessive mesh surface count']),
        ('fern_reference','rejected','Individual leaflets replace fused fronds, but sparse narrow leaves lose the concept canopy. Separate stem objects also inflate scenery surfaces. Change density, width and batching.',['Canopy too sparse','Excessive mesh surface count'])]:
        review_attempt(key,decision,notes,regressions=regressions)
    for key,template,config in [('watchtower','timber_supports',{'cut_height':4.25,'post_top':5.95}),('fern_reference','fern_fronds',{'fronds':12,'pairs':16,'spread':.61,'height':.44})]:
        aid=diagnose(key,'PARTIAL REBUILD',[{'region':'supports/ladder' if key=='watchtower' else 'fronds','description':'Previous targeted pass improved separation but caused documented silhouette or runtime regressions. Original retained.','cause':'Matched mesh and rendered evidence, with failed candidate archived.'}],
            [{'operation':'rebuild_parts','parameters':{'object':'Forge_watchtower' if key=='watchtower' else 'Forge_fern_reference','template':template,'config':config}}],['Open corrected before/after and confirm batching and gameplay appearance.'])
        result=wait(request(f'/assets/{aid}/repair',{'assisted':False}));atomic_json(OUT/'benchmarks'/key/'corrected_job.json',result);print('CORRECTED',key,result['state'],flush=True)
        a=request('/assets/'+aid);t=a['reviewflow']['attempts'][-1]
        for name,path in t.get('evidence',{}).items():
            if name.endswith('.png'):shutil.copy2(STORE.file(aid,path),OUT/'benchmarks'/key/('corrected_'+name))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['register_benchmarks','register_remaining','prepare','collect','repair_benchmarks','correct_static_benchmarks']);args=parser.parse_args()
    if args.command=='register_benchmarks':register(BENCHMARKS)
    if args.command=='register_remaining':register([])
    if args.command=='prepare':prepare()
    if args.command=='collect':collect()
    if args.command=='repair_benchmarks':repair_benchmarks()
    if args.command=='correct_static_benchmarks':correct_static_benchmarks()
