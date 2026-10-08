"""Evidence-bound diagnosis, bounded attempts and immutable accepted versions."""
import copy, hashlib, json, shutil, uuid
from pathlib import Path
from .store import now, digest, atomic_json
from .backends import BACKENDS

STATUSES=('KEEP','POLISH','PARTIAL REBUILD','REGENERATE','REJECT')
OPERATIONS={
 'selective_smooth':{'stage':'blender','parameters':['object','region','protected_regions','iterations','factor','max_displacement'],'requires':'Explicit mesh-local region; boundaries and sharp features are protected.'},
 'normals_repair':{'stage':'blender','parameters':['object'],'requires':'Mesh evidence of incorrect normals, not merely a rough screenshot.'},
 'material_adjust':{'stage':'blender','parameters':['material','roughness','metallic'],'requires':'Named material and supported unlinked channels.'},
 'simplify':{'stage':'blender','parameters':['triangle_budget','max_surface_error'],'requires':'Surface and animation guards plus visual silhouette review.'},
 'rebuild_parts':{'stage':'blender','parameters':['object','template','config'],'requires':'Explicit diagnosed static regions; curated timber or fern templates only. Preserves source roof or root crown.'},
 'assisted_blender':{'stage':'assisted','parameters':['candidate_id'],'requires':'One focused saved Blender modification; never simulated by an automatic stage.'},
 'regenerate':{'stage':'generation','parameters':['backend','reference_id','reference_set_id','settings'],'requires':'Available local backend, reviewed primary image or consistent view set, supported settings; paid backends disabled.'}}


def capabilities():
    return {'statuses':STATUSES,'operations':OPERATIONS,'default_budget':{'automatic_rounds':2,'assisted_passes':1,'elapsed_seconds':360},
        'paid_regeneration':False,'model_assistance':'External Codex/Blender pass; unavailable unattended. Review remains explicit.',
        'generation_parameters':{'triposr':['mc_resolution','texture_resolution'],
        'triposg':['generation_seed','diffusion_steps','guidance_scale','shape_octree_depth'],
        'trellis':['generation_seed','trellis_steps','trellis_guidance','multiview_mode','project_reference_colors']}}


def state(asset):
    return copy.deepcopy(asset.get('reviewflow',{'status':'POLISH','diagnosis':None,'plan':[],
        'budget':capabilities()['default_budget'],'attempts':[],'versions':[],'accepted_version':None,
        'remaining_review':['Diagnosis and standardized mesh/render evidence required.']}))


def current_hash(store, asset):
    source=asset.get('artifacts',{}).get('files',{}).get('runtime.glb')
    if source:return digest(store.file(asset['id'],source))
    candidate=next((c for c in asset['candidates'] if c['id']==asset['selected_candidate']),None)
    return digest(store.file(asset['id'],candidate['path'])) if candidate else None


def validate_plan(plan):
    for op in plan:
        name=op.get('operation')
        if name not in OPERATIONS:raise ValueError('Unsupported repair operation: '+str(name))
        args=op.get('parameters',{})
        extra=set(args)-set(OPERATIONS[name]['parameters'])
        if extra:raise ValueError('Unsupported parameters: '+', '.join(sorted(extra)))
        if name=='regenerate':
            backend=args.get('backend','triposr')
            if backend not in ('triposr','triposg','trellis') or not BACKENDS[backend].capabilities()['available']:
                raise ValueError('Only available local backends can regenerate. Paid regeneration disabled.')
            if set(args.get('settings',{}))-set(capabilities()['generation_parameters'][backend]):
                raise ValueError('This backend does not support those generation settings')
        if name=='selective_smooth':
            region=args.get('region',{})
            if not args.get('object') or set(region)!= {'min','max'}:raise ValueError('Smoothing requires a named object and explicit region')
            for box in [region,*args.get('protected_regions',[])]:
                if set(box)!={'min','max'} or any(len(box[k])!=3 for k in ['min','max']):raise ValueError('Regions require min/max triples')
                if any(not isinstance(v,(float,int)) or not __import__('math').isfinite(v) for k in box for v in box[k]):raise ValueError('Region coordinates must be finite')
                if any(box['min'][i]>box['max'][i] for i in range(3)):raise ValueError('Invalid region bounds')
            if not 1<=args.get('iterations',1)<=8 or not 0<args.get('factor',.1)<=.4 or not 0<args.get('max_displacement',.01)<=.1:
                raise ValueError('Smoothing exceeds the bounded local repair limits')
        if name=='material_adjust' and (not args.get('material') or any(not 0<=args[k]<=1 for k in ['roughness','metallic'] if k in args)):
            raise ValueError('Material repair requires a named material and values in 0..1')
        if name=='normals_repair' and not args.get('object'):raise ValueError('Normals repair requires a named mesh')
        if name=='rebuild_parts':
            template=args.get('template');config=args.get('config',{})
            allowed={'timber_supports':{'cut_height','post_top'},'fern_fronds':{'fronds','pairs','spread','height'}}
            if not args.get('object') or template not in allowed or set(config)-allowed[template]:raise ValueError('Unsupported local rebuild template or parameters')
            if any(not isinstance(v,(int,float)) or not __import__('math').isfinite(v) for v in config.values()):raise ValueError('Rebuild values must be finite')
            if template=='fern_fronds' and (not 4<=config.get('fronds',12)<=16 or not 8<=config.get('pairs',16)<=24 or not .2<=config.get('spread',.55)<=1 or not .1<=config.get('height',.45)<=1):raise ValueError('Foliage rebuild exceeds bounded template limits')
            if template=='timber_supports' and (not 3<=config.get('cut_height',4.25)<=5 or not 5<=config.get('post_top',5.95)<=7):raise ValueError('Timber region exceeds template limits')
        if name=='simplify' and (not 100<=args.get('triangle_budget',0)<=2000000 or not 0<args.get('max_surface_error',.02)<=.1):raise ValueError('Invalid simplification limits')
    return plan


def save_diagnosis(store, aid, record):
    a=store.get(aid);flow=state(a)
    if record['status'] not in STATUSES:raise ValueError('Invalid actionable asset status')
    if record.get('source_sha256')!=current_hash(store,a):raise ValueError('Diagnosis must identify the exact current saved source hash')
    if not record.get('criteria') or not record.get('evidence') or not record.get('confidence'):
        raise ValueError('Diagnosis needs asset-specific criteria, evidence and confidence')
    for ev in record['evidence']:
        if ev.get('kind') not in ('mesh','render','reference','animation','runtime'):raise ValueError('Unknown evidence kind')
        if ev.get('path') and not store.file(aid,ev['path']).is_file():raise ValueError('Evidence file does not exist')
    if record.get('defects') and not any(e['kind']=='mesh' for e in record['evidence']):raise ValueError('Defect diagnosis needs mesh inspection as well as screenshots')
    plan=validate_plan(record.get('plan',[]))
    budget={**flow['budget'],**record.get('budget',{})}
    if set(budget)!= {'automatic_rounds','assisted_passes','elapsed_seconds'} or not 0<=budget['automatic_rounds']<=5 or not 0<=budget['assisted_passes']<=2 or not 1<=budget['elapsed_seconds']<=7200:raise ValueError('Invalid repair budget')
    for key in ('automatic_rounds','assisted_passes'):
        if not isinstance(budget[key],int):raise ValueError('Attempt budgets must be integers')
    flow.update(status=record['status'],diagnosis=record,plan=plan,budget=budget,remaining_review=record.get('remaining_review',[]))
    flow['diagnosed_at']=now()
    def mutate(a):
        old=state(a)
        if old['diagnosis']:
            relative='reviews/history/'+uuid.uuid4().hex[:12]+'.json';atomic_json(store.file(aid,relative),old)
        a['reviewflow']=flow
    return store.update(aid,mutate)


def begin_attempt(store, aid, assisted=False):
    a=store.get(aid);flow=state(a)
    if flow['status'] in ('KEEP','REJECT'):raise ValueError('KEEP requires no repair; REJECT is excluded from processing')
    if not flow['diagnosis'] or flow['diagnosis']['source_sha256']!=current_hash(store,a):raise ValueError('Diagnose the current source before repairing')
    if not flow['plan']:raise ValueError('No actionable repair plan')
    if any(t['state'] in ('queued','running','requires_review') for t in flow['attempts']):raise ValueError('Review the previous attempt before another round')
    kind='assisted' if assisted else 'automatic'
    if sum(t['kind']==kind for t in flow['attempts'])>=flow['budget']['assisted_passes' if assisted else 'automatic_rounds']:raise ValueError('Repair round budget reached')
    if sum(t.get('elapsed_seconds',0) for t in flow['attempts'])>=flow['budget']['elapsed_seconds']:raise ValueError('Repair time budget reached')
    fingerprint=hashlib.sha256(json.dumps(flow['plan'],sort_keys=True).encode()).hexdigest()
    if any(t['fingerprint']==fingerprint and t['state'] in ('rejected','failed','plateau') for t in flow['attempts']):raise ValueError('Change the approach after a failed or plateaued attempt')
    ops=validate_plan(flow['plan'])
    if assisted!=any(op['operation']=='assisted_blender' for op in ops):raise ValueError('Assisted pass needs an actual saved Blender candidate')
    attempt={'id':uuid.uuid4().hex[:12],'kind':kind,'state':'queued','created_at':now(),'fingerprint':fingerprint,
             'plan':ops,'source_sha256':current_hash(store,a),'cost_credits':0,'elapsed_seconds':0}
    flow['attempts'].append(attempt);store.update(aid,lambda a:a.update(reviewflow=flow));return attempt


def archive_candidate(store, aid, cid, reason):
    def mutate(a):
        candidate=next((c for c in a['candidates'] if c['id']==cid),None)
        if not candidate:raise ValueError('Unknown candidate')
        candidate.update(archived=True,archive_reason=reason,archived_at=now())
        if a['selected_candidate']==cid:
            a['selected_candidate']=None;a['artifacts']={};a['review']['status']='rejected'
        a['history'].append({'operation':'archive_candidate','candidate_id':cid,'reason':reason,'timestamp':now()})
    return store.update(aid,mutate)


def promote(store, aid, review):
    a=store.get(aid);flow=state(a)
    if flow['status']=='REJECT':raise ValueError('Rejected assets cannot be accepted or exported')
    if not flow['diagnosis'] or flow['remaining_review']:raise ValueError('Complete the remaining review requirements')
    files=a['artifacts'].get('files',{})
    if a['artifacts'].get('stale') or a['artifacts'].get('validation',{}).get('technical_status')!='passed':raise ValueError('Current technical validation must pass')
    if not a['artifacts'].get('godot',{}).get('technical',{}).get('status')=='passed':raise ValueError('Isolated Godot validation must pass before promotion')
    required=['silhouette','materials','no_regressions','gameplay_distance','integration']
    if review.get('fallback'):
        if not review.get('fallback_reason','').strip():raise ValueError('A temporary fallback requires its reference limitations and replacement reason')
    else:required.append('reference_fidelity')
    if any(not review.get('checks',{}).get(k) for k in required):raise ValueError('Complete independent visual and integration checks')
    if flow['attempts'] and flow['attempts'][-1]['state'] not in ('accepted','rejected','plateau','failed'):raise ValueError('Review the latest repair attempt')
    if not review.get('notes','').strip() or not review.get('evidence'):raise ValueError('Acceptance requires evidence and a written comparison')
    for rel in review['evidence']:
        if not store.file(aid,rel).is_file():raise ValueError('Review evidence does not exist')
    runtime=store.file(aid,files['runtime.glb']);sha=digest(runtime)
    if sha!=a['artifacts'].get('runtime_sha256'):raise ValueError('Runtime changed after validation')
    godot=a['artifacts']['godot']
    if godot.get('runtime_sha256')!=sha:raise ValueError('Godot validation belongs to a different runtime')
    vid=uuid.uuid4().hex[:12];directory=store.file(aid,'versions/'+vid);directory.mkdir(parents=True)
    # Preserve a full version manifest, textures and editable/source meshes, not
    # merely the runtime file. Artifacts remain independently retained too.
    for name,rel in files.items():
        if name.endswith(('.glb','.gltf','.bin','.blend','.png','.json')):shutil.copy2(store.file(aid,rel),directory/name)
    version={'id':vid,'created_at':now(),'sha256':sha,'runtime':'versions/'+vid+'/runtime.glb','review':review,
             'previous':flow['accepted_version'],'candidate_id':a['selected_candidate'],'artifacts':copy.deepcopy(a['artifacts'])}
    atomic_json(directory/'manifest.json',a);flow['versions'].append(version);flow['accepted_version']=vid
    def accept(a):
        a['reviewflow']=flow
        a['review'].update(status='accepted',accepted_at=now(),candidate_id=a['selected_candidate'],runtime_sha256=sha,notes=review['notes'])
    store.update(aid,accept);return version


def rollback(store, aid, vid):
    a=store.get(aid);flow=state(a);version=next((v for v in flow['versions'] if v['id']==vid),None)
    if not version:raise ValueError('Unknown accepted version')
    if digest(store.file(aid,version['runtime']))!=version['sha256']:raise ValueError('Archived version hash mismatch')
    flow['accepted_version']=vid
    def mutate(a):
        a['reviewflow']=flow;a['history'].append({'operation':'rollback','version':vid,'timestamp':now()})
    return store.update(aid,mutate)


def fail_attempt(store, aid, tid, notes, elapsed_seconds):
    """Recover interrupted output without granting another repair budget."""
    def mutate(a):
        t=next(t for t in a['reviewflow']['attempts'] if t['id']==tid)
        if t['state'] not in ('queued','running','requires_review'):return
        t.update(state='failed',notes=notes,elapsed_seconds=max(t.get('elapsed_seconds',0),elapsed_seconds),cost_credits=0)
        if 'before_artifacts' not in t:return
        t['failed_artifacts']=copy.deepcopy(a['artifacts'])
        bad=a['artifacts'].get('candidate_id')
        for c in a['candidates']:
            if c['id']==bad and bad!=t['before_candidate_id']:
                c.update(archived=True,archive_reason=notes,archived_at=now())
        a['artifacts']=copy.deepcopy(t['before_artifacts'])
        a['selected_candidate']=t['before_candidate_id']
    return store.update(aid,mutate)


def review_attempt(store, aid, tid, review):
    a=store.get(aid);flow=state(a);attempt=next((t for t in flow['attempts'] if t['id']==tid),None)
    if not attempt or attempt['state']!='requires_review':raise ValueError('Attempt is not ready for review')
    if review['decision'] not in ('accepted','rejected','plateau'):raise ValueError('Choose accepted, rejected or plateau')
    for path in review['evidence']:
        if not store.file(aid,path).is_file():raise ValueError('Before/after review evidence missing')
    if current_hash(store,a)!=attempt['result_sha256']:raise ValueError('Attempt result changed before review')
    if review['decision']=='accepted':
        if not review['improved_defects'] or review['regressions']:raise ValueError('An accepted repair must improve a defect without unacceptable regressions')
        if not all(review.get('checks',{}).get(k) for k in ('silhouette','materials','animation','integration')):raise ValueError('Complete repair comparison checks')
        if a['artifacts'].get('validation',{}).get('technical_status')!='passed':raise ValueError('Repair failed technical validation')
    attempt.update(state=review['decision'],review=review,reviewed_at=now())
    def mutate(asset):
        asset['reviewflow']=flow
        if review['decision']!='accepted':
            # Preserve rejected output and restore the complete working artifact
            # mapping immediately. No source, texture or candidate is deleted.
            attempt['rejected_artifacts']=copy.deepcopy(asset['artifacts'])
            bad=asset['artifacts'].get('candidate_id')
            for candidate in asset['candidates']:
                if candidate['id']==bad and bad!=attempt['before_candidate_id']:
                    candidate.update(archived=True,archive_reason=review['notes'],archived_at=now())
            asset['artifacts']=copy.deepcopy(attempt['before_artifacts'])
            asset['selected_candidate']=attempt['before_candidate_id']
        else:
            asset['reviewflow']['diagnosis']['source_sha256']=attempt['result_sha256']
            asset['selected_candidate']=asset['artifacts'].get('candidate_id',asset['selected_candidate'])
    return store.update(aid,mutate)
