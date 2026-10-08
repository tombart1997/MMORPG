import bpy,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2]
plan=json.loads((root/'blender/forge_rebuild/plan.json').read_text())
out={}
for key in sys.argv[sys.argv.index('--')+1:]:
 e=next(e for e in plan['assets'] if e['key']==key)
 data={}
 if e.get('rig_source'):
  bpy.ops.wm.open_mainfile(filepath=str(root/e['rig_source']))
  rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
  rig=rigs[0];rig.data.pose_position='REST'
  data['bones']={b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones}
  data['rest_frame']=bpy.context.scene.frame_current
  data['clips']=[t.name for t in rig.animation_data.nla_tracks]
  data['parts']=[o.name for o in bpy.context.scene.objects if o.type=='MESH']
  vs=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices]
  data['target_bounds']=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
 bpy.ops.wm.read_factory_settings(use_empty=True)
 if e.get('generated_source'):
  bpy.ops.import_scene.gltf(filepath=e['generated_source'])
  vs=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices]
  data['generated_bounds']=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
 out[key]=data
(root/'docs/forge_rebuild/rig_inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
