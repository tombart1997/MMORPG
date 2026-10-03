class_name QuestData
extends Resource
@export var id: StringName
@export var title: String
@export_multiline var description: String
@export var giver: StringName
@export var turn_in: StringName
@export var prerequisites: Array[StringName] = []
@export var required_level: int = 1
@export var objectives: Array[Dictionary] = []
@export var gold: int = 0
@export var xp: int = 0
@export var items: Dictionary = {}
