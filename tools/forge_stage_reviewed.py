"""Stage reviewed exports without altering the game's active registry."""
from pathlib import Path
import json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
sys.path.insert(0,str(FORGE))
from forge.store import Store,atomic_json,digest
store=Store(FORGE/'data')
inventory=json.loads((ROOT/'docs/asset_review/inventory.json').read_text())['assets']
fallbacks=json.loads((ROOT/'docs/asset_review/fallback_inventory.json').read_text())['assets']
rows=[];mappings={}
for row in fallbacks:
    assert digest(ROOT/'game'/row['fallback_path'][6:])==row['fallback_sha256']
    target='res://'+row['target'].removeprefix('game/')
    record={'path':row['fallback_path'],'sha256':row['fallback_sha256'],'fallback':True,'asset_id':row['asset_id']}
    mappings[target]=record;rows.append({**row,**record})
for key,parent_key in [('watchtower','watchtower'),('fern_reference','fern_reference'),('derived_benchmark_fern','fern_reference')]:
    row=next(x for x in inventory if x['key']==key)
    parent=next(x for x in inventory if x['key']==parent_key)
    asset=store.get(parent['asset_id'])
    src=store.file(asset['id'],asset['artifacts']['files']['runtime.glb'])
    dest=ROOT/'game/review_assets/accepted'/f'{key}.glb';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    record={'path':'res://'+dest.relative_to(ROOT/'game').as_posix(),'sha256':digest(dest),'fallback':False,'asset_id':row['asset_id']}
    mappings['res://'+row['target'].removeprefix('game/')]=record
    rows.append({**row,**record,'evidence_key':parent_key})
atomic_json(ROOT/'game/review_assets/staged_mappings.json',{'mappings':mappings})
atomic_json(ROOT/'docs/asset_review/staged_inventory.json',{'assets':rows})
atomic_json(ROOT/'docs/asset_review/staged_contract_request.json',{'assets':[{'key':r['key'],'path':r['path']} for r in rows], 'output':str(ROOT/'docs/asset_review/staged_contracts.json')})
print(f'Staged {len(rows)} exports; production registry unchanged.')
