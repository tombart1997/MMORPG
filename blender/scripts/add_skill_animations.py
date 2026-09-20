"""Add/replace only Turnwarden clips in the existing traveler source; retain all other assets."""
import importlib.util
import json
from pathlib import Path
import bpy
spec = importlib.util.spec_from_file_location("builder", Path(__file__).with_name("build_characters.py"))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
bpy.ops.wm.open_mainfile(filepath=str(builder.SOURCE / "traveler.blend"))
bpy.context.preferences.filepaths.save_version = 0
rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
for track in list(rig.animation_data.nla_tracks):
    if track.name.startswith("skill_"): rig.animation_data.nla_tracks.remove(track)
builder.animations(rig, False, only_skills=True)
manifest = builder.EXPORT / "manifest.json"
builder.MANIFEST = json.loads(manifest.read_text(encoding="utf-8"))
builder.save_export("traveler", rig)
manifest.write_text(json.dumps(builder.MANIFEST, indent=2) + "\n", encoding="utf-8")
print("TURNWARDEN ANIMATIONS EXPORTED")
