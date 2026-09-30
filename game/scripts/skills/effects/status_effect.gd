class_name SkillStatusEffect
extends SkillEffect
@export var status: StringName
@export var duration: float = 4
@export var to_caster: bool = false
@export var magnitude: float = 1
func execute(context: SkillContext, targets: Array[ActorBody]) -> void:
	if to_caster:
		context.actor.statuses.add(status, duration, magnitude, context.actor)
		return
	for target in targets: target.statuses.add(status, duration, magnitude, context.actor)
