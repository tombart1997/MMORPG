"""Remove the black exterior shell diagnosed in the exported dead-tree views."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'blender/multiview_rebuild/prepared/dead_tree.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
removed=0
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    mat=o.data.materials[0];shader=mat.node_tree.nodes['Principled BSDF']
    image=shader.inputs['Base Color'].links[0].from_node.image
    pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(image.size[1],image.size[0],4)
    uv=o.data.uv_layers.active.data;discard=[]
    for f in o.data.polygons:
        values=[]
        for loop in f.loop_indices:
            p=uv[loop].uv;values.append(pixels[min(image.size[1]-1,max(0,int(p.y*image.size[1]))),min(image.size[0]-1,max(0,int(p.x*image.size[0]))),:3])
        # Retain fine bark crevices. The hallucinated outer shell has large,
        # nearly black polygons unsupported by every input reference.
        center=sum((uv[loop].uv for loop in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
        color=pixels[min(image.size[1]-1,max(0,int(center.y*image.size[1]))),min(image.size[0]-1,max(0,int(center.x*image.size[0]))),:3]
        if color.max()<.16 or sum(value.max()<.10 for value in values)>=2:discard.append(f.index)
    bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.faces[i] for i in discard],context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
    unseen=set(bm.verts);groups=[]
    while unseen:
        todo=[unseen.pop()];group=[]
        while todo:
            v=todo.pop();group.append(v)
            for e in v.link_edges:
                n=e.other_vert(v)
                if n in unseen:unseen.remove(n);todo.append(n)
        groups.append(group)
    biggest=max(groups,key=len)
    bmesh.ops.delete(bm,geom=[v for group in groups if group is not biggest for v in group],context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();removed+=len(discard)
    shader.inputs['Roughness'].default_value=.92
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'game/review_assets/full_rebuild/dead_tree/runtime.glb'),export_format='GLB',export_animations=False)
(ROOT/'docs/full_asset_rebuild/dead_tree_repair.json').write_text(json.dumps({'method':'targeted_exterior_shell_removal','removed_faces':removed,
    'diagnosis':'Black rectangular shell absent from all four references; found by opening actual Godot front/side/back/three-quarter renders.',
    'old_geometry_reused':False,'reference':'concepts_docs/art/asset_turnarounds_v2/dead_tree/turnaround.png'},indent=2))
print('SHELL_REMOVAL',removed,flush=True)
