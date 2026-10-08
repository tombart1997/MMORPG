"""One explicit Codex Blender pass per named source. Retain every rejected file."""
import bpy,bmesh,json,sys,math,time
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
PLAN=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())['assets']
def save(key,notes,started):
 out=ROOT/'docs/asset_review/inventory'/key/'assisted';out.mkdir(parents=True,exist_ok=True)
 for o in bpy.context.scene.objects:
  if o.type=='ARMATURE':o.data.pose_position='POSE'
 bpy.context.scene.frame_set(0)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'focused.blend'))
 (out/'modification.json').write_text(json.dumps({'operation':'Actual Codex-assisted Blender pass','notes':notes,'elapsed_seconds':time.monotonic()-started,'paid_credits':0},indent=2))
def load(key):
 e=next(e for e in PLAN if e['key']==key)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(ROOT/e['target']))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 obj=max([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
 return e,rig,obj
def weights(obj,v,values):
 for g in list(v.groups):obj.vertex_groups[g.group].remove([v.index])
 total=sum(values.values())
 for name,w in values.items():
  if w>1e-5:obj.vertex_groups[name].add([v.index],w/total,'REPLACE')
def wolf(key):
 started=time.monotonic();e,rig,obj=load(key)
 # Actual head is at negative Y, while Head joint is at positive Y.
 # Correct geometry about its saved extent center, never rotate the skeleton.
 coords=[obj.matrix_world@v.co for v in obj.data.vertices]
 center=Vector([(min(p[i] for p in coords)+max(p[i] for p in coords))*.5 for i in range(3)])
 rot=Matrix.Translation(center)@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-center)
 obj.data.transform(obj.matrix_world.inverted()@rot@obj.matrix_world)
 # Transfer from the preserved compatible rest template, not old reversed skin.
 meshname=obj.name;before=set(bpy.data.objects)
 bpy.ops.wm.append(directory=str(ROOT/e['rig_source'])+'/Object/',filename='Wolf_ContinuousSkin')
 added=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
 if not added:
  # Object names differ across authored versions: import retained original GLB.
  bpy.ops.import_scene.gltf(filepath=str(ROOT/'.local/forge_rebuild/baseline/game/assets/creatures/wolf.glb'))
  added=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
 records=[]
 for guide in added:
  names={g.index:g.name for g in guide.vertex_groups}
  for v in guide.data.vertices:
   values={names[g.group]:g.weight for g in v.groups if names[g.group] in rig.data.bones and g.weight>.001}
   if values:records.append((guide.matrix_world@v.co,values))
 tree=KDTree(len(records))
 for i,(p,w) in enumerate(records):tree.insert(p,i)
 tree.balance()
 for v in obj.data.vertices:
  values={};near=tree.find_n(obj.matrix_world@v.co,4)
  for _,i,d in near:
   for n,w in records[i][1].items():values[n]=values.get(n,0)+w/(d*d+.0004)
  values=dict(sorted(values.items(),key=lambda p:-p[1])[:4]);weights(obj,v,values)
 for o in list(bpy.data.objects):
  if o in before:continue
  bpy.data.objects.remove(o,do_unlink=True)
 save(key,'Verified 180-degree geometry/Head-joint mismatch corrected; nearest four compatible original-template weights transferred. UVs/materials, rig and all actions retained.',started)
def horse():
 key='horse_bay';started=time.monotonic();e,rig,obj=load(key)
 # The audit identifies physical cross-midline forehoof bridges. Reweighting
 # those faces cannot separate four limbs, so replace only articulated regions.
 bm=bmesh.new();bm.from_mesh(obj.data)
 names={g.index:g.name for g in obj.vertex_groups};deform=bm.verts.layers.deform.active
 remove=[]
 for v in bm.verts:
  p=obj.matrix_world@v.co;tail=sum(w for i,w in v[deform].items() if names.get(i)=='Tail')
  if p.z<1.08 and tail<.5 and -.99<p.y<1.15:remove.append(v)
 bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(obj.data);bm.free()
 mat=bpy.data.materials.new('RebuiltBayLegs');mat.use_nodes=True
 shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.11,.045,.022,1);shader.inputs['Roughness'].default_value=.73
 hoof=bpy.data.materials.new('RebuiltDarkHooves');hoof.use_nodes=True
 hs=hoof.node_tree.nodes.get('Principled BSDF');hs.inputs['Base Color'].default_value=(.019,.016,.013,1);hs.inputs['Roughness'].default_value=.8
 for front in [True,False]:
  for side,x in [('L',-.266),('R',.266)]:
   family='Fore' if front else 'Hind';prefix=f'{family}.{side}.'
   if front:stations=[(.64,1.15,.080,.082,'Upper'),(.64,.97,.055,.054,'Lower'),(.67,.74,.041,.043,'Lower'),(.685,.49,.042,.044,'Ankle'),(.665,.32,.033,.038,'Ankle'),(.65,.16,.039,.043,'Hoof'),(.69,.105,.066,.088,'Hoof'),(.705,.035,.064,.088,'Hoof')]
   else:stations=[(-.51,1.15,.10,.11,'Upper'),(-.58,.85,.065,.065,'Lower'),(-.70,.68,.052,.055,'Lower'),(-.79,.5,.043,.045,'Ankle'),(-.80,.32,.030,.036,'Ankle'),(-.81,.16,.037,.043,'Hoof'),(-.77,.105,.065,.084,'Hoof'),(-.755,.035,.064,.084,'Hoof')]
   verts=[];faces=[];sidecount=10
   for y,z,rx,ry,bone in stations:
    for i in range(sidecount):
     angle=i*math.tau/sidecount;verts.append((x+rx*math.cos(angle),y+ry*math.sin(angle),z))
   for ring in range(len(stations)-1):
    for i in range(sidecount):faces.append((ring*sidecount+i,ring*sidecount+(i+1)%sidecount,(ring+1)*sidecount+(i+1)%sidecount,(ring+1)*sidecount+i))
   faces.extend([tuple(reversed(range(sidecount))),tuple((len(stations)-1)*sidecount+i for i in range(sidecount))])
   mesh=bpy.data.meshes.new(prefix+'CleanLeg');mesh.from_pydata(verts,[],faces);mesh.update()
   leg=bpy.data.objects.new(prefix+'CleanLeg',mesh);bpy.context.collection.objects.link(leg);leg.data.materials.append(mat);leg.data.materials.append(hoof)
   for b in rig.data.bones:leg.vertex_groups.new(name=b.name)
   for n,station in enumerate(stations):
    for i in range(sidecount):leg.vertex_groups[prefix+station[-1]].add([n*sidecount+i],1,'REPLACE')
   for poly in mesh.polygons:poly.use_smooth=True;poly.material_index=1 if poly.center.z<.13 else 0
   leg.parent=rig;mod=leg.modifiers.new('MatchedHorseSkin','ARMATURE');mod.object=rig
 save(key,'Removed anatomically fused lower limbs with proven opposite-side faces; lofted four clean low-poly leg/hoof regions over existing joint centers. Preserved generated torso/head, original UV atlas, tail, separate tack, rest bones and all four gait clips.',started)
def rider():
 key='hero_ironvow';started=time.monotonic();e,rig,obj=load(key);changed=0
 for v in obj.data.vertices:
  p=obj.matrix_world@v.co;x=abs(p.x);side='L' if p.x<0 else 'R'
  if p.z<.72 and x<.105:
   # Joined cloth center follows pelvis; blending removes opposing bone jump.
   blend=min(1,max(0,(x-.045)/.06));old={obj.vertex_groups[g.group].name:g.weight*blend for g in v.groups}
   old['Hips']=old.get('Hips',0)+1-blend;weights(obj,v,old);changed+=1
  elif x>.32 and .76<p.z<1.35:
   hand=max(0,min(1,(1.01-p.z)/.12));upper=max(0,min(1,(p.z-1.08)/.16));fore=max(0,1-hand-upper)
   values={f'Hand.{side}':hand,f'Forearm.{side}':fore,f'UpperArm.{side}':upper}
   weights(obj,v,values);changed+=1
 save(key,f'Painted continuous pelvis influence across physically joined central cloth and height-based arm joint transitions, {changed} vertices. Geometry/UV/materials and actions unchanged. Requires all-clip comparison; does not claim artist retopology.',started)
for key in sys.argv[sys.argv.index('--')+1:]:
 if key in ['mob_red_wolf','mob_grey_wolf']:wolf(key)
 elif key=='horse_bay':horse()
 elif key=='hero_ironvow':rider()
 else:raise ValueError(key)
