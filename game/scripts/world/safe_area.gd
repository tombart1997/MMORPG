class_name SafeArea
extends Node3D
@export var radius: float = 7.5

func _ready() -> void:
	add_to_group("safe_areas")

func contains(point: Vector3) -> bool:
	return Vector2(point.x - global_position.x, point.z - global_position.z).length() <= radius

static func protects(actor: Node3D) -> bool:
	if not is_instance_valid(actor) or not actor.is_inside_tree(): return false
	for area in actor.get_tree().get_nodes_in_group("safe_areas"):
		if area.contains(actor.global_position): return true
	return false
