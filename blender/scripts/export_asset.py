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
if builder.SOURCE.resolve() not in source.parents:
    raise ValueError("Source must be inside this project's blender/characters directory")
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
builder.save_export(args[0], rigs[0] if rigs else None, save_source=False)
manifest_path.write_text(json.dumps(builder.MANIFEST, indent=2) + "\n", encoding="utf-8")
print("IRONFIELD SINGLE ASSET EXPORT COMPLETE")
