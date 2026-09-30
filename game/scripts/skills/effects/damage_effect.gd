class_name SkillDamageEffect
extends SkillEffect
@export var coefficient: float = 1.0
@export var open_bonus: float = 0.0
@export var consume_open: bool = false
@export var answer_bonus: float = 0.0
@export var answer_heal: float = 0.0
@export var answer_push: float = 0.0
@export var push_distance: float = 0.0
@export var heal_on_hit: float = 0.0
func execute(context: SkillContext, targets: Array[ActorBody]) -> void:
	for target in targets:
		var scale := coefficient + (open_bonus if target.statuses.has(&"open") else 0.0) + (answer_bonus if context.answer else 0.0)
		var before := target.health.current
		if target.health.apply_damage(context.attack * scale, context.actor):
			context.hit_count += 1
			if consume_open: target.statuses.remove(&"open")
			if context.answer and answer_push > 0: target.statuses.push(target.global_position - context.actor.global_position, answer_push, 0.2)
			if push_distance > 0: target.statuses.push(target.global_position - context.actor.global_position, push_distance, .18)
			SkillVFX.hit(context, target, before - target.health.current)
	if context.hit_count > 0 and heal_on_hit > 0: context.actor.health.heal(context.attack * heal_on_hit)
	if context.hit_count > 0 and context.answer and answer_heal > 0: context.actor.health.heal(context.attack * answer_heal)
