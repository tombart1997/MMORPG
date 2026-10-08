"""Constrain limb ownership and remove painted geometry bridging feet."""
import bpy,bmesh,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).with_name('forge_bind_export.py'))
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
plan=json.loads((ROOT/'blender/forge_rebuild/plan.json').read_text())
for e in plan['assets']:
 if e['category']!='mob' or e['family'] in ['wisp','spider']:continue
 # Use the retained fitted source before this refinement, making repeated
 # inspection corrections reproducible rather than accumulating trim/weights.
 forge_dir=Path(r'C:\Users\Tom\Documents\2D_to_3D\data\assets')/e['forge_asset_id']
 manifest=json.loads((forge_dir/'manifest.json').read_text())
 basis=next((c for c in manifest['candidates'] if c['id']==e.get('skin_basis_editable_candidate')),None)
 if not basis:basis=next(c for c in reversed(manifest['candidates']) if c.get('origin')=='imported' and c.get('original_filename')==e['key']+'.blend')
 bpy.ops.wm.open_mainfile(filepath=str(forge_dir/basis['path']))
 e['skin_basis_editable_candidate']=basis['id']
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 quad=e['family'] in ['wolf','boar'];changed=0;removed=0
 for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
  lo,hi=bridge.bounds([o]);height=hi.z-lo.z
  if not quad:
   bm=bmesh.new();bm.from_mesh(o.data)
   # Floor connecting left and right foot regions stretches into a sheet when
   # they move independently. Remove only the low central bridge.
   discard=[f for f in bm.faces if f.calc_center_median().z<max(lo.z+height*.14,.44) and abs(f.calc_center_median().x)<(hi.x-lo.x)*.045]
   removed+=len(discard);bmesh.ops.delete(bm,geom=discard,context='FACES')
   bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
   bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  groups={g.name:g for g in o.vertex_groups}
  owners={};centroids={}
  if quad:
   # Assign an entire connected calf to one limb. A turned reference often
   # puts a complete leg across x=0, so signing each vertex tears that leg.
   eligible={v.index for v in o.data.vertices if v.co.z<.44}
   adjacency={i:[] for i in eligible}
   for edge in o.data.edges:
    a,b=edge.vertices
    if a in eligible and b in eligible:adjacency[a].append(b);adjacency[b].append(a)
   components=[]
   while eligible:
    todo=[eligible.pop()];comp=[]
    while todo:
     i=todo.pop();comp.append(i)
     for n in adjacency[i]:
      if n in eligible:eligible.remove(n);todo.append(n)
    if len(comp)>8:
     from mathutils import Vector
     center=sum((o.data.vertices[i].co for i in comp),Vector())/len(comp)
     components.append((comp,center))
   for station in ['Front','Hind']:
    subset=[(comp,c) for comp,c in components if (c.y>-.03)==(station=='Front') and c.y>-.85]
    subset.sort(key=lambda x:x[1].x)
    for index,(comp,c) in enumerate(subset):
     side='L' if index==0 else 'R';tag=station+'.'+side;centroids[tag]=c
     for i in comp:owners[i]=tag
   for comp,c in components:
    if c.y<-.92:
     for i in comp:owners[i]='Tail'
  for v in o.data.vertices:
   p=v.co;side='R' if p.x>=0 else 'L';weights=None
   if quad and p.z<.69:
    old={o.vertex_groups[g.group].name:g.weight for g in v.groups}
    if owners.get(v.index)=='Tail' or (p.y<-1.06 and abs(p.x)<.3):
     weights={'Tail':1}
    elif old.get('Tail',0)>.4:continue
    limb_weight=sum(w for name,w in old.items() if 'Upper.' in name or 'Lower.' in name)
    if weights is None:
     if p.z>.35 and limb_weight<.35:continue
     tag=owners.get(v.index)
     if not tag and centroids:tag=min(centroids,key=lambda name:(p.xy-centroids[name].xy).length_squared)
     if not tag:continue
     station,side=tag.split('.')
     lower=station+'Lower.'+side;upper=station+'Upper.'+side
     joint=rig.data.bones[lower].head_local.z
     t=max(0,min(1,(p.z-joint+.07)/.20));t=t*t*(3-2*t)
     weights={lower:1-t,upper:t}
   elif not quad and .18<p.z<.78 and abs(p.x)>.34:
    weights={'Hand.'+side:1}
   elif not quad and p.z<.34:
    foot='Foot.'+side;shin='Shin.'+side
    joint=rig.data.bones[foot].head_local.z
    t=max(0,min(1,(p.z-joint-.035)/.14));t=t*t*(3-2*t)
    weights={foot:1-t,shin:t}
   if weights:
    for group in o.vertex_groups:group.remove([v.index])
    for name,w in weights.items():
     if w>.00001:groups[name].add([v.index],w,'REPLACE')
    changed+=1
  # Blend the transferred fields over neighboring surface vertices. Abrupt
  # per-vertex classifications otherwise turn small seam triangles into fins.
  neighbors=[set() for _ in o.data.vertices]
  for edge in o.data.edges:
   a,b=edge.vertices;neighbors[a].add(b);neighbors[b].add(a)
  fields=[{g.group:g.weight for g in v.groups} for v in o.data.vertices]
  for iteration in range(6):
   next_fields=[]
   for v in o.data.vertices:
    if v.co.z>.78 or not neighbors[v.index]:next_fields.append(fields[v.index]);continue
    weights={g:w*.5 for g,w in fields[v.index].items()}
    for index in neighbors[v.index]:
     for g,w in fields[index].items():weights[g]=weights.get(g,0)+w*.5/len(neighbors[v.index])
    top=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(w for _,w in top)
    next_fields.append({g:w/total for g,w in top})
   fields=next_fields
  for v in o.data.vertices:
   if v.co.z>.78:continue
   for group in o.vertex_groups:group.remove([v.index])
   for index,w in fields[v.index].items():o.vertex_groups[index].add([v.index],w,'REPLACE')
  if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
  for f in o.data.polygons:f.use_smooth=True
 rig.data.pose_position='POSE'
 bridge.save_editable(ROOT/'blender/forge_rebuild/editable'/f"{e['key']}.blend")
 bridge.export_runtime(ROOT/e['target'],export_skins=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True)
 report_path=ROOT/'docs/forge_rebuild'/f"{e['key']}.json";report=json.loads(report_path.read_text())
 report['animation_skin_refinement']={'constrained_limb_vertices':changed,'removed_bridge_faces':removed,'reason':'Opened run views revealed lower-limb sheets from floor geometry and mixed limb influence.'}
 report_path.write_text(json.dumps(report,indent=2))
 # The previous archive remains retained as a candidate; archive the corrected
 # editable and runtime files again after the animation review.
 e.pop('finalized_candidate_id',None);e.pop('editable_candidate_id',None)
 print('FORGE_SKIN_REFINED',e['key'],changed,removed,flush=True)
(ROOT/'blender/forge_rebuild/plan.json').write_text(json.dumps(plan,indent=2))
