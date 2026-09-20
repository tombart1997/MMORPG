class_name AggroGroup
extends Node
## Explicit encounter membership; striking any member alerts all living members.
signal alerted(target: Node3D)
var members: Array[ActorBody] = []
var target: ActorBody

func register(actor: ActorBody) -> void:
	members.append(actor)
	actor.health.damaged.connect(_on_member_damaged)
	actor.statuses.hostile_applied.connect(func(source): _on_member_damaged(0, source))

func _on_member_damaged(_amount: float, source: Node3D) -> void:
	if source is ActorBody and source.health.is_alive() and not SafeArea.protects(source):
		target = source
		alerted.emit(target)

func has_target() -> bool:
	return is_instance_valid(target) and target.health.is_alive() and not SafeArea.protects(target)

func living_count() -> int:
	var count := 0
	for member in members:
		if is_instance_valid(member) and member.health.is_alive():
			count += 1
	return count

func disengage() -> void:
	target = null
	for member in members:
		if is_instance_valid(member):
			member.combat.cancel()
			member.velocity.x = 0
			member.velocity.z = 0
