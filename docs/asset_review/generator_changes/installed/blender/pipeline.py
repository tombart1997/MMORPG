"""Executed by Blender in a disposable background process."""
import argparse
import json
import math
import sys
import time
import struct
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


def emit(stage, **kwargs):
    print("FORGE:"+json.dumps({"stage":stage,**kwargs}),flush=True)


def save_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2),encoding="utf-8")


def mesh_objects():
    custom_shapes = {b.custom_shape for o in bpy.context.scene.objects if o.type=="ARMATURE" for b in o.pose.bones if b.custom_shape}
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.get("forge_collision") and o not in custom_shapes and not o.hide_render]


def bounds(objects):
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    if not points:
        raise RuntimeError("No mesh geometry was imported")
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return low, high


def inspect():
    objects = mesh_objects()
    records, textures = [], []
    for o in objects:
        me = o.data
        me.calc_loop_triangles()
        degenerate = sum(1 for t in me.loop_triangles if t.area < 1e-12)
        bm = bmesh.new()
        bm.from_mesh(me)
        boundary = sum(e.is_boundary for e in bm.edges)
        nonmanifold = sum(not e.is_manifold and not e.is_boundary and len(e.link_faces)>0 for e in bm.edges)
        loose = sum(len(v.link_edges)==0 for v in bm.verts)
        bm.free()
        uv_collapsed = 0
        if me.uv_layers.active:
            uv = me.uv_layers.active.data
            for tri in me.loop_triangles:
                a,b,c = [uv[i].uv for i in tri.loops]
                if abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)) < 1e-12:
                    uv_collapsed += 1
        armature = next((m.object for m in o.modifiers if m.type == "ARMATURE" and m.object),None)
        unweighted = 0
        if armature:
            bones = set(armature.data.bones.keys())
            group_ids = {g.index for g in o.vertex_groups if g.name in bones}
            unweighted = sum(sum(g.weight for g in v.groups if g.group in group_ids)<0.001 for v in me.vertices)
        records.append({"name":o.name,"vertices":len(me.vertices),"triangles":len(me.loop_triangles),"materials":len(me.materials),
                        "degenerate_faces":degenerate,"boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
                        "loose_vertices":loose,"has_uv":bool(me.uv_layers),"collapsed_uv_triangles":uv_collapsed,
                        "skinned":bool(armature),"unweighted_vertices":unweighted})
    for image in bpy.data.images:
        if image.source == "FILE":
            textures.append({"name":image.name,"resolution":list(image.size),"packed":bool(image.packed_file),
                             "available":bool(image.has_data)})
    lo,hi = bounds(objects)
    return {"objects":records,"triangles":sum(r["triangles"] for r in records),"textures":textures,
            "bounds":{"min":list(lo),"max":list(hi)}, "armatures":[{"name":o.name,"bones":len(o.data.bones)} for o in bpy.context.scene.objects if o.type == "ARMATURE"],
            "actions":[a.name for a in bpy.data.actions],"boundary_note":"Open boundaries may be intentional; no watertight requirement is applied",
            "unverified":["UV overlap beyond collapsed triangles", "Internal occluded geometry", "Baked lighting", "Joint clipping", "Reference fidelity"]}


def select_asset():
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        if o.type in ("MESH","ARMATURE","EMPTY") and not o.get("forge_preview") and (o.type!="MESH" or o in mesh_objects()):
            o.select_set(True)


def export(path, fmt="glb", apply_modifiers=False):
    select_asset()
    kwargs = dict(filepath=str(path),export_format="GLB" if fmt == "glb" else "GLTF_SEPARATE",use_selection=True,
                  export_animations=True,export_yup=True,export_apply=apply_modifiers)
    if any(o.type=="ARMATURE" and o.animation_data and o.animation_data.nla_tracks for o in bpy.context.scene.objects):
        kwargs.update(export_animation_mode="NLA_TRACKS",export_force_sampling=True,export_anim_slide_to_zero=True)
    bpy.ops.export_scene.gltf(**kwargs)


def clip_intervals(path):
    blob=Path(path).read_bytes()
    size=struct.unpack_from("<I",blob,12)[0];doc=json.loads(blob[20:20+size])
    result={}
    for clip in doc.get("animations",[]):
        inputs=[doc["accessors"][s["input"]] for s in clip["samplers"]]
        result[clip["name"]]={"start":min(a.get("min",[0])[0] for a in inputs),
                              "end":max(a.get("max",[0])[0] for a in inputs)}
    return result


def verify_clip_timing(source, runtime):
    before=clip_intervals(source);after=clip_intervals(runtime)
    if before.keys()!=after.keys():raise ValueError("Processing changed animation clip names")
    for name,old in before.items():
        new=after[name]
        if abs((old["end"]-old["start"])-(new["end"]-new["start"]))>1/60+.0001:
            raise ValueError("Processing changed animation duration: "+name)
        if abs(new["start"])>.0001:raise ValueError("Exported clip does not start at zero: "+name)
    return {"source":before,"runtime":after,"duration_tolerance_seconds":1/60,"passed":True}


def setup_lighting():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("Forge studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.055,0.065,0.08,1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    for o in list(scene.objects):
        if o.type in ("LIGHT","CAMERA"):
            bpy.data.objects.remove(o,do_unlink=True)
    objects = mesh_objects()
    lo,hi = bounds(objects)
    center = (lo+hi)/2
    size = max((hi-lo).length,0.1)
    for name,offset,power in [("Key",(2,-3,4),350),("Fill",(-3,-1,2),180),("Rim",(1,3,3),250)]:
        light = bpy.data.lights.new(name,"AREA")
        light.energy = power*size*size
        light.shape = "DISK"
        light.size = size*1.5
        o = bpy.data.objects.new(name,light)
        scene.collection.objects.link(o)
        o.location = center+Vector(offset)*size/2
        o.rotation_euler = (center-o.location).to_track_quat("-Z","Y").to_euler()
        o["forge_preview"] = True
    cam = bpy.data.objects.new("Review camera",bpy.data.cameras.new("Review camera"))
    scene.collection.objects.link(cam)
    cam["forge_preview"] = True
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = size*1.12
    scene.camera = cam
    return cam,center,size


def render_views(out, turntable=False, front_axis="-Z"):
    cam,center,size = setup_lighting()
    scene = bpy.context.scene
    count = 12 if turntable else 1
    for i in range(count):
        angle = 2*math.pi*i/count
        sign = 1 if front_axis=="-Z" else -1
        cam.location = center+Vector((math.sin(angle)*size*2,sign*math.cos(angle)*size*2,size*0.2))
        cam.rotation_euler = (center-cam.location).to_track_quat("-Z","Y").to_euler()
        scene.render.filepath = str(out/f"turntable_{i:02d}.png")
        emit("render",frame=i+1,total=count)
        bpy.ops.render.render(write_still=True)
    if not turntable:
        clay = bpy.data.materials.new("Review clay")
        clay.diffuse_color = (0.42,0.44,0.47,1)
        scene.view_layers[0].material_override = clay
        scene.render.filepath = str(out/"clay.png")
        bpy.ops.render.render(write_still=True)
        scene.view_layers[0].material_override = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request",required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    source,out = Path(request["source"]),Path(request["output"])
    out.mkdir(parents=True,exist_ok=True)
    settings = request["settings"]
    stage = request.get("operation","process")
    start = time.monotonic()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Imported glTF time keys are converted to Blender frames at this rate.
    # Exporting at factory 24 FPS shifts/quantizes the gameplay clips.
    bpy.context.scene.render.fps=60
    bpy.context.scene.render.fps_base=1.0
    emit("import")
    if source.suffix.lower() == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(source))
    elif source.suffix.lower() in (".glb",".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(source))
    elif source.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(source))
    elif source.suffix.lower() == ".obj":
        bpy.ops.wm.obj_import(filepath=str(source))
    else:
        raise RuntimeError("Supported mesh formats: GLB, Blender, FBX, OBJ")
    for o in list(bpy.context.scene.objects):
        if o.type in ("CAMERA","LIGHT") or o.get("forge_preview"):
            bpy.data.objects.remove(o,do_unlink=True)
    for image in bpy.data.images:
        if image.has_data and image.source == "FILE":
            image.pack()
    emit("inspection")
    before = inspect()
    save_json(out/"inspection_before.json",before)
    if stage == "turntable":
        render_views(out,True,settings.get("front_axis","-Z"))
        save_json(out/"render_report.json",{"seconds":time.monotonic()-start,"views":12,"resolution":[512,512],"engine":"Cycles CPU","visual_status":"pending"})
        return
    # Store an editable source before any optional destructive processing.
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"source.blend"))
    export(out/"source.glb")
    if request.get('repairs'):
        sys.path.insert(0,str(Path(__file__).parent))
        from repair import apply as apply_repairs
        repairs=apply_repairs(request['repairs'])
        save_json(out/'repair.json',{'operations':repairs,'visual_status':'requires_review','source_preserved':True})
    rotation = settings.get("source_rotation_degrees",[0,0,0])
    if any(rotation):
        from mathutils import Euler
        transform = Euler(tuple(math.radians(v) for v in rotation)).to_matrix().to_4x4()
        for o in bpy.context.scene.objects:
            if o.parent is None and o.type in ("MESH","ARMATURE","EMPTY"):
                o.matrix_world = transform @ o.matrix_world
        bpy.context.view_layer.update()
    if settings.get("repair_degenerate",False):
        for o in mesh_objects():
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bad = [f for f in bm.faces if f.calc_area()<1e-12]
            bmesh.ops.delete(bm,geom=bad,context="FACES")
            bm.to_mesh(o.data)
            bm.free()
    if settings.get("recalculate_normals",False):
        for o in mesh_objects():
            bm=bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(o.data)
            bm.free()
    emit("optimization")
    sys.path.insert(0,str(Path(__file__).parent))
    from optimize import optimize
    optimization = optimize(mesh_objects(),settings,emit,work_dir=out/"optimization_work")
    save_json(out/"optimization.json",optimization)
    # Resize downward only. A higher requested resolution does not invent detail.
    target_texture = settings.get("texture_resolution",2048)
    for image in bpy.data.images:
        if image.source == "FILE" and image.has_data and max(image.size)>target_texture:
            ratio = target_texture/max(image.size)
            image.scale(max(1,round(image.size[0]*ratio)),max(1,round(image.size[1]*ratio)))
            image.pack()
    if settings.get("material_variant"):
        variant = settings["material_variant"]
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    if not node.inputs["Roughness"].is_linked:
                        node.inputs["Roughness"].default_value = variant.get("roughness",0.7)
                    node.inputs["Emission Color"].default_value = tuple(variant.get("emission",[0,0,0]))+(1,)
                    node.inputs["Emission Strength"].default_value = variant.get("strength",0)
    if settings.get("attachment"):
        empty = bpy.data.objects.new(settings["attachment"].get("name","grip_socket"),None)
        bpy.context.scene.collection.objects.link(empty)
        empty.location = settings["attachment"].get("location",[0,0,0])
    emit("export")
    export(out/"runtime.glb")
    timing_source=source if source.suffix.lower()==".glb" else out/"source.glb"
    animation_contract=verify_clip_timing(timing_source,out/"runtime.glb")
    save_json(out/"animation_contract.json",animation_contract)
    if "gltf" in settings.get("export_formats",[]):
        export(out/"runtime.gltf","gltf")
    runtime_stats = inspect()
    lods = []
    if settings.get("generate_lods",False):
        if any(any(m.type == "ARMATURE" for m in o.modifiers) for o in mesh_objects()):
            lods.append({"status":"skipped","reason":"Skinned meshes need deformation-aware optimization and human topology review"})
        else:
            for level,ratio in enumerate(settings.get("lod_ratios",[0.65,0.35]),1):
                modifiers = []
                for o in mesh_objects():
                    mod = o.modifiers.new("Reviewable LOD","DECIMATE")
                    mod.ratio = ratio
                    mod.use_collapse_triangulate = True
                    delimit = {"MATERIAL","SEAM","SHARP"}
                    mod.delimit = delimit
                    modifiers.append((o,mod))
                export(out/f"lod{level}.glb",apply_modifiers=True)
                deps = bpy.context.evaluated_depsgraph_get()
                count = 0
                for o,mod in modifiers:
                    evaluated = o.evaluated_get(deps)
                    me = evaluated.to_mesh()
                    me.calc_loop_triangles()
                    count += len(me.loop_triangles)
                    evaluated.to_mesh_clear()
                lods.append({"level":level,"ratio":ratio,"triangles":count,"file":f"lod{level}.glb","visual_status":"pending","tradeoff":"Thin details and silhouette require comparison before acceptance"})
                for o,mod in modifiers:
                    o.modifiers.remove(mod)
    collision = None
    if settings.get("collision","none") == "convex" and not before["armatures"]:
        bm = bmesh.new()
        for o in mesh_objects():
            for v in o.data.vertices:
                bm.verts.new(o.matrix_world@v.co)
        result = bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
        interior = set(result.get("geom_interior",[])+result.get("geom_unused",[]))
        bmesh.ops.delete(bm,geom=[v for v in interior if isinstance(v,bmesh.types.BMVert) and v.is_valid],context="VERTS")
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        me = bpy.data.meshes.new("Convex collision")
        bm.to_mesh(me)
        bm.free()
        collision = bpy.data.objects.new("asset-col",me)
        bpy.context.scene.collection.objects.link(collision)
        collision["forge_collision"] = True
        bpy.ops.object.select_all(action="DESELECT")
        collision.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(out/"collision.glb"),export_format="GLB",use_selection=True)
        collision.hide_render = True
    # Geometry and effect objects remain distinct; separately export only named
    # imported components. No generated primitive geometry is used.
    if settings.get("separate_effects",False):
        groups = {"effects":[o for o in mesh_objects() if any(k in o.name.lower() for k in ("core","effect","glow","shard"))]}
        groups["structure"] = [o for o in mesh_objects() if o not in groups["effects"]]
        for label,objects in groups.items():
            if objects:
                bpy.ops.object.select_all(action="DESELECT")
                for o in objects:
                    o.select_set(True)
                bpy.ops.export_scene.gltf(filepath=str(out/f"{label}.glb"),export_format="GLB",use_selection=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"editable.blend"))
    report = {"before":before,"after":runtime_stats,"lods":lods,"settings":settings,"optimization":optimization,
              "triangle_budget":settings.get("triangle_budget"),"achieved_triangles":runtime_stats["triangles"],
              "budget_status":"within_target" if runtime_stats["triangles"]<=settings.get("triangle_budget",10**12) else "above_target_review_required",
              "processing_seconds":round(time.monotonic()-start,3),"blender_version":bpy.app.version_string,
              "visual_status":"pending","collision":"separate_convex_hull" if collision else "none",
              "notes":["Source preserved; selected optimization mode and quality-guard results recorded in optimization.json", "Existing skeleton and animation tracks preserved; no autorig invented"]}
    save_json(out/"processing.json",report)
    if settings.get("render_preview",True):
        render_views(out,False,settings.get("front_axis","-Z"))
    emit("complete")


if __name__ == "__main__":
    main()
