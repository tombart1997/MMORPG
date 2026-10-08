"""Clean reconstructed silhouettes and restore presentation node contracts."""
import bpy,bmesh,math,json,importlib.util,sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).with_name('forge_bind_export.py'))
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())

def save(e):
 bridge.save_editable(ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend")
 bridge.export_runtime(ROOT/e['target'],export_skins=bool(e.get('rig_source')),export_animations=bool(e.get('rig_source')),export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_extras=True)

def clean(e):
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend"))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
 lo,hi=bridge.bounds(parts);removed=0
 for o in parts:
  bm=bmesh.new();bm.from_mesh(o.data);before=len(bm.verts)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
  unseen=set(bm.verts);components=[]
  while unseen:
   todo=[unseen.pop()];comp=[]
   while todo:
    v=todo.pop();comp.append(v)
    for edge in v.link_edges:
     n=edge.other_vert(v)
     if n in unseen:unseen.remove(n);todo.append(n)
   components.append(comp)
  largest=max(map(len,components))
  discard=[v for comp in components if len(comp)<max(12,largest*.003) or (e.get('family')=='spider' and max(v.co.z for v in comp)<lo.z+(hi.z-lo.z)*.23) for v in comp]
  bmesh.ops.delete(bm,geom=discard,context='VERTS')
  if e.get('family') in ['mossling','bandit','stonekin']:
   trim=.05 if e['key'] in ['mob_grown','mob_ironback'] else .023
   bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,lo.z+(hi.z-lo.z)*trim),plane_no=(0,0,1),clear_inner=True)
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));removed+=before-len(bm.verts)
  bm.to_mesh(o.data);bm.free()
  if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
  for face in o.data.polygons:face.use_smooth=True
 nlo,nhi=bridge.bounds(parts)
 for o in parts:
  for v in o.data.vertices:
   v.co.z=(v.co.z-nlo.z)/max(.0001,nhi.z-nlo.z)*(hi.z-lo.z)+lo.z
  if e.get('family')=='wisp':
   for mat in o.data.materials:
    shader=mat.node_tree.nodes.get('Principled BSDF')
    tex=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'),None)
    if shader and tex:
     mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Emission Color']);shader.inputs['Emission Strength'].default_value=.4
 rig.data.pose_position='POSE';save(e)
 report=ROOT/'docs/forge_rebuild'/f"{e['key']}.json";data=json.loads(report.read_text());data['silhouette_cleanup']={'removed_vertices':removed,'painted_ground_trim':e.get('family') in ['mossling','bandit','stonekin']};report.write_text(json.dumps(data,indent=2))
 print('FORGE_CLEAN',e['key'],removed,flush=True)

def tack(e):
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend"))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 body=next(o for o in bpy.context.scene.objects if o.name.startswith('Forge_horse'))
 head=[body.matrix_world@v.co for v in body.data.vertices if v.co.y>.85 and v.co.z>1.42]
 tree=KDTree(len(head))
 for i,p in enumerate(head):tree.insert(p,i)
 tree.balance();changed=0
 for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and o!=body]:
  headgear=any(s in o.name for s in ['BitRing','BrowBand','NoseBand','CheekStrap'])
  rein='Rein' in o.name
  if not (headgear or rein):continue
  inverse=o.matrix_world.inverted()
  for v in o.data.vertices:
   p=o.matrix_world@v.co
   if headgear or (rein and p.y>.85):
    nearest,index,distance=tree.find(p)
    normal=(p-nearest).normalized() if distance>.00001 else Vector((1 if p.x>0 else -1,0,0))
    v.co=inverse@(nearest+normal*.018);changed+=1
 # Build continuous hanging reins from the fitted mouth to the retained grip.
 # The endpoints keep their Head/Body blend, and the hand anchor stays fixed.
 old_reins=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Rein')]
 material=old_reins[0].data.materials[0]
 for o in old_reins:bpy.data.objects.remove(o,do_unlink=True)
 for side in [-1,1]:
  mouth=tree.find(Vector((side*.11,1.66,1.60)))[0]+Vector((side*.018,0,0))
  path=[mouth,Vector((side*.18,1.15,1.48)),Vector((side*.20,.80,1.59)),Vector((-.04,.44,1.75)),Vector((-.15,.22,1.83))]
  verts=[];faces=[];count=8
  for i,p in enumerate(path):
   tangent=(path[min(i+1,len(path)-1)]-path[max(i-1,0)]).normalized()
   u=tangent.cross(Vector((0,0,1))).normalized();v=tangent.cross(u).normalized()
   for j in range(count):verts.append(p+.005*(u*math.cos(j*math.tau/count)+v*math.sin(j*math.tau/count)))
  for i in range(len(path)-1):
   for j in range(count):faces.append((i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j))
  mesh=bpy.data.meshes.new('FittedReinMesh');mesh.from_pydata(verts,[],faces);mesh.materials.append(material)
  o=bpy.data.objects.new('ReinFitted_'+str(side),mesh);bpy.context.collection.objects.link(o);o.parent=rig
  groups={name:o.vertex_groups.new(name=name) for name in ['Head','Body']}
  for i in range(len(path)):
   weight=max(0,1-i/2)
   if weight:groups['Head'].add(list(range(i*count,(i+1)*count)),weight,'REPLACE')
   if weight<1:groups['Body'].add(list(range(i*count,(i+1)*count)),1-weight,'REPLACE')
  mod=o.modifiers.new('ConceptTackSkin','ARMATURE');mod.object=rig
 rig.data.pose_position='POSE';save(e)
 print('FORGE_TACK',changed,flush=True)

def fracture(e):
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend"))
 source=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 lo,hi=bridge.bounds([source]);size=hi-lo;center=(lo+hi)*.5
 def region(p):
  # Runtime needs individually movable ribs and a separately pulsing core.
  if abs(p.x-center.x)<size.x*.12 and abs(p.y-center.y)<size.y*.18 and .25<(p.z-lo.z)/size.z<.84:return 'Core_0'
  return 'Rib_'+str(int(((math.atan2(p.y-center.y,p.x-center.x)-.18)%(math.tau))/math.tau*7)%7)
 labels={p.index:region(p.center) for p in source.data.polygons}
 made=[]
 for name in ['Core_0']+['Rib_'+str(i) for i in range(7)]:
  o=source.copy();o.data=source.data.copy();bpy.context.collection.objects.link(o);o.name=name;o.data.name=name+'Mesh'
  bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table()
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if labels[f.index]!=name],context='FACES')
  bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free()
  assert o.data.polygons,(name,'empty fracture region')
  made.append(o)
 bpy.data.objects.remove(source,do_unlink=True);save(e)
 print('FORGE_FRACTURE',[(o.name,len(o.data.polygons)) for o in made],flush=True)

keys=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for e in plan['assets']:
 if keys and e['key'] not in keys:continue
 if e['category']=='mob':clean(e)
 elif e['category']=='horse':tack(e)
 elif e['key']=='fracture':fracture(e)
