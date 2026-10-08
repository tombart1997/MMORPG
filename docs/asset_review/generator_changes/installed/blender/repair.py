"""Small, explicit Blender operations. No inferred anatomy or universal smoothing."""
import bpy,bmesh,math
from mathutils import Vector
from optimize import quality,deformation_quality


def inside(point,box):return all(box['min'][i]<=point[i]<=box['max'][i] for i in range(3))


def smooth(obj,args):
    source=obj.data.copy();saved=[v.co.copy() for v in obj.data.vertices]
    points=[v.co for v in source.vertices];lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
    diag=max((hi-lo).length,1e-6);epsilon=diag*1e-6
    bm=bmesh.new();bm.from_mesh(source);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=epsilon)
    bm.verts.ensure_lookup_table()
    def key(co):return tuple(round(v/epsilon) for v in co)
    # Canonical welded positions keep UV/normal seam duplicates together.
    aliases={}
    for v in source.vertices:aliases.setdefault(key(v.co),[]).append(v.index)
    frozen={v for v in bm.verts if not inside(v.co,args['region']) or any(inside(v.co,r) for r in args.get('protected_regions',[]))
        or any(e.is_boundary or e.is_manifold and e.calc_face_angle(0)>math.radians(60) for e in v.link_edges)}
    selected=[v for v in bm.verts if v not in frozen];original={v:v.co.copy() for v in selected}
    for _ in range(args.get('iterations',1)):
        updates={v:v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges),args.get('factor',.1)) for v in selected if v.link_edges}
        for v,co in updates.items():
            movement=co-original[v];limit=diag*args.get('max_displacement',.01)
            if movement.length>limit:movement*=limit/movement.length
            v.co=original[v]+movement
    moved=0;maxmove=0
    for v in selected:
        origin=original[v]
        ids=aliases.get(key(origin),[])
        for i in ids:obj.data.vertices[i].co=v.co;moved+=1;maxmove=max(maxmove,(v.co-origin).length)
    bm.free();obj.data.update()
    report=quality(source,obj.data)
    if report['surface_max_fraction']>args.get('max_displacement',.01)*1.1:
        for v,co in zip(obj.data.vertices,saved):v.co=co
        obj.data.update();bpy.data.meshes.remove(source);raise ValueError('Local smoothing exceeded surface guard; source restored')
    # Geometry remains indexed identically: UVs, material slots and weights are
    # retained exactly. Every animation still requires rendered review.
    bpy.data.meshes.remove(source)
    return {'operation':'selective_smooth','object':obj.name,'moved_vertices':moved,'protected_vertices':len(frozen),
            'max_displacement':maxmove,'surface':report,'uv_and_weight_policy':'Original indexed UVs and weights retained'}


def apply(plan):
    results=[];armatures=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    poses=[o.data.pose_position for o in armatures]
    for o in armatures:o.data.pose_position='REST'
    try:
        for op in plan:
            name=op['operation'];args=op.get('parameters',{})
            if name=='selective_smooth':
                obj=bpy.data.objects.get(args['object'])
                if not obj or obj.type!='MESH':raise ValueError('Repair mesh not found: '+args['object'])
                results.append(smooth(obj,args))
            elif name=='normals_repair':
                obj=bpy.data.objects.get(args['object'])
                if not obj or obj.type!='MESH':raise ValueError('Normal repair mesh not found')
                bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();results.append({'operation':name,'object':obj.name})
            elif name=='rebuild_parts':
                from rebuild_parts import apply as rebuild
                obj=bpy.data.objects.get(args['object'])
                if not obj:raise ValueError('Diagnosed rebuild mesh not found')
                results.append(rebuild(obj,args['template'],args.get('config',{})))
            elif name=='material_adjust':
                mat=bpy.data.materials.get(args['material'])
                if not mat or not mat.use_nodes:raise ValueError('Named node material not found')
                bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
                if not bsdf:raise ValueError('Unsupported material graph')
                changed=[]
                for key in ['roughness','metallic']:
                    if key in args:
                        socket=bsdf.inputs[key.capitalize()]
                        if socket.is_linked:raise ValueError('Linked channel needs texture authoring, not a constant override')
                        socket.default_value=args[key];changed.append(key)
                results.append({'operation':name,'material':mat.name,'channels':changed})
            elif name in ('simplify','assisted_blender','regenerate'):
                results.append({'operation':name,'stage':'handled by frozen job inputs'})
            else:raise ValueError('Unsupported Blender repair')
    finally:
        for obj,pose in zip(armatures,poses):obj.data.pose_position=pose
    return results
