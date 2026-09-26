class_name MountData
extends Resource
@export var id: StringName
@export var display_name: String
@export var speed: float = 8.8
@export var rider_height: float = 0.5
@export var visual: PackedScene

static func find(id_to_find: StringName) -> MountData:
	# Definitions are extensible without adding mount-type branches to the controller.
	for file in DirAccess.get_files_at("res://data/mounts"):
		if file.ends_with(".tres"):
			var definition := load("res://data/mounts/" + file) as MountData
			if definition and definition.id == id_to_find: return definition
	return null
