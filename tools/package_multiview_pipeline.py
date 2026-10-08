"""Keep the external Forge changes and evidence reviewable in the game workspace."""
import json
import hashlib
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORGE=Path('C:/Users/Tom/Documents/2D_to_3D')
DEST=ROOT/'tools/asset_generator_multiview_patch'
paths=['README.md','forge/api.py','forge/backends.py','forge/jobs.py','forge/reviewflow.py','forge/reference_sets.py',
    'web/app.js','web/index.html','web/style.css','web/multiview.js','web/dist/app.js','web/dist/app.js.map',
    'blender/optimize.py','blender/project_reference_colors.py','godot_validation/evidence.gd',
    'scripts/setup_trellis.ps1','scripts/seed_turnarounds.py','scripts/browser_multiview_validation.py',
    'backends/trellis/runner.py','backends/trellis/foreground.py','backends/trellis/test_foreground.py','backends/trellis/export_glb.py','backends/trellis/sdpa.py','backends/trellis/tensor_checks.py',
    'backends/trellis/patch_upstream.py','backends/trellis/checkpoint.py','backends/trellis/test_attention.py',
    'backends/trellis/test_export.py','backends/trellis/test_projection.py','backends/trellis/test_color_bake.py',
    'tests/test_api.py','tests/test_contracts.py','tests/test_multiview.py','tests/test_multiview_checkpoint.py']
manifest=[]
for name in paths:
    source=FORGE/name;target=DEST/name
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    manifest.append({'path':name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(DEST/'manifest.json').write_text(json.dumps({'schema':1,'created':'2026-10-07','original_forge':str(FORGE),'files':manifest},indent=2),encoding='utf-8')
EVIDENCE=ROOT/'docs/multiview_pipeline/evidence'
EVIDENCE.mkdir(parents=True,exist_ok=True)
results=ROOT/'.local/multiview_benchmarks/validation/results'
for name in ['boar_single.png','boar_multi.png','boar_current_game.png','boar_four_native.png','boar_four_runtime.png','boar_projection_yup.png','boar_corrected_runtime.png','horse_native.png','horse_projected.png','horse_runtime.png','report.json','report_four.json','report_corrected.json','report_horse.json']:
    if (results/name).exists():shutil.copy2(results/name,EVIDENCE/name)
for source in (FORGE/'data/evidence/multiview').glob('*'):
    if source.is_file():shutil.copy2(source,EVIDENCE/source.name)
gen=FORGE/'data/assets/9bd5513739b9/generated/2e7a500bfc46'
for name in ['generation.json','all_sides_provenance.json','reference_projection_all_sides.json']:
    shutil.copy2(gen/name,EVIDENCE/name)
for key in ['boar_single','boar_multi']:
    source=ROOT/'.local/multiview_benchmarks'/key/'generation.json'
    if source.exists():shutil.copy2(source,EVIDENCE/(key+'_generation.json'))
for name in ['optimization.json','validation.json','processing.json']:
    shutil.copy2(FORGE/'data/assets/9bd5513739b9/processed/595d28bcc72d'/name,EVIDENCE/('final_'+name))
for key in ['multiview_game_baseline','multiview_game_extra25','multiview_game_warm_baseline','multiview_game_grounded25']:
    for suffix in ['.json','_dense_combat.png']:
        source=ROOT/'game/.local'/('asset_balance_'+key+suffix)
        if source.exists():shutil.copy2(source,EVIDENCE/source.name)
for name in ['performance.json','technical.json','closeup.png','gameplay.png','multi_instance.png']:
    source=FORGE/'data/assets/9bd5513739b9/godot/10c1eef84a8e/results'/name
    if source.exists():shutil.copy2(source,EVIDENCE/('final_godot_'+name))
for name in ['performance.json','technical.json']:
    source=FORGE/'data/assets/4c42176e618f/godot/a01df4b2869e/results'/name
    if source.exists():shutil.copy2(source,EVIDENCE/('horse_godot_'+name))
print('Packaged',len(paths),'source files and saved evidence')
