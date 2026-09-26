class_name PlayerSkills
extends Node
## Authoritative skill commitment/cooldowns; input and UI submit the same request.
signal changed
signal resolved(context: SkillContext)
const REFERENCE = preload("res://data/classes/turnwarden.tres")
var actor: ActorBody
var specialization: SpecializationData
var ranks: Dictionary = {}
var cooldowns: Dictionary = {}
var current: SkillContext
var elapsed: float = 0
var executed: bool = false
var serial: int = 0
var armed: SkillData
var preview: MeshInstance3D
var feedback: String = ""
var motion_direction := Vector3.ZERO
var motion_speed: float = 0
var motion_remaining: float = 0
var last_hits: int = 0
var telegraph: MeshInstance3D
func _ready() -> void:
	select_reference()
func select_reference() -> bool:
	if specialization != null:
		if not SafeArea.protects(actor) or busy() or actor.combat.is_attacking(): return false
		return true # Reselecting cannot reset cooldowns.
	specialization = REFERENCE
	for skill in specialization.skills: ranks[String(skill.id)] = 1
	changed.emit()
	return true
func busy() -> bool:
	return current != null
func remaining(skill: SkillData) -> float:
	return float(cooldowns.get(String(skill.id), 0))
func unavailable(skill: SkillData) -> String:
	if specialization == null or not specialization.skills.has(skill): return "Skill is not learned."
	if not actor.health.is_alive(): return "You have fallen."
	if actor.ui_open: return "Close the open panel first."
	if busy() or actor.combat.is_attacking(): return "Finish the committed action first."
	if remaining(skill) > 0: return "Skill is cooling down."
	var weapon: ItemStack = actor.equipment.slots.get(&"weapon")
	if weapon == null or (not specialization.weapon_families.has(weapon.definition().weapon_family) or not specialization.base_class.weapon_families.has(weapon.definition().weapon_family)): return "Equip a sword."
	return ""
func activate(index: int) -> bool:
	if specialization == null or index < 0 or index >= specialization.skills.size(): return false
	var skill := specialization.skills[index]
	var error := unavailable(skill)
	if not error.is_empty(): return reject(error)
	if skill.targeting in ["ground", "direction"]:
		cancel_aim()
		armed = skill
		actor.world_interaction.target = null
		actor.world_interaction.kind = &""
		actor.navigation.cancel()
		preview = SkillVFX.ring(skill.radius if skill.targeting == "ground" else 0.45, skill.color)
		actor.get_parent().add_child(preview)
		feedback = "Choose ground for %s. Esc cancels." % skill.display_name
		changed.emit()
		return true
	return request(skill, actor.world_interaction.selected_enemy)
func reject(message: String) -> bool:
	feedback = message
	changed.emit()
	return false
func request(skill: SkillData, target: ActorBody = null, point: Vector3 = Vector3.ZERO) -> bool:
	var error := unavailable(skill)
	if not error.is_empty(): return reject(error)
	var context := SkillContext.new()
	context.actor = actor
	context.skill = skill
	context.target = target
	context.point = point
	context.origin = actor.global_position
	context.direction = -actor.global_basis.z
	context.rank = int(ranks.get(String(skill.id), 1))
	context.attack = actor.stats.value(&"attack") * (1.0 + (context.rank - 1) * skill.rank_scaling)
	error = SkillTargeting.validate(context)
	if not error.is_empty(): return reject(error)
	if actor.mounts: actor.mounts.dismount("Dismounted to fight")
	if skill.targeting in ["selected", "direction"]:
		var offset := context.point - context.origin
		offset.y = 0
		if offset.length_squared() > 0.001: context.direction = offset.normalized()
	actor.rotation.y = atan2(-context.direction.x, -context.direction.z)
	context.answer = skill.consumes_answer and actor.statuses.has(&"answer")
	if context.answer: actor.statuses.remove(&"answer")
	actor.navigation.cancel()
	# Keep selection, stop automatic attacks/travel. No unseen attack after a skill.
	actor.world_interaction.target = null
	actor.world_interaction.kind = &""
	actor.combat.cancel()
	cancel_aim()
	current = context
	telegraph = SkillVFX.ring(skill.radius if skill.shape == "arc" or skill.targeting == "ground" else 0.8, skill.color.darkened(0.3), skill.angle if skill.shape == "arc" else 360)
	actor.get_parent().add_child(telegraph)
	telegraph.global_position = context.point if skill.targeting == "ground" else context.origin
	telegraph.rotation.y = actor.rotation.y
	elapsed = 0
	executed = false
	serial += 1
	cooldowns[String(skill.id)] = skill.cooldown
	feedback = skill.display_name
	changed.emit()
	return true
func cancel_aim() -> void:
	armed = null
	if is_instance_valid(preview): preview.queue_free()
	preview = null
func cancel_transient() -> void:
	if is_instance_valid(telegraph): telegraph.queue_free()
	current = null
	motion_remaining = 0
	cancel_aim()
	actor.statuses.clear()
	for area in get_tree().get_nodes_in_group("skill_areas"):
		if area.caster == actor: area.queue_free()
	changed.emit()
func consume_motion(delta: float) -> Vector3:
	if motion_remaining <= 0: return Vector3.ZERO
	var portion := minf(delta, motion_remaining)
	motion_remaining -= portion
	return motion_direction * motion_speed * portion / maxf(delta, 0.0001)
func handle_world_click(point: Vector2) -> void:
	if armed == null: return
	var hit := WorldPicker.pick(actor.world_interaction.camera, point)
	if hit.is_empty() or hit.kind != &"terrain" or hit.get("normal", Vector3.UP).y < 0.7:
		reject("Choose clear ground, not an entity.")
		return
	request(armed, null, hit.position)
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_6:
			activate(event.physical_keycode - KEY_1)
			get_viewport().set_input_as_handled()
		elif event.physical_keycode == KEY_F6:
			feedback = "Ironvow / Turnwarden selected." if select_reference() else "Choose specialization at the refuge outside combat."
			get_viewport().set_input_as_handled()
		elif event.physical_keycode == KEY_ESCAPE and armed:
			cancel_aim()
			get_viewport().set_input_as_handled()
func _physics_process(delta: float) -> void:
	for id in cooldowns.keys(): cooldowns[id] = maxf(0, float(cooldowns[id]) - delta)
	if not actor.health.is_alive():
		if busy() or armed: cancel_transient()
		return
	if current == null: return
	elapsed += delta
	if not executed and elapsed >= current.skill.windup:
		executed = true
		if is_instance_valid(telegraph): telegraph.queue_free()
		var targets := SkillTargeting.targets(current)
		for effect in current.skill.effects: effect.execute(current, targets)
		last_hits = current.hit_count
		SkillVFX.flash(actor.get_parent(), actor.global_position, current.skill.radius if current.skill.shape == "arc" else 0.65, current.skill.color, current.skill.angle if current.skill.shape == "arc" else 360, actor.rotation.y)
		resolved.emit(current)
	if current and elapsed >= current.skill.windup + current.skill.recovery:
		current = null
		changed.emit()
func _process(_delta: float) -> void:
	if armed and is_instance_valid(preview):
		var hit := WorldPicker.pick(actor.world_interaction.camera, get_viewport().get_mouse_position())
		preview.visible = not hit.is_empty() and hit.kind == &"terrain"
		if preview.visible:
			preview.global_position = hit.position
func snapshot() -> Dictionary:
	return {"class": String(specialization.class_id), "specialization": String(specialization.id), "ranks": ranks.duplicate(), "cooldowns": cooldowns.duplicate()}
static func default_snapshot() -> Dictionary:
	var initial: Dictionary = {}
	for skill in REFERENCE.skills: initial[String(skill.id)] = 1
	return {"class": String(REFERENCE.class_id), "specialization": String(REFERENCE.id), "ranks": initial, "cooldowns": {}}
static func valid_snapshot(data: Variant) -> bool:
	if not data is Dictionary or data.get("class") != String(REFERENCE.class_id) or data.get("specialization") != String(REFERENCE.id): return false
	if not data.get("ranks") is Dictionary or not data.get("cooldowns") is Dictionary: return false
	if data.ranks.size() != REFERENCE.skills.size(): return false
	for skill in REFERENCE.skills:
		var rank: Variant = data.ranks.get(String(skill.id))
		if not rank is float and not rank is int: return false
		if rank < 1 or rank > skill.maximum_rank or float(rank) != floorf(float(rank)): return false
	for id in data.cooldowns:
		var skill: SkillData
		for candidate in REFERENCE.skills:
			if String(candidate.id) == id: skill = candidate
		var value: Variant = data.cooldowns[id]
		if skill == null or (not value is float and not value is int): return false
		if not is_finite(float(value)) or value < 0 or value > skill.cooldown: return false
	return true
func restore(data: Dictionary) -> void:
	cancel_transient()
	specialization = REFERENCE
	ranks = data.ranks.duplicate()
	cooldowns = data.cooldowns.duplicate()
	changed.emit()
