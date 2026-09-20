class_name SkillAreaEffect
extends SkillEffect
@export var radius: float = 2.7
@export var duration: float = 5.0
@export var slow: float = 0.25
@export var shelter: float = 0.0
@export var at_origin: bool = false
@export var replace_previous: bool = false
func execute(context: SkillContext, _targets: Array[ActorBody]) -> void:
	if replace_previous:
		for area in context.actor.get_tree().get_nodes_in_group("skill_areas"):
			if area.caster == context.actor and area.id == context.skill.id: area.queue_free()
	var area := SkillArea.new()
	area.caster = context.actor
	area.id = context.skill.id
	area.radius = radius
	area.remaining = duration
	area.slow = slow
	area.shelter = shelter
	area.color = context.skill.color
	context.actor.get_parent().add_child(area)
	area.global_position = context.origin if at_origin else context.point
