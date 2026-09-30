class_name SkillArea
extends Node3D
var caster: ActorBody
var id: StringName
var radius: float
var remaining: float
var slow: float
var shelter: float
var color: Color
var tick: float = 0
var damage: float = 0
var damage_interval: float = .5
var damage_clock: float = 0
var follow_caster: bool = false
func _ready() -> void:
	add_to_group("skill_areas")
	add_child(SkillVFX.ring(radius, color))
	if id == &"standard_of_ash": SkillVFX.spectacle(self, "fire", Vector3.ZERO, caster, remaining, radius)
	elif id == &"gate_sweep": SkillVFX.spectacle(self, "spin", Vector3.ZERO, caster, remaining, radius)
func _physics_process(delta: float) -> void:
	remaining -= delta
	if remaining <= 0 or not is_instance_valid(caster) or not caster.health.is_alive(): queue_free(); return
	if follow_caster: global_position = caster.global_position
	damage_clock -= delta
	tick -= delta
	if tick > 0: return
	tick = 0.05
	var burn := damage_clock <= 0
	if burn: damage_clock += damage_interval
	for actor: ActorBody in get_tree().get_nodes_in_group(caster.opponents):
		if actor.global_position.distance_to(global_position) <= radius and SkillTargeting.line_clear(actor, global_position, actor.global_position):
			actor.statuses.add(&"zone_slow", 0.25, slow, caster)
			if burn and damage > 0:
				var before := actor.health.current
				if actor.health.apply_damage(damage, caster): SkillVFX.damage_number(actor, before-actor.health.current, color)
	if shelter > 0 and caster.global_position.distance_to(global_position) <= radius and SkillTargeting.line_clear(caster, global_position, caster.global_position): caster.statuses.add(&"shelter", 0.25, shelter, caster)
