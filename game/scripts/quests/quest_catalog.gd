class_name QuestCatalog
extends RefCounted
static var definitions: Dictionary = {}
static func all() -> Dictionary:
	if definitions.is_empty():
		for file in DirAccess.get_files_at("res://data/quests"):
			file = file.trim_suffix(".remap")
			if not file.ends_with(".tres"): continue
			var data := load("res://data/quests/" + file) as QuestData
			if data and data.id != &"": definitions[data.id] = data
	return definitions
