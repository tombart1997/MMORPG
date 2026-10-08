"""Stage actual candidates for matched Godot rendering; keep game mappings intact."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
PROJECT=ROOT/'.local/multiview_benchmarks/validation'
GEN=FORGE/'data/assets/9bd5513739b9/generated/2e7a500bfc46'
RUNTIME=FORGE/'data/assets/9bd5513739b9/processed/157b9730eec0/runtime.glb'
sources={'boar_four_native':GEN/'source.glb','boar_four_projected':GEN/'projected.glb','boar_four_runtime':RUNTIME,
         'boar_current_game':ROOT/'game/assets/reviewed/ec2c860e6fb3/137a8e438ed2/runtime.glb'}
entries=[]
for key,source in sources.items():
    shutil.copy2(source,PROJECT/'assets'/f'{key}.glb')
    entries.append({'key':key,'path':f'res://assets/{key}.glb',
        'reference':str(ROOT/'concepts_docs/art/asset_turnarounds_v2/ironhide_boar/three_quarter.png'),
        'output':str(PROJECT/'results'/f'{key}.png'),
        **({'pair_with':'boar_four_native'} if key in ('boar_four_projected','boar_four_runtime') else {})})
shutil.copy2(FORGE/'godot_validation/evidence.gd',PROJECT/'evidence.gd')
(PROJECT/'request_four.json').write_text(json.dumps({'assets':entries,'report':str(PROJECT/'results/report_four.json')},indent=2),encoding='utf-8')
print(str(PROJECT))
