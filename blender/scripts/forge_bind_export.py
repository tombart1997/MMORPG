"""Fit genuinely reconstructed Forge geometry to existing runtime rig contracts.

Keep original action data and rest bones, transfer sparse skin weights from the
editable template, preserve reconstructed UV/basecolor, and export named NLA.
Original mesh geometry is used only as a fitting/weight guide, never as output.
"""
import bpy, bmesh, json, math, sys, time
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
PLAN=ROOT/'blender/forge_rebuild/plan.json'

def save_editable(path):
 # Backups are already retained under .local; avoid Blender's locked .blend1
 # replacement on Windows and keep incomplete writes out of runtime folders.
 bpy.context.preferences.filepaths.save_version=0
 temp=ROOT/'.local/forge_rebuild/editable_writes'/path.name
 temp.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(temp))
 for attempt in range(40):
  try:temp.replace(path);break
  except PermissionError:
   if attempt==39:raise
   time.sleep(.25)

def export_runtime(path,**options):
 temp=ROOT/'.local/forge_rebuild/exports'/path.name
 temp.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.export_scene.gltf(filepath=str(temp),export_format='GLB',use_active_scene=True,**options)
 for attempt in range(40):
  try:temp.replace(path);break
  except PermissionError:
   if attempt==39:raise
   time.sleep(.25)

def bounds(objects):
 vs=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
 return Vector([min(v[i] for v in vs) for i in range(3)]),Vector([max(v[i] for v in vs) for i in range(3)])

def weights_guide(objects,rig):
 records=[]
 for o in objects:
  names={g.index:g.name for g in o.vertex_groups}
  step=max(1,len(o.data.vertices)//60000)
  for v in o.data.vertices[::step]:
   w={names[g.group]:g.weight for g in v.groups if g.weight>.001 and names[g.group] in rig.data.bones}
   if w:records.append((o.matrix_world@v.co,w))
 tree=KDTree(len(records))
 for i,(p,w) in enumerate(records):tree.insert(p,i)
 tree.balance();return tree,records

def apply_weights(o,rig,tree,records):
 o.vertex_groups.clear()
 groups={b.name:o.vertex_groups.new(name=b.name) for b in rig.data.bones}
 for v in o.data.vertices:
  p=o.matrix_world@v.co;near=tree.find_n(p,4);acc={};total=0
  for _,i,d in near:
   f=1/(d*d+.00004);total+=f
   for bone,w in records[i][1].items():acc[bone]=acc.get(bone,0)+w*f
  ranked=sorted(((n,w/total) for n,w in acc.items()),key=lambda x:-x[1])[:4]
  denom=sum(w for n,w in ranked)
  for n,w in ranked:groups[n].add([v.index],w/denom,'REPLACE')
 mod=o.modifiers.new('ConceptSkin','ARMATURE');mod.object=rig;o.parent=rig

def decimate(o,budget):
 tris=sum(len(p.vertices)-2 for p in o.data.polygons)
 if tris<=budget:return {'before':tris,'after':tris}
 high=o.copy();high.data=o.data.copy();bpy.context.collection.objects.link(high);high.name='BakeSource'
 # xatlas duplicates positions at UV seams. Weld only the runtime topology;
 # the original source's per-loop UVs stay available for the diffuse transfer.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for mesh in [o.data,high.data]:
  if mesh.has_custom_normals:mesh.normals_split_custom_set([(0,0,0)]*len(mesh.loops))
 lo,hi=bounds([o]);mod=o.modifiers.new('RuntimeBudget','DECIMATE');mod.ratio=budget/tris
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 nlo,nhi=bounds([o]);drift=max((nlo-lo).length,(nhi-hi).length)
 # Relative silhouette bounds must survive optimization. This is a coarse gate;
 # the exported Godot front/side/three-quarter review remains necessary.
 if drift>=max(.04,(hi-lo).length*.03):
  o.data=high.data.copy();bpy.data.objects.remove(high,do_unlink=True)
  return decimate(o,min(tris,int(budget*1.5)))
 # Collapsing a dense xatlas mesh merges unrelated tiny UV charts. Generate a
 # fresh runtime atlas and bake the original diffuse color onto the reduced mesh.
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=1.151917,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 atlas=bpy.data.images.new(o.name+'_RuntimeAtlas',width=1024,height=1024,alpha=False)
 material=bpy.data.materials.new(o.name+'_RuntimeColor');material.use_nodes=True
 shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.75
 texture=material.node_tree.nodes.new('ShaderNodeTexImage');texture.image=atlas
 material.node_tree.nodes.active=texture
 o.data.materials.clear();o.data.materials.append(material)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
 scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
 scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.025;scene.render.bake.max_ray_distance=.10;scene.render.bake.margin=12
 high.select_set(True);bpy.ops.object.bake(type='DIFFUSE')
 material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
 atlas.pack();bpy.data.objects.remove(high,do_unlink=True)
 return {'before':tris,'after':sum(len(p.vertices)-2 for p in o.data.polygons),'extent_drift':drift}

def bind(e):
 rig=None;old=[];keep=[];guide=None
 if e.get('rig_source'):
  bpy.ops.wm.open_mainfile(filepath=str(ROOT/e['rig_source']))
  rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(rigs)==1
  rig=rigs[0];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
  old=[o for o in bpy.context.scene.objects if o.type=='MESH']
  fit=[o for o in old if 'EliteCrown' not in o.name]
  if e['category']=='horse':
   # The separate saddle/reins/stirrups retain the reviewed rider anchor positions.
   keep=[o for o in old if any(s in o.name for s in ['Saddle','PadEdge','Stirrup','FlapStitch','Girth','Rein','Strap','BitRing','BrowBand','NoseBand'])]
   fit=[o for o in old if o.name=='Horse_ContinuousSkin']
  target_lo,target_hi=bounds(fit)
  guide=weights_guide(old,rig)
 else:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  target_lo=Vector((0,0,0));target_hi=Vector(e.get('dimensions',[.8,.8,1.2]))
  original=ROOT/'.local/forge_rebuild/baseline'/e['target']
  if original.exists() and e['category']!='weapon':
   bpy.ops.import_scene.gltf(filepath=str(original))
   target_lo,target_hi=bounds([o for o in bpy.context.scene.objects if o.type=='MESH'])
   bpy.ops.wm.read_factory_settings(use_empty=True)
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=e['generated_source'])
 parts=[o for o in bpy.data.objects if o not in before and o.type=='MESH'];assert parts
 # Apply glTF import transforms before fitting; Blender +Y is runtime -Z front.
 for o in parts:
  o.data.transform(o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
  if e['category']=='mob':
   # Concept plates contain ground paint and disconnected ornaments. Keep
   # substantive anatomy; remove only tiny isolated fragments before fitting.
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
   unseen=set(bm.verts);components=[]
   while unseen:
    todo=[unseen.pop()];component=[]
    while todo:
     v=todo.pop();component.append(v)
     for edge in v.link_edges:
      neighbor=edge.other_vert(v)
      if neighbor in unseen:unseen.remove(neighbor);todo.append(neighbor)
    components.append(component)
   largest=max(len(c) for c in components)
   remove=[v for c in components if len(c)<max(20,largest*.004) for v in c]
   bmesh.ops.delete(bm,geom=remove,context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
   if e.get('family') in ['mossling','bandit','stonekin']:
    # Remove the thin painted ground reconstructed beneath standing subjects.
    low=min(v.co.z for v in o.data.vertices);high=max(v.co.z for v in o.data.vertices)
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,low+(high-low)*.02),plane_no=(0,0,1),clear_inner=True)
    bm.to_mesh(o.data);bm.free()
 quadruped=e.get('family') in ['wolf','boar'] or e['category']=='horse'
 yaw=e.get('yaw',90 if quadruped else 0)
 if quadruped and 'yaw' not in e:
  import numpy as np
  xy=np.array([[v.co.x,v.co.y] for o in parts for v in o.data.vertices])
  _,axes=np.linalg.eigh(np.cov(xy.T));axis=axes[:,-1]
  if axis[0]<0:axis=-axis
  yaw=90-math.degrees(math.atan2(axis[1],axis[0]))
 rot=Matrix.Rotation(math.radians(yaw),4,'Z')
 for o in parts:o.data.transform(rot)
 lo,hi=bounds(parts);size=hi-lo
 if e['category']=='weapon':
  # Reconstructed reference points down. Exported equipment blade points +Y.
  rot=Matrix.Rotation(math.pi/2,4,'X')
  for o in parts:o.data.transform(rot)
  lo,hi=bounds(parts);size=hi-lo
  target_lo=Vector((-.095,-.18,-.018));target_hi=Vector((.095,1.25,.018))
 if e['category']=='horse':
  target_lo=Vector((-.40,-1.20,.005));target_hi=Vector((.40,1.73,1.98))
 elif e['category']=='hero' and not e['key'].startswith('legacy_'):
  target_lo=Vector((-.49,-.20,.006));target_hi=Vector((.49,.22,1.8994))
 elif e['category']=='mob' and e.get('family') in ['wolf','boar']:
  target_hi.z=min(target_hi.z,1.45 if e['family']=='wolf' else 1.36)
 elif e['category']=='npc':
  target_lo=Vector((-.46,-.19,.005));target_hi=Vector((.46,.21,1.82))
 target_size=target_hi-target_lo
 for o in parts:
  for v in o.data.vertices:
   v.co=Vector([(v.co[i]-lo[i])/max(.00001,size[i])*target_size[i]+target_lo[i] for i in range(3)])
  o.name='Forge_'+e['key']
  for mat in o.data.materials:
   if not mat:continue
   mat.name='Forge_'+e['key']+'_BaseColor';mat.use_nodes=True
   shader=mat.node_tree.nodes.get('Principled BSDF')
   if shader:
    shader.inputs['Roughness'].default_value=.78 if e['category'] not in ['hero','weapon'] else .48
    shader.inputs['Metallic'].default_value=.32 if e['category']=='weapon' else .08 if e['category']=='hero' else 0
 budget=e.get('triangle_budget',42000 if e['category']=='hero' else 28000 if e['category']=='horse' else 14000 if rig else 5000)
 optimize=[decimate(o,budget//len(parts)) for o in parts]
 for o in parts:
  for mat in o.data.materials:
   shader=mat.node_tree.nodes.get('Principled BSDF') if mat and mat.use_nodes else None
   if shader:
    shader.inputs['Roughness'].default_value=.48 if e['category'] in ['hero','weapon'] else .82
    shader.inputs['Metallic'].default_value=.35 if e['category']=='weapon' else 0
 if rig:
  for o in parts:apply_weights(o,rig,*guide)
 for o in old:
  if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
 # Remove cameras/lights/empties from the original modelling scene.
 for o in list(bpy.data.objects):
  if o not in parts and o not in keep and o!=rig:bpy.data.objects.remove(o,do_unlink=True)
 if rig:rig.data.pose_position='POSE'
 bpy.context.scene.render.fps=60;bpy.context.scene.frame_set(0)
 dst=ROOT/e['target'];dst.parent.mkdir(parents=True,exist_ok=True)
 editable=ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend";editable.parent.mkdir(parents=True,exist_ok=True)
 for image in bpy.data.images:
  if image.source=='FILE':
   try:image.pack()
   except RuntimeError:pass
 save_editable(editable)
 export_runtime(dst,export_yup=True,export_skins=bool(rig),export_animations=bool(rig),export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False,export_materials='EXPORT',export_extras=True)
 report={'key':e['key'],'forge_asset_id':e['forge_asset_id'],'generated_source':e['generated_source'],'rig_source':e.get('rig_source'),'export':str(dst),'editable':str(editable),'yaw':yaw,'bounds':[list(target_lo),list(target_hi)],'optimization':optimize,'bones':len(rig.data.bones) if rig else 0,'clips':[t.name for t in rig.animation_data.nla_tracks] if rig else [],'reused_original_meshes':[o.name for o in keep],'status':'exported_for_visual_review'}
 (ROOT/'docs/forge_rebuild'/f"{e['key']}.json").write_text(json.dumps(report,indent=2))
 print('FORGE_BOUND',e['key'],report['bones'],sum(p['after'] for p in optimize),flush=True)

if __name__=='__main__':
 plan=json.loads(PLAN.read_text());keys=sys.argv[sys.argv.index('--')+1:]
 for e in plan['assets']:
  if e['key'] in keys:
   if not e.get('generated_source'):
    manifest_path=Path(r'C:\Users\Tom\Documents\2D_to_3D\data\assets')/e['forge_asset_id']/'manifest.json'
    asset=json.loads(manifest_path.read_text());candidate=next(c for c in asset['candidates'] if c['id']==asset['selected_candidate'])
    e['generated_source']=str(manifest_path.parent/candidate['path'])
   bind(e)
