class_name SkillStatusEffect
extends SkillEffect
@export var status: StringName
@export var duration: float = 4
@export var magnitude: float = 1
func execute(context: SkillContext, targets: Array[ActorBody]) -> void:
	for target in targets: target.statuses.add(status, duration, magnitude, context.actor)
