import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
SOURCE=FORGE/'data/assets/9bd5513739b9/processed/595d28bcc72d/runtime.glb'
PROJECT=ROOT/'.local/multiview_benchmarks/validation'
shutil.copy2(SOURCE,PROJECT/'assets/boar_corrected_runtime.glb')
shutil.copy2(FORGE/'data/assets/9bd5513739b9/generated/2e7a500bfc46/projected_all_sides.glb',PROJECT/'assets/boar_projection_yup.glb')
request={'assets':[{'key':key,'path':'res://assets/'+key+'.glb',
    'reference':str(ROOT/'concepts_docs/art/asset_turnarounds_v2/ironhide_boar/three_quarter.png'),
    'output':str(PROJECT/'results'/f'{key}.png')}
    for key in ['boar_projection_yup','boar_corrected_runtime']],
    'report':str(PROJECT/'results/report_corrected.json')}
(PROJECT/'request_baked.json').write_text(json.dumps(request,indent=2),encoding='utf-8')
print(str(SOURCE))
GAME_DEST=ROOT/'game/review_assets/multiview_ironhide_boar'
GAME_DEST.mkdir(parents=True,exist_ok=True)
shutil.copy2(SOURCE,GAME_DEST/'runtime.glb')
