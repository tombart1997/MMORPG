from pathlib import Path
import json, shutil
root=Path(__file__).resolve().parents[1]
plan=json.loads((root/'blender/forge_rebuild/plan.json').read_text())
assets=[]
for e in plan['assets']:
    if not e.get('generated_source'):continue
    dst=root/'game/assets/forge_rebuild/raw'/f"{e['key']}.glb"
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(e['generated_source'],dst)
    assets.append({'name':e['name'],'path':'res://'+dst.relative_to(root/'game').as_posix()})
(root/'docs/forge_rebuild/initial_gallery.json').write_text(json.dumps({'assets':assets,'output':str(root/'docs/forge_rebuild/initial_gallery.png')}))
