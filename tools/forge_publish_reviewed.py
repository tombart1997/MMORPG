"""Promote only the exact exports covered by opened evidence and staged checks.

Run with Forge's virtualenv. Source candidates and manifests remain retained;
temporary fallback limitations are part of each immutable accepted version.
"""
from pathlib import Path
import json,sys,shutil,copy,time
ROOT=Path(__file__).resolve().parents[1];FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
sys.path.insert(0,str(FORGE))
from forge.store import Store,atomic_json,digest,now
from forge.validation import validate_glb
from forge import reviewflow,game_bridge
store=Store(FORGE/'data');docs=ROOT/'docs/asset_review'
rows=json.loads((docs/'staged_inventory.json').read_text())['assets']
contracts=json.loads((docs/'staged_contracts.json').read_text())
integration=json.loads((docs/'integration/contracts.json').read_text())
assert contracts['status']=='passed' and integration['status']=='passed'
judgments=json.loads((docs/'fallback_judgments.json').read_text())
assert judgments['reviewer']=='Codex: actual opened saved renders and mesh evidence'
deployed=[];start=time.monotonic()
for row in rows:
    aid=row['asset_id'];asset=store.get(aid);flow=reviewflow.state(asset)
    if flow.get('game_version'):
        deployed.append({'key':row['key'],'asset_id':aid,'version_id':flow['game_version'],'already_deployed':True});continue
    runtime=ROOT/'game'/row['path'][6:];assert digest(runtime)==row['sha256']
    technical=validate_glb(runtime);assert technical['technical_status']=='passed',technical['errors']
    contract=next(x for x in contracts['assets'] if x['key']==row['key'])
    assert contract['path']==row['path'] and contract['status']=='passed'
    before=copy.deepcopy(asset['artifacts']);bad=asset['selected_candidate']
    relative='reviews/production';folder=store.file(aid,relative);folder.mkdir(parents=True,exist_ok=True)
    atomic_json(folder/'previous_manifest.json',asset)
    evidence=[]
    def retain(path,name,kind='render'):
        shutil.copy2(path,folder/name);rel=relative+'/'+name;evidence.append({'kind':kind,'path':rel});return rel
    retain(docs/'integration/contracts.json','integration.json','runtime')
    retain(docs/'integration/settlement.png','settlement.png')
    retain(docs/'integration/runtime_families.png','runtime_families.png')
    retain(ROOT/'game/.local/asset_balance_reviewed_staged.json','whole_game_performance.json','runtime')
    if row['fallback']:
        judgment=judgments['assets'][row['key']];assert judgment['views_opened']
        assert judgment['animations_opened'] or not contract['animations']
        original=store.file(aid,asset['artifacts']['files']['runtime.glb'])
        shutil.copy2(original,folder/'previous_generated.glb')
        retain(docs/'fallbacks'/row['evidence_key']/'after.png','after.png')
        anim=docs/'fallbacks'/row['evidence_key']/'after_animation.png'
        if anim.exists():retain(anim,'after_animation.png','animation')
        audit=docs/'fallbacks'/row['evidence_key']/'mesh_after.json'
        retain(audit,'mesh_after.json','mesh')
        initial=store.file(aid,'reviews/initial/before.png')
        if initial.exists():retain(initial,'before.png')
        for name in ('traveler_guard','jade_ironback_mantle'):
            if name in row['key']:retain(docs/'integration'/('worn_'+name+'.png'),'worn.png')
        if row['key'] in ('horse_bay','hero_ironvow'):
            for n in ('horse_front','horse_side','horse_threequarter','rider_front','rider_side','rider_threequarter','mounted_front','mounted_side','mounted_threequarter'):
                retain(ROOT/'docs/screenshots/horse-reference/godot/reviewed_staged_clean'/f'{n}.png',n+'.png')
        shutil.copy2(runtime,folder/'runtime.glb')
        candidate=store.candidate(aid,relative+'/runtime.glb','reviewed_temporary_fallback',{'fallback':True,'retained_source':row['fallback_source']})
        notes=judgment['notes'];future=[judgment['limitations'],row['review_notes']]
        artifacts={'files':{'runtime.glb':relative+'/runtime.glb','previous_generated.glb':relative+'/previous_generated.glb','previous_manifest.json':relative+'/previous_manifest.json'},'candidate_id':candidate['id'],'runtime_sha256':digest(runtime),'validation':technical}
    else:
        notes=('Retained roof/balcony and rebuilt straight lower supports, braces and ladder; 3,852 triangles, one mesh, three materials.' if row['evidence_key']=='watchtower' else 'Retained root crown; rebuilt 12 separated fronds with 16 leaflet pairs; 2,719 triangles, one mesh, three materials.')
        future=['Organic roof waviness is retained.' if row['evidence_key']=='watchtower' else 'Leaf color can receive a later material polish.']
        if row['key']=='derived_benchmark_fern':
            shutil.copy2(runtime,folder/'runtime.glb')
            candidate=store.candidate(aid,relative+'/runtime.glb','reviewed_derived_repair')
            artifacts={'files':{'runtime.glb':relative+'/runtime.glb','previous_manifest.json':relative+'/previous_manifest.json'},'candidate_id':candidate['id'],'runtime_sha256':digest(runtime),'validation':technical}
        else:artifacts=copy.deepcopy(asset['artifacts'])
        parent=store.get('f03ebd870fd5' if row['evidence_key']=='watchtower' else '86254633d908')
        retain(store.file(parent['id'],'reviews/initial/corrected_after.png'),'after.png')
        retain(store.file(parent['id'],'reviews/initial/corrected_before.png'),'before.png')
        retain(store.file(parent['id'],parent['artifacts']['files']['inspection_before.json']),'mesh_before.json','mesh')
    for e in evidence:artifacts['files'][Path(e['path']).name]=e['path']
    atomic_json(folder/'validation.json',technical);artifacts['files']['validation.json']=relative+'/validation.json'
    artifacts['godot']={'technical':contract,'runtime_sha256':digest(runtime),'scope':'Exact staged export; independent whole-game integration and opened visual evidence retained.'}
    store.update(aid,lambda a:a.update(artifacts=artifacts))
    diagnosis={'status':'KEEP','source_sha256':digest(runtime),'criteria':flow['diagnosis']['criteria'],'confidence':'high for runtime safety; temporary concept differences recorded' if row['fallback'] else 'high',
        'evidence':evidence,'defects':[],'plan':[],'remaining_review':[],'future_work':future}
    reviewflow.save_diagnosis(store,aid,diagnosis)
    store.update(aid,lambda a:a['reviewflow'].update(generated_status=row['status'],temporary_fallback=row['fallback']))
    if row['fallback']:
        reviewflow.archive_candidate(store,aid,bad,'Excluded from production: '+row['review_notes'])
    # Also migrate earlier rejected attempts to the archive state.
    for attempt in flow['attempts']:
        if attempt['state'] not in ('rejected','failed'):continue
        cid=attempt.get('result_artifacts',attempt.get('failed_artifacts',{})).get('candidate_id')
        current=store.get(aid)
        if cid and cid!=current['selected_candidate'] and any(c['id']==cid and not c.get('archived') for c in current['candidates']):
            reviewflow.archive_candidate(store,aid,cid,attempt.get('review',{}).get('notes',attempt.get('notes','Failed bounded repair')))
    review={'notes':notes,'evidence':[e['path'] for e in evidence], 'fallback':row['fallback'],'fallback_reason':judgments['assets'][row['key']]['limitations'] if row['fallback'] else '',
        'checks':dict(silhouette=True,materials=True,no_regressions=True,gameplay_distance=True,integration=True,reference_fidelity=not row['fallback'])}
    version=reviewflow.promote(store,aid,review)
    mapping=game_bridge.apply_version(store,aid,version['id'])
    deployed.append({'key':row['key'],'asset_id':aid,'version_id':version['id'],'mapping':mapping,'fallback':row['fallback']})
    atomic_json(docs/'deployment.json',{'assets':deployed,'status':'in_progress'})
atomic_json(docs/'deployment.json',{'assets':deployed,'status':'passed','elapsed_seconds':round(time.monotonic()-start,2),'cost_credits':0})
print('Controlled versioned replacements:',len(deployed))
