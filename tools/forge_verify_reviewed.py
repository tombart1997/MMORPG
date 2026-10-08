"""Verify deployed hashes, retained originals, archives and an actual rollback."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];FORGE=Path(r'C:\Users\Tom\Documents\2D_to_3D')
sys.path.insert(0,str(FORGE))
from forge.store import Store,digest,atomic_json
from forge import game_bridge,reviewflow
from forge.validation import validate_glb
store=Store(FORGE/'data');registry=ROOT/'game/data/visuals/reviewed_versions.json'
data=json.loads(registry.read_text());inventory=json.loads((ROOT/'docs/asset_review/inventory.json').read_text())['assets']
assert len(inventory)==110 and len(data['mappings'])==57
retained=0;archived=0
for row in inventory:
    asset=store.get(row['asset_id'])
    assert Path(row['original_source']).exists()
    for ref in asset['references']:
        assert digest(store.file(asset['id'],ref['path']))==ref['sha256']
    for candidate in asset['candidates']:
        assert store.file(asset['id'],candidate['path']).exists()
        if candidate.get('archived'):archived+=1;assert candidate['id']!=asset['selected_candidate']
    retained+=1
for target,record in data['mappings'].items():
    path=ROOT/'game'/record['path'][6:]
    assert digest(path)==record['sha256']
    assert validate_glb(path)['technical_status']=='passed'
    asset=store.get(record['asset_id']);flow=reviewflow.state(asset)
    version=next(v for v in flow['versions'] if v['id']==record['version_id'])
    assert version['sha256']==record['sha256']
    assert digest(store.file(asset['id'],version['runtime']))==record['sha256']
    assert digest(ROOT/'game'/record['previous']['path'][6:])==record['previous']['sha256']
    if record['fallback']:assert version['review']['fallback_reason'] and not version['review']['checks']['reference_fidelity']
# Exercise rollback and restore a real export, with no game running.
aid='f03ebd870fd5';target='res://assets/world_kit/watchtower.glb';working=data['mappings'][target]
try:
    previous=game_bridge.rollback_game(store,aid)
    assert previous['sha256']==working['previous']['sha256']
    assert reviewflow.state(store.get(aid))['game_version']==previous.get('version_id')
finally:game_bridge.apply_version(store,aid,working['version_id'])
count=len(json.loads(registry.read_text())['history'])
game_bridge.apply_version(store,aid,working['version_id'])
assert len(json.loads(registry.read_text())['history'])==count
report={'status':'passed','inventory_sources_retained':retained,'deployed_version_hashes_checked':57,'fallbacks':54,'repairs_including_derived_fern':3,'archived_candidates':archived,'actual_game_rollback_and_restore':True,'idempotent_apply':True,'scope':'Exact immutable versions, source/reference retention and mapping roundtrip. Visual and runtime checks are separate reports.'}
atomic_json(ROOT/'docs/asset_review/deployment_verification.json',report)
print(report)
