"""Reviewable topology replacement, surface projection and material/skin transfer.

Runs inside Blender. Raw sources are retained by pipeline.py. A failed quality
guard restores the original mesh; it never silently forces a damaged low-poly
result into the runtime export. QuadriFlow is automatic retopology, not authored
joint loops or automatic anatomy repair.
"""
import math
import json
import os
import re
import subprocess
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def remesh_bounded(obj, target, work_dir):
    """A difficult remesh must fall back without freezing the whole asset job."""
    work_dir=Path(work_dir);work_dir.mkdir(parents=True,exist_ok=True)
    name=re.sub(r"[^a-zA-Z0-9_-]","_",obj.name)
    request_path=work_dir/(name+"_input.json");result_path=work_dir/(name+"_quads.json")
    request={"vertices":[list(v.co) for v in obj.data.vertices],
             "faces":[list(f.vertices) for f in obj.data.polygons],
             "target":target,"parent_pid":os.getpid(),"output":str(result_path)}
    request_path.write_text(json.dumps(request),encoding="utf-8")
    log_path=work_dir/(name+"_remesh.log")
    with log_path.open("w",encoding="utf-8") as log:
        try:
            result=subprocess.run([bpy.app.binary_path,"--background","--threads","6","--python-exit-code","1",
                "--python",str(Path(__file__).with_name("remesh_worker.py")),"--","--request",str(request_path)],
                stdout=log,stderr=subprocess.STDOUT,timeout=90,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
        except subprocess.TimeoutExpired:
            raise ValueError("QuadriFlow exceeded 90 seconds; simplification fallback selected") from None
    if result.returncode or not result_path.exists():
        raise ValueError("QuadriFlow failed; see "+str(log_path))
    result=json.loads(result_path.read_text(encoding="utf-8"))
    mesh=bpy.data.meshes.new(obj.name+"_Retopology")
    mesh.from_pydata(result["vertices"],[],result["faces"]);mesh.update()
    obj.data=mesh
    return {"remesh_input":result["remesh_input"],"remeshed_quads":result["remeshed_quads"],"log":str(log_path)}


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def surface(mesh):
    mesh.calc_loop_triangles()
    faces = [tuple(t.vertices) for t in mesh.loop_triangles]
    return BVHTree.FromPolygons([v.co for v in mesh.vertices], faces, all_triangles=True), faces


def extent(mesh):
    points = [v.co for v in mesh.vertices]
    lo = Vector([min(v[i] for v in points) for i in range(3)])
    hi = Vector([max(v[i] for v in points) for i in range(3)])
    return lo, hi


def quality(source, result):
    """Bidirectional distances catch missing limbs as well as displaced surfaces."""
    old_bvh, _ = surface(source)
    new_bvh, _ = surface(result)
    lo, hi = extent(source)
    new_lo, new_hi = extent(result)
    diagonal = max((hi-lo).length, 1e-6)
    errors = []
    for mesh, tree in [(source, new_bvh), (result, old_bvh)]:
        step = max(1, len(mesh.vertices)//3000)
        points = [mesh.vertices[i].co for i in range(0,len(mesh.vertices),step)]
        # Extremities must not disappear between uniformly sampled vertices.
        for axis in range(3):
            points.extend([min(mesh.vertices,key=lambda v:v.co[axis]).co,
                           max(mesh.vertices,key=lambda v:v.co[axis]).co])
        for point in points:
            nearest = tree.find_nearest(point)
            errors.append(nearest[3] if nearest and nearest[0] is not None else diagonal)
    errors.sort()
    bm = bmesh.new(); bm.from_mesh(result)
    defects = sum(not e.is_manifold and not e.is_boundary and bool(e.link_faces) for e in bm.edges)
    bm.free()
    return {"surface_max_fraction":errors[-1]/diagonal,
            "surface_p95_fraction":errors[int(len(errors)*.95)]/diagonal,
            "bounds_drift_fraction":max(max(abs(new_lo[i]-lo[i]),abs(new_hi[i]-hi[i]))/diagonal for i in range(3)),
            "nonmanifold_edges":defects,"samples":len(errors)}


def barycentric(point, a, b, c):
    ab, ac, ap = b-a, c-a, point-a
    aa, bb, cc, dd, ee = ab.dot(ab), ab.dot(ac), ac.dot(ac), ap.dot(ab), ap.dot(ac)
    denominator = aa*cc-bb*bb
    if abs(denominator)<1e-15:return (1,0,0)
    v, w = (cc*dd-bb*ee)/denominator, (aa*ee-bb*dd)/denominator
    weights = [max(0,1-v-w),max(0,v),max(0,w)]
    total = sum(weights)
    return [x/total for x in weights]


def project_and_transfer(source, target):
    tree, faces = surface(source.data)
    names = [g.name for g in source.vertex_groups]
    for group in list(target.vertex_groups):target.vertex_groups.remove(group)
    for name in names:target.vertex_groups.new(name=name)
    armature = next((m.object for m in source.modifiers if m.type=="ARMATURE" and m.object),None)
    bone_names = set(armature.data.bones.keys()) if armature else set()
    for vertex in target.data.vertices:
        point, _, index, _ = tree.find_nearest(vertex.co)
        if point is None:raise ValueError("No source surface for a remeshed vertex")
        vertex.co = point
        ids = faces[index]
        coefficients = barycentric(point, *[source.data.vertices[i].co for i in ids])
        weights = {}
        for i, factor in zip(ids, coefficients):
            for group in source.data.vertices[i].groups:
                if names[group.group] in bone_names:
                    weights[group.group] = weights.get(group.group,0)+factor*group.weight
        if bone_names and not weights:raise ValueError("Source contains an unweighted surface region")
        top = sorted(weights.items(),key=lambda pair:-pair[1])[:4]
        total = sum(w for _,w in top)
        for group, weight in top:
            if weight>1e-7:target.vertex_groups[group].add([vertex.index],weight/total,"REPLACE")


def deformation_quality(source, target, limit):
    """Reject reductions that drift from the retained rig in sampled clip poses."""
    rig=next((m.object for m in source.modifiers if m.type=="ARMATURE" and m.object),None)
    if not rig or not rig.animation_data or not rig.animation_data.nla_tracks:return []
    scene=bpy.context.scene;data=rig.animation_data
    saved_frame=scene.frame_current;pose=rig.data.pose_position;action=data.action
    slot=data.action_slot if action else None
    states=[(track,track.mute,track.is_solo) for track in data.nla_tracks]
    records=[]
    try:
        data.action=None;rig.data.pose_position="POSE"
        for track,_,_ in states:track.mute=True;track.is_solo=False
        for track,_,_ in states:
            if not track.strips:continue
            track.mute=False
            for strip in track.strips:
                largest=0.0;p95=0.0
                for fraction in [.25,.5,.75]:
                    scene.frame_set(round(strip.frame_start+fraction*(strip.frame_end-strip.frame_start)))
                    deps=bpy.context.evaluated_depsgraph_get()
                    old=source.evaluated_get(deps);new=target.evaluated_get(deps)
                    old_mesh=old.to_mesh();new_mesh=new.to_mesh()
                    try:
                        guard=quality(old_mesh,new_mesh)
                        largest=max(largest,guard["surface_max_fraction"])
                        p95=max(p95,guard["surface_p95_fraction"])
                    finally:old.to_mesh_clear();new.to_mesh_clear()
                record={"clip":track.name,"samples":3,"max_fraction":largest,"p95_fraction":p95}
                records.append(record)
                if largest>limit or p95>limit*.5:raise ValueError("Deformation quality guard rejected clip: "+str(record))
            track.mute=True
    finally:
        for track,mute,solo in states:track.mute=mute;track.is_solo=solo
        data.action=action
        if action and slot:data.action_slot=slot
        rig.data.pose_position=pose;scene.frame_set(saved_frame)
    return records


def bake_materials(source, target, size, normal_map=False):
    """Transfer Principled inputs without baking studio lighting into the atlas."""
    # Godot's documented -vcol hint interprets COLOR_0 as sRGB. Blender's
    # imported color field is linear, so match the source's Godot appearance
    # before turning it into an sRGB albedo texture. Only the disposable bake
    # copy changes; the retained input and source export stay untouched.
    import re
    if any(m and re.search(r'-vcol(?:\.\d+)*$',m.name) for m in source.data.materials):
        import numpy as np
        for attribute in source.data.color_attributes:
            values=np.empty(len(attribute.data)*4,dtype=np.float32)
            attribute.data.foreach_get('color',values)
            rgba=values.reshape(-1,4);rgb=rgba[:,:3].copy()
            rgba[:,:3]=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
            attribute.data.foreach_set('color',values)
    shaders = []
    for material in source.data.materials:
        shader = next((n for n in material.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None) if material and material.use_nodes else None
        if shader is None:raise ValueError("Material transfer requires Principled BSDF sources")
        output=next((n for n in material.node_tree.nodes if n.type=="OUTPUT_MATERIAL" and n.is_active_output),None)
        if not output or not output.inputs["Surface"].is_linked or output.inputs["Surface"].links[0].from_node != shader:
            raise ValueError("Mixed material shaders require manual transfer; source retained")
        shaders.append(shader)
    if not shaders:raise ValueError("Source has no transferable materials")
    alpha=[s.inputs["Alpha"] for s in shaders]
    if any(i.is_linked for i in alpha) or any(i.default_value!=alpha[0].default_value for i in alpha):
        raise ValueError("Textured/mixed transparency requires a combined RGBA atlas; source retained")
    normal_map=normal_map or any(s.inputs["Normal"].is_linked for s in shaders)
    activate(target)
    for layer in list(target.data.uv_layers):target.data.uv_layers.remove(layer)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008)
    bpy.ops.object.mode_set(mode="OBJECT")
    target.data.materials.clear()
    material = bpy.data.materials.new(target.name+"_Runtime")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    target.data.materials.append(material)
    for face in target.data.polygons:face.material_index=0
    # Transfer constant opacity/culling policy along with the new UVs.
    shader.inputs["Alpha"].default_value=alpha[0].default_value
    material.use_backface_culling=all(m.use_backface_culling for m in source.data.materials)
    if hasattr(material,"surface_render_method"):
        material.surface_render_method=source.data.materials[0].surface_render_method
    scene = bpy.context.scene
    previous_engine = scene.render.engine
    scene.render.engine="CYCLES"; scene.cycles.device="CPU"; scene.cycles.samples=1
    bake=scene.render.bake
    bake.use_selected_to_active=True; bake.use_cage=False
    lo,hi=extent(source.data)
    bake.cage_extrusion=max((hi-lo).length*.025,.001)
    bake.max_ray_distance=max((hi-lo).length*.08,.003)
    bake.margin=8; bake.use_clear=True
    source.hide_render=False; source.hide_set(False)
    images=[]

    def run(channel, kind, color=True):
        atlas=bpy.data.images.new(target.name+"_"+channel,width=size,height=size,alpha=False)
        if not color:atlas.colorspace_settings.name="Non-Color"
        node=material.node_tree.nodes.new("ShaderNodeTexImage");node.image=atlas
        material.node_tree.nodes.active=node
        activate(target);source.select_set(True)
        bpy.ops.object.bake(type=kind)
        atlas.pack();images.append(atlas.name)
        return node

    def transfer(channel, color=False, force=False):
        inputs=[s.inputs[channel] for s in shaders]
        values=[tuple(i.default_value) if color else float(i.default_value) for i in inputs]
        different=any(value!=values[0] for value in values)
        if not force and not any(i.is_linked for i in inputs) and not different:
            shader.inputs[channel].default_value=inputs[0].default_value
            return
        temporary=[]
        for s in shaders:
            graph=s.id_data
            output=next(n for n in graph.nodes if n.type=="OUTPUT_MATERIAL" and n.is_active_output)
            previous=[link.from_socket for link in output.inputs["Surface"].links]
            emitter=graph.nodes.new("ShaderNodeEmission")
            emitter.inputs["Strength"].default_value=1
            if s.inputs[channel].is_linked:graph.links.new(s.inputs[channel].links[0].from_socket,emitter.inputs["Color"])
            else:emitter.inputs["Color"].default_value=s.inputs[channel].default_value if color else (s.inputs[channel].default_value,)*3+(1,)
            graph.links.new(emitter.outputs[0],output.inputs["Surface"])
            temporary.append((graph,output,previous,emitter))
        try:
            node=run(channel,"EMIT",color)
            material.node_tree.links.new(node.outputs["Color"],shader.inputs[channel])
        finally:
            for graph,output,previous,emitter in temporary:
                graph.nodes.remove(emitter)
                for socket in previous:graph.links.new(socket,output.inputs["Surface"])

    try:
        transfer("Base Color",color=True,force=True)
        for channel in ["Roughness","Metallic"]:transfer(channel)
        # A texture for emission strength is not portable through glTF. Retain
        # such sources rather than silently discard a glow mask/intensity.
        strengths=[s.inputs["Emission Strength"] for s in shaders]
        if any(i.is_linked for i in strengths) or any(i.default_value!=strengths[0].default_value for i in strengths):
            raise ValueError("Varying emission strength requires a combined emission atlas; source retained")
        shader.inputs["Emission Strength"].default_value=strengths[0].default_value
        if strengths[0].default_value>0:transfer("Emission Color",color=True)
        if normal_map:
            node=run("Normal","NORMAL",False)
            normal=material.node_tree.nodes.new("ShaderNodeNormalMap")
            material.node_tree.links.new(node.outputs["Color"],normal.inputs["Color"])
            material.node_tree.links.new(normal.outputs["Normal"],shader.inputs["Normal"])
    finally:
        scene.render.engine=previous_engine
    # The atlas now owns albedo. Retaining COLOR_0 would multiply it a second
    # time in standard glTF viewers, even though Godot disables it by default.
    for attribute in list(target.data.color_attributes):
        target.data.color_attributes.remove(attribute)
    return images


def optimize(objects, settings, emit, work_dir=None):
    mode=settings.get("optimization_mode","preserve")
    if mode=="preserve":return {"mode":mode,"objects":[],"source_preserved":True}
    total=sum(triangles(o) for o in objects)
    budget=settings.get("triangle_budget",16000)
    work_dir=work_dir or Path(bpy.data.filepath).parent/"optimization_work"
    records=[]
    poses={o:o.data.pose_position for o in bpy.context.scene.objects if o.type=="ARMATURE"}
    for rig in poses:rig.data.pose_position="REST"
    try:
        for obj in objects:
            before=triangles(obj)
            target=max(16,int(budget*before/max(1,total)))
            record={"name":obj.name,"before":before,"target":target,"status":"unchanged"}
            records.append(record)
            if before<=target and mode!="retopology":continue
            # Original data, materials and rig stay isolated for projection/baking.
            high=obj.copy();high.data=obj.data.copy()
            bpy.context.scene.collection.objects.link(high)
            high.name=obj.name+"_BakeSource"
            for i,mat in enumerate(high.data.materials):
                if mat:high.data.materials[i]=mat.copy()
            saved_mesh=obj.data.copy()
            saved_groups=[[(g.group,g.weight) for g in v.groups] for v in obj.data.vertices]
            saved_names=[g.name for g in obj.vertex_groups]
            skinned=any(m.type=="ARMATURE" for m in obj.modifiers)
            attempts=[]
            methods=["quad_remesh","simplify"] if mode in ("balanced","retopology") and not skinned else ["simplify"]
            if mode=="retopology":methods=["quad_remesh","simplify"]

            def restore():
                obj.data=saved_mesh.copy()
                for group in list(obj.vertex_groups):obj.vertex_groups.remove(group)
                for name in saved_names:obj.vertex_groups.new(name=name)
                for i,groups in enumerate(saved_groups):
                    for group,weight in groups:obj.vertex_groups[group].add([i],weight,"REPLACE")

            try:
                for method in methods:
                    restore();activate(obj)
                    emit("optimization",object=obj.name,method=method,target=target)
                    try:
                        if method=="quad_remesh":
                            remesh_info=remesh_bounded(obj,target,work_dir)
                            project_and_transfer(high,obj)
                        if triangles(obj)>target:
                            modifier=obj.modifiers.new("Forge budget reduction","DECIMATE")
                            modifier.ratio=max(.001,(target-4)/triangles(obj))
                            modifier.use_collapse_triangulate=True
                            bpy.ops.object.modifier_apply(modifier=modifier.name)
                        if method=="quad_remesh":
                            for face in obj.data.polygons:face.use_smooth=True
                        guard=quality(high.data,obj.data)
                        limit=settings.get("max_surface_error",.02)
                        if guard["surface_max_fraction"]>limit or guard["surface_p95_fraction"]>limit*.5 or guard["nonmanifold_edges"]:
                            raise ValueError("Surface quality guard rejected the reduction: "+str(guard))
                        if skinned:
                            bone_names={b.name for m in obj.modifiers if m.type=="ARMATURE" and m.object for b in m.object.data.bones}
                            for v in obj.data.vertices:
                                weights=[(g.group,g.weight) for g in v.groups if obj.vertex_groups[g.group].name in bone_names]
                                top=sorted(weights,key=lambda pair:-pair[1])[:4];weight_sum=sum(w for _,w in top)
                                if weight_sum<1e-6:raise ValueError("Optimization introduced an unweighted vertex")
                                for g in obj.vertex_groups:g.remove([v.index])
                                for index,w in top:obj.vertex_groups[index].add([v.index],w/weight_sum,"REPLACE")
                        deformation=deformation_quality(high,obj,limit) if skinned else []
                        if method=="simplify" and before<=target:raise ValueError("Source is already within budget; fallback leaves its topology unchanged")
                        # Decimation removes vertex paint samples as well as vertices.
                        # Bake the retained high-resolution color field to UVs before
                        # export; keeping sparse vertex colors destroys surface detail.
                        has_vertex_colors=bool(high.data.color_attributes)
                        rebaked=method=="quad_remesh" or settings.get("bake_normal_map",False) or has_vertex_colors
                        images=bake_materials(high,obj,settings.get("texture_resolution",1024),settings.get("bake_normal_map",False)) if rebaked else []
                        record.update(status="optimized",method=method,after=triangles(obj),quality=guard,textures=images,
                                      material_transfer="rebaked_atlas" if rebaked else "preserved_source_uvs_and_materials",
                                      deformation=deformation)
                        if method=="quad_remesh":record.update(remesh_info)
                        break
                    except Exception as error:
                        if bpy.context.object and bpy.context.object.mode!="OBJECT":bpy.ops.object.mode_set(mode="OBJECT")
                        attempts.append({"method":method,"reason":str(error)})
                        # Applied mesh changes are restored before the next attempt.
                        for mod in list(obj.modifiers):
                            if mod.name.startswith("Forge budget"):obj.modifiers.remove(mod)
                if record["status"]!="optimized":
                    restore();record.update(status="quality_guard_kept_source",after=before)
                record["rejected_attempts"]=attempts
            finally:
                bpy.data.objects.remove(high,do_unlink=True)
    finally:
        for rig,pose in poses.items():rig.data.pose_position=pose
    return {"mode":mode,"source_preserved":True,"objects":records,
            "target_triangles":budget,"achieved_triangles":sum(triangles(o) for o in objects),
            "note":"Automatic quad remeshing is available; authored joint loops, anatomy repair and animation acceptance still require review."}
