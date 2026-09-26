"""Export an existing project-local .blend without regenerating or saving its source.

blender --background <source.blend> --python-exit-code 1 --python export_asset.py -- <asset_name>
All outputs are restricted to game/assets/characters/; see tools/build_assets.ps1 -Asset.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path
import bpy

script = Path(__file__).resolve().with_name("build_characters.py")
spec = importlib.util.spec_from_file_location("ironfield_builder", script)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) != 1 or not re.fullmatch(r"[a-z][a-z0-9_]*", args[0]):
    raise ValueError("Pass exactly one snake_case asset name after --")
source = Path(bpy.data.filepath).resolve()
benchmark_source = builder.ROOT / 'blender' / 'benchmark'
if builder.SOURCE.resolve() not in source.parents and benchmark_source.resolve() not in source.parents:
    raise ValueError("Source must be inside this project's Blender art directories")
rigs = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
if len(rigs) > 1:
    raise ValueError("One rig per character asset")
if bpy.context.scene.render.fps != builder.FPS:
    raise ValueError("Source must use the pipeline's 60 FPS time base")
if rigs:
    rig = rigs[0]
    if not rig.animation_data:
        raise ValueError("Rig requires named NLA animation tracks")
    for track in rig.animation_data.nla_tracks:
        if len(track.strips) != 1 or track.strips[0].frame_start != 0 or track.strips[0].action_frame_start != 0:
            raise ValueError("Each clip needs one NLA strip starting at frame 0: " + track.name)
manifest_path = builder.EXPORT / "manifest.json"
if manifest_path.exists():
    builder.MANIFEST = json.loads(manifest_path.read_text(encoding="utf-8"))
# Benchmark sources stay editable; join production pieces only in this export session.
if benchmark_source.resolve() in source.parents:
    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    editable_count = len(parts)
    if args[0] != 'briarwake' and len(parts) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in parts: obj.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        bpy.context.object.name = args[0] + ('Skin' if rigs else 'Mesh')
    if args[0] not in ('briarling','turnwarden_v2','turnwarden_v2_sword','traveler_guard'):
        builder.EXPORT = builder.ROOT / 'game' / 'assets' / 'benchmark'
builder.save_export(args[0], rigs[0] if rigs else None, save_source=False)
if builder.EXPORT == builder.ROOT / 'game' / 'assets' / 'characters':
    manifest_path.write_text(json.dumps(builder.MANIFEST, indent=2) + "\n", encoding="utf-8")
if benchmark_source.resolve() in source.parents:
    parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    report_path = builder.ROOT / 'game' / 'assets' / 'benchmark' / 'manifest.json'
    report = json.loads(report_path.read_text())
    info = builder.MANIFEST['assets'][args[0]]
    info.update({'runtime_meshes': len(parts), 'editable_meshes': editable_count, 'source_meshes': editable_count,
                 'skinned_meshes': sum(bool(o.modifiers.get('Skin')) for o in parts),
                 'surfaces': sum(len(set(p.material_index for p in o.data.polygons)) for o in parts)})
    report[args[0]] = info
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    if builder.EXPORT == builder.ROOT / 'game' / 'assets' / 'characters':
        manifest_path.write_text(json.dumps(builder.MANIFEST, indent=2)+'\n')
print("IRONFIELD SINGLE ASSET EXPORT COMPLETE")
