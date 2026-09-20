class_name SkillMovementEffect
extends SkillEffect
@export var duration: float = 0.25
func execute(context: SkillContext, _targets: Array[ActorBody]) -> void:
	context.actor.skills.motion_direction = context.direction
	context.actor.skills.motion_speed = context.origin.distance_to(context.point) / duration
	context.actor.skills.motion_remaining = duration
