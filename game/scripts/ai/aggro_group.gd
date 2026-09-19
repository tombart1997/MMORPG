class_name AggroGroup
extends Node
## Explicit encounter membership; striking any member alerts all living members.
signal alerted(target: Node3D)
var members: Array[ActorBody] = []
var target: ActorBody

func register(actor: ActorBody) -> void:
	members.append(actor)
	actor.health.damaged.connect(_on_member_damaged)

func _on_member_damaged(_amount: float, source: Node3D) -> void:
	if source is ActorBody and source.health.is_alive():
		target = source
		alerted.emit(target)

func has_target() -> bool:
	return is_instance_valid(target) and target.health.is_alive()

func living_count() -> int:
	var count := 0
	for member in members:
		if is_instance_valid(member) and member.health.is_alive():
			count += 1
	return count
