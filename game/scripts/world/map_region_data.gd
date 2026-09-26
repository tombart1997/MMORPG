class_name MapRegionData
extends Resource
@export var id: StringName
@export var display_name: String
@export var bounds: Rect2
@export var roads: PackedVector2Array
@export var landmarks: Array[Dictionary] = []

static func regions() -> Array[MapRegionData]:
	var result: Array[MapRegionData] = []
	for file in DirAccess.get_files_at("res://data/maps"):
		if file.ends_with(".tres"):
			var region := load("res://data/maps/" + file) as MapRegionData
			if region: result.append(region)
	return result
