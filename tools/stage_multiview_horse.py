"""Stage native and optimized horse candidates from the API for actual Godot review."""
import json
from pathlib import Path
import shutil
import httpx

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
asset=httpx.get('http://127.0.0.1:8743/api/assets/4c42176e618f').json()
asset_root=FORGE/'data/assets'/asset['id']
PROJECT=ROOT/'.local/multiview_benchmarks/validation'
gen=asset_root/'generated/d275b177c052'
sources={'horse_native':gen/'source.glb','horse_projected':gen/'projected.glb',
    'horse_runtime':asset_root/asset['artifacts']['files']['runtime.glb']}
entries=[]
for key,source in sources.items():
    shutil.copy2(source,PROJECT/'assets'/f'{key}.glb')
    entries.append({'key':key,'path':f'res://assets/{key}.glb',
        'reference':str(ROOT/'concepts_docs/art/asset_turnarounds_v2/bay_horse/three_quarter.png'),
        'output':str(PROJECT/'results'/f'{key}.png'),
        **({'pair_with':'horse_native'} if key=='horse_projected' else {})})
(PROJECT/'request_horse.json').write_text(json.dumps({'assets':entries,'report':str(PROJECT/'results/report_horse.json')},indent=2),encoding='utf-8')
evidence=ROOT/'docs/multiview_pipeline/evidence'
for name in ['generation.json','reference_projection.json']:
    shutil.copy2(gen/name,evidence/('horse_'+name))
for name in ['optimization.json','validation.json','processing.json']:
    shutil.copy2(asset_root/asset['artifacts']['files'][name],evidence/('horse_'+name))
game_dest=ROOT/'game/review_assets/multiview_bay_horse';game_dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(sources['horse_runtime'],game_dest/'runtime.glb')
print('candidate',asset['selected_candidate'],'process',asset['artifacts']['job_id'])
