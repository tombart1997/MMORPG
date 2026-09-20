class_name StatusVisual
extends Node3D
var actor: ActorBody
var guard: MeshInstance3D
var answer: MeshInstance3D
var opening: MeshInstance3D
var slow: MeshInstance3D
func _ready() -> void:
	actor = get_parent() as ActorBody
	guard = SkillVFX.ring(1.0, Color(0.3, 0.7, 1), 120)
	add_child(guard)
	answer = SkillVFX.ring(0.6, Color.GOLD)
	add_child(answer)
	opening = SkillVFX.ring(0.42, Color(1, 0.65, 0.2))
	add_child(opening)
	slow = SkillVFX.ring(0.5, Color(0.4, 0.7, 0.95), 240)
	add_child(slow)
func _process(_delta: float) -> void:
	opening.visible = actor.statuses.has(&"open")
	slow.visible = actor.statuses.movement_multiplier() < 1
	guard.visible = actor.statuses.has(&"guard")
	answer.visible = actor.statuses.has(&"answer")
	if guard.visible:
		var direction: Vector3 = actor.statuses.entries[&"guard"].direction
		guard.global_rotation.y = atan2(-direction.x, -direction.z)
