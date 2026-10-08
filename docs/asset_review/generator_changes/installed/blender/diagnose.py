"""Mesh evidence, not an artistic score. Runs inside Blender on saved sources."""
import bpy, bmesh, json, sys, math, time
from pathlib import Path
from mathutils import Vector


def inspect_regions(obj, regions):
    result=[]
    for region in regions:
        lo,hi=region['min'],region['max']
        vertices=[v.index for v in obj.data.vertices if all(lo[i]<=v.co[i]<=hi[i] for i in range(3))]
        ids=set(vertices)
        faces=[p for p in obj.data.polygons if all(v in ids for v in p.vertices)]
        uv=obj.data.uv_layers.active
        area=0.0
        if uv:
            for p in faces:
                points=[uv.data[i].uv for i in p.loop_indices]
                area+=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(points,points[1:]+points[:1])))*.5
        result.append({'name':region['name'],'vertices':len(vertices),'faces':len(faces),'uv_area':area,
                       'coordinate_space':'mesh local','bounds':[lo,hi]})
    return result


def audit(regions=None):
    objects=[]
    shapes={b.custom_shape for o in bpy.context.scene.objects if o.type=='ARMATURE' for b in o.pose.bones if b.custom_shape}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or obj.hide_render or obj in shapes:continue
        me=obj.data;me.calc_loop_triangles()
        bm=bmesh.new();bm.from_mesh(me)
        # glTF duplicates UV/normal seams. Weld a temporary inspection mesh;
        # never mislabel those duplicate edges as physical holes in the source.
        diag=max((Vector(obj.dimensions)).length,1e-6)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=diag*1e-6)
        bm.verts.index_update()
        unvisited=set(bm.verts);components=[]
        while unvisited:
            todo=[unvisited.pop()];count=0
            while todo:
                v=todo.pop();count+=1
                for edge in v.link_edges:
                    n=edge.other_vert(v)
                    if n in unvisited:unvisited.remove(n);todo.append(n)
            components.append(count)
        boundary=sum(e.is_boundary for e in bm.edges)
        nonmanifold=sum(len(e.link_faces)>2 for e in bm.edges)
        sharp=sum(e.is_manifold and e.calc_face_angle(0)>math.radians(60) for e in bm.edges)
        bm.free()
        arm=next((m.object for m in obj.modifiers if m.type=='ARMATURE' and m.object),None)
        groupids={g.index for g in obj.vertex_groups if arm and g.name in arm.data.bones}
        weight_sums=[sum(g.weight for g in v.groups if g.group in groupids) for v in me.vertices] if arm else []
        uv=me.uv_layers.active;uv_area=0.0;collapsed=0
        if uv:
            for tri in me.loop_triangles:
                a,b,c=[uv.data[i].uv for i in tri.loops]
                value=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
                uv_area+=value;collapsed+=value<1e-12
        lo=[min(v.co[i] for v in me.vertices) for i in range(3)]
        hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
        objects.append({'name':obj.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),
            'local_bounds':[lo,hi],'world_matrix':[list(row) for row in obj.matrix_world],
            'degenerate_triangles':sum(t.area<1e-12 for t in me.loop_triangles),
            'welded_boundary_edges':boundary,'welded_nonmanifold_edges':nonmanifold,
            'connected_components_vertices':sorted(components,reverse=True),'sharp_edges_over_60_degrees':sharp,
            'smooth_faces':sum(p.use_smooth for p in me.polygons),'faces':len(me.polygons),
            'custom_normals':me.has_custom_normals,'uv_layers':[u.name for u in me.uv_layers],
            'uv_triangle_area_sum':uv_area,'collapsed_uv_triangles':collapsed,
            'materials':[m.name if m else None for m in me.materials],
            'skinned':bool(arm),'unweighted_vertices':sum(w<.001 for w in weight_sums),
            'weight_sum_range':[min(weight_sums),max(weight_sums)] if weight_sums else None,
            'regions':inspect_regions(obj,(regions or {}).get(obj.name,[]))})
    materials=[]
    for mat in bpy.data.materials:
        nodes=mat.node_tree.nodes if mat.use_nodes else []
        bsdf=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
        channels={}
        if bsdf:
            for key in ['Base Color','Roughness','Metallic','Normal','Alpha','Emission Color','Emission Strength']:
                socket=bsdf.inputs[key];value=socket.default_value
                channels[key]={'linked':socket.is_linked,'value':list(value) if hasattr(value,'__len__') else value}
        materials.append({'name':mat.name,'channels':channels,'textures':[{'name':n.image.name,
            'resolution':list(n.image.size),'available':n.image.has_data,'packed':bool(n.image.packed_file),
            'colorspace':n.image.colorspace_settings.name} for n in nodes if n.type=='TEX_IMAGE' and n.image]})
    return {'schema':1,'objects':objects,'materials':materials,
        'triangles':sum(o['triangles'] for o in objects),
        'skeletons':[{'name':o.name,'bones':[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local)} for b in o.data.bones]} for o in bpy.context.scene.objects if o.type=='ARMATURE'],
        'clips':[a.name for a in bpy.data.actions],
        'interpretation_limits':['Boundaries and connected components need semantic inspection; openings may be intentional.',
        'UV area sums do not prove overlaps or face pixel quality. Source textures and region allocation require review.',
        'Normal vectors and weights alone do not establish anatomy, clipping or reference fidelity.'],
        'visual_status':'requires_review'}


def load_source(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=60
    suffix=Path(path).suffix.lower()
    if suffix=='.blend':bpy.ops.wm.open_mainfile(filepath=str(path))
    elif suffix in ('.glb','.gltf'):bpy.ops.import_scene.gltf(filepath=str(path))
    elif suffix=='.fbx':bpy.ops.import_scene.fbx(filepath=str(path))
    elif suffix=='.obj':bpy.ops.wm.obj_import(filepath=str(path))
    else:raise ValueError('Unsupported saved mesh format: '+suffix)
    for o in bpy.context.scene.objects:
        if o.type=='ARMATURE':o.data.pose_position='REST'
    bpy.context.view_layer.update()


def main():
    request=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
    for entry in request['assets']:
        start=time.monotonic();load_source(entry['source'])
        result=audit(entry.get('regions'));result.update(source=entry['source'],seconds=round(time.monotonic()-start,3))
        out=Path(entry['output']);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
        print('DIAGNOSED',entry.get('key'),result['triangles'],flush=True)


if __name__=='__main__':main()
