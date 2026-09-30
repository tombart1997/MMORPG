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
var queued_index: int = -1
var queue_remaining: float = 0
const INPUT_BUFFER := .4
const LEGACY_COOLDOWNS := {"riving_stroke":5.0,"held_line":10.0,"heelturn":8.0,"gate_sweep":9.0,"standard_of_ash":18.0,"due_return":12.0}
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
	if busy(): return "Skill in progress."
	if remaining(skill) > 0: return "Skill is cooling down."
	var weapon: ItemStack = actor.equipment.slots.get(&"weapon")
	if weapon == null or (not specialization.weapon_families.has(weapon.definition().weapon_family) or not specialization.base_class.weapon_families.has(weapon.definition().weapon_family)): return "Equip a sword."
	return ""
func activate(index: int) -> bool:
	if specialization == null or index < 0 or index >= specialization.skills.size(): return false
	if not actor.health.is_alive() or actor.ui_open: return false
	var skill := specialization.skills[index]
	# One replaceable buffered intent, including a cooldown about to expire.
	if busy() or (remaining(skill) > 0 and remaining(skill) <= INPUT_BUFFER):
		if remaining(skill) > INPUT_BUFFER: return reject("Skill is cooling down.")
		queued_index = index
		queue_remaining = INPUT_BUFFER
		feedback = "Next: " + skill.display_name
		return true
	var target: ActorBody = actor.world_interaction.selected_enemy
	var point := actor.global_position
	if skill.targeting == "direction":
		var direction := travel_direction()
		# Shorten to the available lane instead of refusing a dash near a wall.
		var found := false
		for step in range(10, 0, -1):
			var candidate := actor.global_position + direction * skill.reach * step / 10.0
			var probe := SkillContext.new()
			probe.actor = actor
			probe.skill = skill
			probe.point = candidate
			if SkillTargeting.validate(probe).is_empty():
				point = probe.point
				found = true
				break
		if not found: return reject("No room to dash in that direction.")
	return request(skill, target, point)

func travel_direction() -> Vector3:
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	for child in actor.get_children():
		if child is PlayerController and input.length_squared() > .01:
			return Vector3(input.x,0,input.y).rotated(Vector3.UP,child.rig.yaw).normalized()
	if actor.navigation and actor.navigation.active:
		var direction := actor.navigation.destination - actor.global_position
		direction.y = 0
		if direction.length_squared() > .01: return direction.normalized()
	return -actor.global_basis.z

func clear_buffer() -> void:
	queued_index = -1
	queue_remaining = 0

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
	context.point = actor.global_position if skill.targeting == "self" else point
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
	if skill.targeting == "facing":
		# Selection supports attacking while strafing; without one, cast in travel direction.
		context.direction = travel_direction()
		if is_instance_valid(target) and target.health.is_alive() and target.faction == actor.opponents and actor.global_position.distance_to(target.global_position) <= skill.reach and SkillTargeting.line_clear(actor,actor.global_position,target.global_position):
			context.direction = (target.global_position - actor.global_position).normalized()
		context.direction.y = 0
		context.direction = context.direction.normalized()
	actor.rotation.y = atan2(-context.direction.x, -context.direction.z)
	context.answer = skill.consumes_answer and actor.statuses.has(&"answer")
	if context.answer: actor.statuses.remove(&"answer")
	if skill.targeting == "direction": actor.navigation.cancel()
	# Preserve click travel while a skill animates; stop only the enemy autoattack intent.
	actor.world_interaction.target = null
	actor.world_interaction.kind = &"terrain" if actor.navigation.active else &""
	actor.combat.cancel()
	for child in actor.get_children():
		if child is PlayerController: child.stop_auto_attack()
	clear_buffer()
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
	clear_buffer()
	for effect in get_tree().get_nodes_in_group("skill_spectacles"):
		if effect.caster == actor: effect.queue_free()
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
		elif event.physical_keycode == KEY_ESCAPE:
			clear_buffer()
			cancel_aim()
			get_viewport().set_input_as_handled()
func _physics_process(delta: float) -> void:
	for id in cooldowns.keys(): cooldowns[id] = maxf(0, float(cooldowns[id]) - delta)
	if not actor.health.is_alive():
		if busy() or armed: cancel_transient()
		return
	if actor.ui_open: clear_buffer()
	if queued_index >= 0:
		queue_remaining -= delta
		if queue_remaining <= 0: clear_buffer()
		elif current == null and remaining(specialization.skills[queued_index]) <= 0:
			var next := queued_index
			clear_buffer()
			activate(next)
	if current == null: return
	elapsed += delta
	if is_instance_valid(telegraph) and current.skill.targeting != "ground": telegraph.global_position = actor.global_position
	if not executed and elapsed >= current.skill.windup:
		executed = true
		if is_instance_valid(telegraph): telegraph.queue_free()
		if current.skill.targeting == "self": current.point = actor.global_position
		var targets := SkillTargeting.targets(current)
		for effect in current.skill.effects: effect.execute(current, targets)
		last_hits = current.hit_count
		SkillVFX.cast(current)
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
		if not is_finite(float(value)) or value < 0 or value > maxf(skill.cooldown, float(LEGACY_COOLDOWNS.get(id, 0))): return false
	return true
func restore(data: Dictionary) -> void:
	cancel_transient()
	specialization = REFERENCE
	ranks = data.ranks.duplicate()
	cooldowns = data.cooldowns.duplicate()
	for skill in specialization.skills:
		if cooldowns.has(String(skill.id)): cooldowns[String(skill.id)] = minf(float(cooldowns[String(skill.id)]), skill.cooldown)
	changed.emit()
