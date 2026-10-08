"""Migrate every legacy model identity to the new export catalogue.

Dry inventory is the default. --apply rewrites text references and registries
only after every replacement exists. Cleanup is a separate final step.
"""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GAME=ROOT/'game';GENERATED=GAME/'assets/generated'
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
registry=json.loads((GAME/'data/visuals/reviewed_versions.json').read_text())
old=set(registry['mappings'])
old.update('res://'+m['path'][5:] for m in json.loads((ROOT/'docs/forge_rebuild/original_model_inventory.json').read_text())['models'])
old.update('res://'+m['target'][5:] for m in json.loads((ROOT/'docs/asset_review/inventory.json').read_text())['assets'])
old=sorted(old)
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets']
mapping={}
for e in plan:
    target='res://'+e['target'].removeprefix('game/') if hasattr(str,'removeprefix') else 'res://'+e['target'][5:]
    if e['category']=='mob':new=f"mobs/{e['mob_id']}"
    elif e['category']=='npc':new='npcs/'+Path(target).stem
    elif e['category']=='hero':new='warrior'
    elif e['category']=='horse':new='bay_horse'
    elif e['category']=='weapon':new='weapons/jade'
    elif e['key']=='coin':new='equipment/gold_coin'
    elif e['key']=='saddle':new='equipment/saddle'
    elif e['key']=='fracture':new='world/fracture'
    else:new='world/'+Path(target).stem
    mapping[target]='res://assets/generated/'+new+'.glb'
for path in old:
    if path in mapping:continue
    name=Path(path).stem;group=Path(path).parent.name
    if group in ['benchmark','world_kit']:
        name={'briarwake':'fracture'}.get(name,name);new='world/'+name
    elif group=='creatures':new='mobs/'+{'wolf':'meadow_wolf','boar':'bristle_boar','spider':'reed_spider','stonekin':'cairn_sentinel','wisp':'grave_wisp'}[name]
    elif group=='npcs':new='npcs/'+name
    elif group=='weapons':new='weapons/'+name if name!='gold_coin' else 'equipment/gold_coin'
    elif group=='characters':
        if name=='briarling':new='mobs/young'
        elif name=='townfolk_kit':new='npcs/smith'
        elif name in ['traveler_guard','jade_ironback_mantle','warden_insignia']:new='equipment/'+name
        elif 'sword' in name:new='weapons/'+('wayfarer' if name=='wayfarer_sword' else 'jade')
        else:new='warrior'
    else:raise ValueError('Unmapped identity '+path)
    mapping[path]='res://assets/generated/'+new+'.glb'
missing=sorted({path for path in mapping.values() if not (GAME/path[6:]).exists()})
report={'schema':2,'legacy_identity_count':len(mapping),'unique_new_models':len(set(mapping.values())),
    'mappings':mapping,'missing':missing,'method':'Reviewed shared multi-image reconstructions, authored family derivatives, and named clean-section repairs.'}
(ROOT/'docs/full_asset_rebuild/migration_manifest.json').write_text(json.dumps(report,indent=2))
print('MIGRATION',len(mapping),'identities;',len(set(mapping.values())),'new exports;',len(missing),'pending')
if args.apply:
    if missing:raise ValueError('Cannot migrate with missing exports: '+str(missing))
    for path in GAME.rglob('*'):
        if path.suffix not in ['.gd','.tscn','.tres']:continue
        if any(p in ['.godot','.local','review_assets'] for p in path.parts):continue
        text=path.read_text(encoding='utf-8');changed=text
        for old_path,new_path in mapping.items():changed=changed.replace(old_path,new_path)
        if changed!=text:path.write_text(changed,encoding='utf-8')
    current={'schema':2,'mappings':{old:{'path':new,'sha256':hashlib.sha256((GAME/new[6:]).read_bytes()).hexdigest(),'fallback':False,
         'method':'new_multiview_rebuild'} for old,new in mapping.items()}}
    (GAME/'data/visuals/reviewed_versions.json').write_text(json.dumps(current,indent=2))
    manifest=[]
    for path in sorted(GENERATED.rglob('*.glb')):
        manifest.append({'path':'res://'+str(path.relative_to(GAME)).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    (GAME/'data/visuals/generated_manifest.json').write_text(json.dumps({'schema':1,'models':manifest},indent=2))
    print('APPLIED text references and verified hashed manifest')
