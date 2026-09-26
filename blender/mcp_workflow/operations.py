"""Operations run exclusively on Blender's main thread by the upstream bridge."""
import bpy
import bmesh
import math
import json
import re
import io
import time
from contextlib import redirect_stdout
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'output'


def output_path(filename):
    path = (OUTPUT / filename).resolve()
    if not path.is_relative_to(OUTPUT.resolve()):
        raise ValueError('Output path must stay inside output/')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def objects(names):
    if not names:
        raise ValueError('Provide explicit object names')
    return [bpy.context.scene.objects[name] for name in names]


def bounds(items):
    deps = bpy.context.evaluated_depsgraph_get()
    points = [ob.matrix_world @ Vector(p) for src in items
              if src.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}
              for ob in [src.evaluated_get(deps)] for p in ob.bound_box]
    if not points:
        raise ValueError('No renderable geometry in selection')
    return (Vector(tuple(min(p[i] for p in points) for i in range(3))),
            Vector(tuple(max(p[i] for p in points) for i in range(3))))


def inspect_scene():
    bpy.context.view_layer.update()
    result = []
    for ob in bpy.context.scene.objects:
        row = dict(name=ob.name, type=ob.type, parent=ob.parent.name if ob.parent else None,
                   collections=[c.name for c in ob.users_collection],
                   location=list(ob.location), rotation=list(ob.rotation_euler), scale=list(ob.scale),
                   dimensions=list(ob.dimensions), hidden_render=ob.hide_render,
                   modifiers=[dict(name=m.name, type=m.type) for m in ob.modifiers],
                   materials=[m.name if m else None for m in ob.data.materials] if hasattr(ob.data, 'materials') else [])
        if ob.type == 'MESH':
            evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            mesh.calc_loop_triangles()
            row['mesh'] = dict(vertices=len(mesh.vertices), polygons=len(mesh.polygons), triangles=len(mesh.loop_triangles))
            evaluated.to_mesh_clear()
        if ob.type == 'ARMATURE':
            row['bones'] = [dict(name=b.name, parent=b.parent.name if b.parent else None,
                                 head=list(b.head_local), tail=list(b.tail_local)) for b in ob.data.bones]
        result.append(row)
    materials = []
    for mat in bpy.data.materials:
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if mat.use_nodes else None
        materials.append(dict(name=mat.name, users=mat.users, nodes=mat.use_nodes,
                              color=list(bsdf.inputs['Base Color'].default_value) if bsdf else list(mat.diffuse_color),
                              metallic=bsdf.inputs['Metallic'].default_value if bsdf else mat.metallic,
                              roughness=bsdf.inputs['Roughness'].default_value if bsdf else mat.roughness))
    return dict(blender=bpy.app.version_string, file=bpy.data.filepath,
                scene=bpy.context.scene.name, units=bpy.context.scene.unit_settings.scale_length,
                objects=result, materials=materials)


def execute_python(code):
    runtime = ROOT / 'runtime'
    runtime.mkdir(exist_ok=True)
    stamp = str(time.time_ns())
    backup = runtime / 'before_last_edit.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(backup), copy=True)
    (runtime / f'edit_{stamp}.py').write_text(code, encoding='utf-8')
    capture = io.StringIO()
    namespace = {'bpy': bpy, '__name__': '__blender_mcp__'}
    with redirect_stdout(capture):
        exec(compile(code, '<mcp-edit>', 'exec'), namespace)
    bpy.context.view_layer.update()
    return dict(stdout=capture.getvalue(), recovery_copy=str(backup))


VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (-1, 0, 0), 'right': (1, 0, 0),
         'three_quarter': (0.65, -1, 0.35), 'rear_three_quarter': (-0.65, 1, 0.35), 'top': (0, 0, 1)}


def render_preview(names, label, views=('front', 'three_quarter'), resolution=800, focus=''):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', label):
        raise ValueError('Use a simple alphanumeric iteration label')
    if not 128 <= resolution <= 2048 or not views or len(views) > 8:
        raise ValueError('Use 1-8 views at 128-2048 pixels')
    if any(v not in VIEWS for v in views):
        raise ValueError('Unknown view')
    if focus and focus not in names:
        raise ValueError('Close-up focus must belong to the named asset selection')
    source = objects(names)
    low, high = bounds(objects([focus]) if focus else source)
    center = (low + high) / 2
    extent = max((high - low).length, 0.1)
    original = bpy.context.window.scene
    studio = bpy.data.scenes.new('_MCP_Inspection')
    generated = []
    meshes = []
    light_data = []
    camera_data = None
    world = None
    paths = []
    try:
        # Freeze evaluated geometry: armatures/modifiers render exactly as inspected.
        deps = bpy.context.evaluated_depsgraph_get()
        for src in source:
            if src.type not in {'MESH', 'CURVE', 'FONT', 'SURFACE'}:
                continue
            mesh = bpy.data.meshes.new_from_object(src.evaluated_get(deps), depsgraph=deps)
            meshes.append(mesh)
            clone = bpy.data.objects.new('_preview_' + src.name, mesh)
            clone.matrix_world = src.matrix_world.copy()
            studio.collection.objects.link(clone)
            generated.append(clone)
        bpy.context.window.scene = studio
        studio.render.engine = 'CYCLES'
        studio.cycles.samples = 32
        studio.cycles.use_denoising = True
        studio.render.resolution_x = resolution
        studio.render.resolution_y = resolution
        studio.render.resolution_percentage = 100
        studio.render.image_settings.file_format = 'PNG'
        studio.view_settings.view_transform = 'AgX'
        world = bpy.data.worlds.new('_MCP_Neutral')
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.16, 0.16, 0.16, 1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
        studio.world = world
        for name, offset, power, size in [
                ('Key', (-1.5, -2, 2.3), 380, 1.8),
                ('Fill', (1.6, -0.8, 0.2), 200, 1.5),
                ('Rim', (0.5, 1.5, 1.7), 450, 1.5)]:
            data = bpy.data.lights.new('_MCP_' + name, 'AREA')
            light_data.append(data)
            data.energy = power * extent * extent
            data.shape = 'DISK'
            data.size = size * extent
            light = bpy.data.objects.new(data.name, data)
            studio.collection.objects.link(light)
            generated.append(light)
            light.location = center + Vector(offset) * extent
            light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
        camera_data = bpy.data.cameras.new('_MCP_Camera')
        camera_data.type = 'ORTHO'
        camera = bpy.data.objects.new('_MCP_Camera', camera_data)
        studio.collection.objects.link(camera)
        generated.append(camera)
        studio.camera = camera
        corners = [Vector((x, y, z)) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
        for view in views:
            direction = Vector(VIEWS[view]).normalized()
            camera.location = center + direction * extent * 3
            camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
            rotation = camera.rotation_euler.to_matrix().transposed()
            projected = [rotation @ (p - center) for p in corners]
            width = max(p.x for p in projected) - min(p.x for p in projected)
            height = max(p.y for p in projected) - min(p.y for p in projected)
            camera_data.ortho_scale = max(width, height, 0.01) * 1.18
            camera_data.clip_end = extent * 10
            path = output_path(f'previews/{label}/{view}.png')
            studio.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            paths.append(str(path))
    finally:
        bpy.context.window.scene = original
        bpy.data.scenes.remove(studio)
        for ob in generated:
            bpy.data.objects.remove(ob, do_unlink=True)
        for mesh in meshes:
            bpy.data.meshes.remove(mesh)
        for data in light_data:
            bpy.data.lights.remove(data)
        if camera_data:
            bpy.data.cameras.remove(camera_data)
        if world:
            bpy.data.worlds.remove(world)
    return dict(images=paths, source_objects=names, focus=focus, renderer='Cycles 32 samples / AgX',
                bounds=[list(low), list(high)], convention='Z up, front -Y')


def validate_asset(names, require_armature=False, expected_length_m=0):
    selected = objects(names)
    bpy.context.view_layer.update()
    low, high = bounds(selected)
    unit = bpy.context.scene.unit_settings.scale_length
    size = (high - low) * unit
    warnings = []
    rows = []
    fingerprints = {}
    for ob in selected:
        issues = []
        if any(abs(s - 1) > 1e-5 for s in ob.scale):
            issues.append('Unapplied scale')
        if any(abs(r) > 1e-5 for r in ob.rotation_euler):
            issues.append('Unapplied rotation')
        if re.search(r'\.\d{3}$', ob.name) or ob.name in {'Cube', 'Sphere', 'Cylinder'}:
            issues.append('Generic or auto-suffixed name')
        row = dict(name=ob.name, issues=issues)
        if ob.type == 'MESH':
            ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = ev.to_mesh()
            mesh.calc_loop_triangles()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            row.update(vertices=len(mesh.vertices), polygons=len(mesh.polygons), triangles=len(mesh.loop_triangles),
                       boundary_edges=sum(e.is_boundary for e in bm.edges),
                       nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),
                       degenerate_faces=sum(f.calc_area() < 1e-12 for f in bm.faces),
                       loose_vertices=sum(not v.link_edges for v in bm.verts),
                       inconsistent_winding_edges=sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
                       signed_volume=bm.calc_volume(signed=True), materials=[m.name if m else None for m in mesh.materials])
            if row['nonmanifold_edges'] or row['degenerate_faces'] or row['loose_vertices']:
                issues.append('Topology needs review')
            if row['inconsistent_winding_edges'] or row['signed_volume'] < -1e-9:
                issues.append('Face winding/normals need review')
            if not mesh.materials or any(m is None for m in mesh.materials):
                issues.append('Missing material')
            fingerprint = tuple(sorted(tuple(round(v, 6) for v in ob.matrix_world @ vertex.co) for vertex in mesh.vertices))
            if fingerprint in fingerprints:
                issues.append('Coincident duplicate of ' + fingerprints[fingerprint])
            fingerprints[fingerprint] = ob.name
            bm.free()
            ev.to_mesh_clear()
        rows.append(row)
    if require_armature and not any(ob.type == 'ARMATURE' for ob in selected):
        warnings.append('Required armature missing')
    if expected_length_m and abs(max(size) - expected_length_m) / expected_length_m > .15:
        warnings.append('Length differs from requested scale by over 15%')
    if any(ob.type not in {'MESH', 'ARMATURE', 'EMPTY'} for ob in selected):
        warnings.append('Non-mesh geometry may require conversion before glTF export')
    return dict(dimensions_m=list(size), units=unit, objects=rows, warnings=warnings,
                triangles=sum(r.get('triangles', 0) for r in rows),
                limitations=['No self-intersection or semantic unwanted-geometry detector',
                             'Material appearance and Godot import require rendered/import checks',
                             'Boundary edges may be intentional; statistics are not art approval'])


def save_blend(filename):
    if not filename.endswith('.blend'):
        raise ValueError('Expected .blend')
    path = output_path(filename)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    return dict(path=str(path), bytes=path.stat().st_size)


def export_gltf(names, filename, merge_static_meshes=False):
    path = output_path(filename)
    if path.suffix not in {'.glb', '.gltf'}:
        raise ValueError('Expected .glb or .gltf')
    selected = objects(names)
    old_selection = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    temporary = []
    temporary_meshes = []
    if bpy.context.mode != 'OBJECT':
        raise ValueError('Switch to Object mode before export')
    try:
        bpy.ops.object.select_all(action='DESELECT')
        if merge_static_meshes:
            if any(ob.type != 'MESH' or any(m.type == 'ARMATURE' for m in ob.modifiers) for ob in selected):
                raise ValueError('Static merge only supports unrigged mesh selections')
            deps = bpy.context.evaluated_depsgraph_get()
            for ob in selected:
                mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(deps), depsgraph=deps)
                temporary_meshes.append(mesh)
                clone = bpy.data.objects.new('_Export_' + ob.name, mesh)
                clone.matrix_world = ob.matrix_world.copy()
                bpy.context.scene.collection.objects.link(clone)
                temporary.append(clone)
                clone.select_set(True)
            bpy.context.view_layer.objects.active = temporary[0]
            bpy.ops.object.join()
            combined = bpy.context.object
            combined.name = 'Oathkeeper_Sword'
            temporary = [combined]
            selected = [combined]
        for ob in selected:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = selected[0]
        bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB' if path.suffix == '.glb' else 'GLTF_SEPARATE',
                                  use_selection=True, use_active_scene=True, export_apply=True, export_yup=True, export_cameras=False,
                                  export_lights=False)
    finally:
        for ob in temporary:
            bpy.data.objects.remove(ob, do_unlink=True)
        for mesh in temporary_meshes:
            # join() may already have removed source datablocks.
            try:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            except ReferenceError:
                pass
        bpy.ops.object.select_all(action='DESELECT')
        for ob in old_selection:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = active
    return dict(path=str(path), bytes=path.stat().st_size, selected=names)


HANDLERS = {f.__name__: f for f in (inspect_scene, execute_python, render_preview, validate_asset, save_blend, export_gltf)}
