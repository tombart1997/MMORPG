"""Read saved runtime sources; expose regional skin evidence without mutating them."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets']
out={}
for key in sys.argv[sys.argv.index('--')+1:]:
 e=next(e for e in plan if e['key']==key)
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/e['target']))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 rig.data.pose_position='REST';bpy.context.view_layer.update()
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 obj=max(meshes,key=lambda o:len(o.data.vertices))
 record={'source':e['target'],'object':obj.name,'bones':{b.name:{'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local)} for b in rig.data.bones},'regions':[]}
 for region in ['low_front_left','low_front_right','low_hind_left','low_hind_right']:
  front='front' in region;left='left' in region
  vertices=[v for v in obj.data.vertices if (obj.matrix_world@v.co).z<(.6 if key=='horse_bay' else .65) and ((obj.matrix_world@v.co).y>0)==front and ((obj.matrix_world@v.co).x<0)==left]
  names={g.index:g.name for g in obj.vertex_groups};influences={}
  for v in vertices:
   for g in v.groups:influences[names[g.group]]=influences.get(names[g.group],0)+g.weight
  record['regions'].append({'region':region,'vertices':len(vertices),'mean_weights':{n:round(w/max(1,len(vertices)),4) for n,w in influences.items()}})
 rig.data.pose_position='POSE'
 clip=next((a for a in bpy.data.actions if ('trot' if key=='horse_bay' else 'run') in a.name),None)
 rig.animation_data.action=clip;rig.animation_data.use_nla=False;bpy.context.scene.frame_set(int(clip.frame_range[1]*.25));bpy.context.view_layer.update()
 posed=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();bad=[]
 for f in obj.data.polygons:
  v=[obj.data.vertices[i] for i in f.vertices[:3]];p=[posed.vertices[i].co for i in f.vertices[:3]]
  area=(v[1].co-v[0].co).cross(v[2].co-v[0].co).length*.5
  after=(p[1]-p[0]).cross(p[2]-p[0]).length*.5
  if after>area*8 and after>.0002:
   bad.append({'face':f.index,'ratio':after/max(area,1e-15),'area':after,'vertices':[{'position':list(obj.matrix_world@x.co),'weights':{obj.vertex_groups[g.group].name:round(g.weight,4) for g in x.groups}} for x in v]})
 record['bad_faces']=len(bad);record['worst']=sorted(bad,key=lambda v:-v['area'])[:12];out[key]=record
 print(key,'bad faces',len(bad),flush=True)
path=ROOT/'docs/asset_review/regional_skin_probe.json';path.write_text(json.dumps(out,indent=2))
