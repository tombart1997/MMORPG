"""Prepare retained previous meshes for explicit, evidence-reviewed fallback use.

Preparation alone never alters game mappings or approves a visual.
"""
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
sys.path.insert(0,str(FORGE))
from forge.store import Store,atomic_json,digest
STORE=Store(FORGE/'data')

inv=json.loads((ROOT/'docs/asset_review/inventory.json').read_text())['assets']
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets']
baseline=ROOT/'.local/forge_rebuild/baseline'
renders=json.loads((ROOT/'docs/asset_review/render_report.json').read_text())['assets']
contracts=json.loads((ROOT/'docs/asset_review/isolated_contracts.json').read_text())['assets']
requests=[];audits=[];checks=[];rows=[];seen={}
for row in inv:
    if row['status'] not in ('PARTIAL REBUILD','REGENERATE'):continue
    if row['key'] in ('watchtower','fern_reference','derived_benchmark_fern','bridge'):continue
    source=baseline/row['target'];npc=None
    if not source.exists() and '/mobs/' in row['target']:
        name={'mossling':'characters/briarling','bandit':'characters/warden_high'}.get(row['family'],'creatures/'+str(row['family']))
        source=baseline/'game/assets'/f'{name}.glb'
    if '/npcs/' in row['target']:
        source=baseline/'game/assets/characters/townfolk_kit.glb';npc=Path(row['target']).stem
    # The retained primitive wolf/boar share exaggerated horns and are less
    # faithful than already reviewed stable generated members of the species.
    if row['family'] in ('wolf','boar'):
        stable='mob_meadow_wolf' if row['family']=='wolf' else 'mob_blacktusk'
        source=ROOT/next(r['target'] for r in inv if r['key']==stable)
    if not source.exists():continue
    # Different residents select different modules/materials from the same kit.
    identity=str(source)+(':'+npc if npc else '')
    if identity in seen:
        rows.append({**row,**seen[identity]});continue
    key=row['key'];out=ROOT/'docs/asset_review/fallbacks'/key;out.mkdir(parents=True,exist_ok=True)
    relative=source.relative_to(baseline/'game') if source.is_relative_to(baseline/'game') else source.relative_to(ROOT/'game')
    dest=ROOT/'game/review_assets/fallbacks'/relative
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.copy2(source,dest)
    evidence={'fallback_source':str(source),'fallback_sha256':digest(source),'fallback_path':'res://'+dest.relative_to(ROOT/'game').as_posix(),'evidence_key':key}
    seen[identity]=evidence;rows.append({**row,**evidence})
    asset=STORE.get(row['asset_id']);ref=next(r for r in asset['references'] if r['role']=='primary')
    reference=str(STORE.file(asset['id'],ref['path']))
    before=next(r for r in renders if r['key']==row['key'])
    req={'key':key,'path':evidence['fallback_path'],'reference':reference or '', 'output':str(out/'after.png'),'framing_bounds':before['framing_bounds']}
    if npc:req['npc_id']=npc
    requests.append(req);audits.append({'key':key,'source':str(source),'output':str(out/'mesh_after.json')})
    original=next(r for r in contracts if r['key']==row['key'])
    checks.append({'key':key,'path':evidence['fallback_path'],'expected_bones':original['bones'],
        'expected_clips':original['animations']})
atomic_json(ROOT/'docs/asset_review/fallback_inventory.json',{'assets':rows})
atomic_json(ROOT/'docs/asset_review/fallback_render_request.json',{'assets':requests,'report':str(ROOT/'docs/asset_review/fallback_render_report.json')})
atomic_json(ROOT/'docs/asset_review/fallback_audit_request.json',{'assets':audits})
atomic_json(ROOT/'docs/asset_review/fallback_contract_request.json',{'assets':checks,'output':str(ROOT/'docs/asset_review/fallback_contracts.json')})
print(len(rows),'proposed mappings;',len(requests),'distinct visual reviews. Nothing deployed.')
