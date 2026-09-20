class_name ItemCatalog
extends RefCounted
static var definitions: Dictionary = {}

static func get_item(id: StringName) -> ItemData:
	if definitions.is_empty():
		for file in DirAccess.get_files_at("res://data/items"):
			file = file.trim_suffix(".remap")
			if file.ends_with(".tres"):
				var item := load("res://data/items/" + file) as ItemData
				assert(item != null and item.id != &"" and not definitions.has(item.id), "Invalid/duplicate item ID")
				definitions[item.id] = item
	return definitions.get(id) as ItemData
