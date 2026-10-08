import bpy,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];records={}
for key in sys.argv[sys.argv.index('--')+1:]:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/forge_rebuild/editable'/f'{key}.blend'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 track=next(t for t in rig.animation_data.nla_tracks if t.name=='run')
 rig.animation_data.use_nla=False;rig.animation_data.action=track.strips[0].action
 bpy.context.scene.frame_set(15);bpy.context.view_layer.update()
 object=next(o for o in bpy.context.scene.objects if o.type=='MESH');posed=object.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
 out=[]
 for f in object.data.polygons:
  vs=[object.data.vertices[i] for i in f.vertices];pv=[posed.vertices[i].co for i in f.vertices]
  before=(vs[1].co-vs[0].co).cross(vs[2].co-vs[0].co).length/2;after=(pv[1]-pv[0]).cross(pv[2]-pv[0]).length/2
  ratio=after/max(1e-15,before)
  if ratio>8 and after>.00002:out.append({'face':f.index,'before':before,'after':after,'ratio':ratio,'z':f.center.z,'positions':[list(v.co) for v in vs],'weights':[{object.vertex_groups[g.group].name:round(g.weight,3) for g in v.groups} for v in vs]})
 out.sort(key=lambda x:-x['after']);records[key]={'bad_faces':len(out),'worst':out[:10]}
 print(key,len(out),flush=True)
(ROOT/'docs/forge_rebuild/deformation_probe.json').write_text(json.dumps(records,indent=2))
