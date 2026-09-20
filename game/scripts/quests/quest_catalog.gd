class_name QuestCatalog
extends RefCounted
static var definitions: Dictionary = {}
static func all() -> Dictionary:
	if definitions.is_empty():
		for id in ["welcome", "briar_watch", "first_temper"]:
			var data := load("res://data/quests/" + id + ".tres") as QuestData
			definitions[data.id] = data
	return definitions
