class_name ReviewedModels
extends RefCounted
## Visual-only immutable versions. Missing exports retain the working scene.
static var mappings: Dictionary = {}
static var loaded := false
static var scenes: Dictionary = {}

static func path_for(original: String) -> String:
	if not loaded:
		loaded=true
		var registry:="res://data/visuals/reviewed_versions.json"
		if FileAccess.file_exists(registry):
			var value=JSON.parse_string(FileAccess.get_file_as_string(registry))
			if value is Dictionary:mappings=value.get("mappings",{})
	var record: Dictionary=mappings.get(original,{})
	var replacement:=String(record.get("path",original))
	return replacement if ResourceLoader.exists(replacement) else original

static func scene_for(original: String) -> PackedScene:
	var path:=path_for(original)
	if not scenes.has(path):scenes[path]=load(path) as PackedScene
	return scenes[path]

static func resolve(scene: PackedScene) -> PackedScene:
	if scene==null:return null
	return scene_for(scene.resource_path) if not scene.resource_path.is_empty() else scene

static func is_fallback(original: String) -> bool:
	path_for(original)
	return bool(mappings.get(original,{}).get("fallback",false))
