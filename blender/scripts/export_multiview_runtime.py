"""Re-export reviewed final authoring scenes without neural inference."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
request=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
for record in request['models']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/record['source']))
    animated=any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
    target=ROOT/record['target'];target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_yup=True,
        export_skins=animated,export_animations=animated,export_animation_mode='NLA_TRACKS',
        export_force_sampling=True,export_frame_range=False,export_extras=True)
    print('RUNTIME_EXPORT',record['target'],flush=True)
