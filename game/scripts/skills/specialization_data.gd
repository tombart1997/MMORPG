class_name SpecializationData
extends Resource
@export var base_class: CharacterClassData
var class_id: StringName:
	get: return base_class.id
@export var id: StringName
@export var display_name: String
@export var weapon_families: Array[StringName] = [&"sword"]
@export var skills: Array[SkillData] = []
