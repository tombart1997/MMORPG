class_name MeleeCombat
extends Node
## Shared by players and enemies. Facing is locked by controllers during a swing.
signal phase_changed(phase_name: String)
signal hit_landed(target: Node3D)
enum Phase { IDLE, WINDUP, ACTIVE, RECOVERY }
@export var attack: AttackData
var actor: CharacterBody3D
var target_group: StringName
var phase: Phase = Phase.IDLE
var phase_elapsed: float = 0.0
var hit_ids: Dictionary = {}
var swing_hits: int = 0
var total_hits: int = 0
var sequence: Array[AttackData] = []
var sequence_index: int = -1
var combo_grace: float = 0.65
var idle_elapsed: float = 1.0
var queued: bool = false
var motion_elapsed: float = 0.0
var attack_direction := Vector3.FORWARD
var swing_serial: int = 0
var swing_speed: float = 1.0
var swing_damage: float = 0.0

func _ready() -> void:
	actor = get_parent() as CharacterBody3D

func is_attacking() -> bool:
	return phase != Phase.IDLE

func request_attack() -> bool:
	if is_attacking() or not actor.health.is_alive() or attack == null or (actor.skills and actor.skills.busy()):
		return false
	if not sequence.is_empty():
		sequence_index = 0 if idle_elapsed > combo_grace else (sequence_index + 1) % sequence.size()
		attack = sequence[sequence_index]
	swing_speed = actor.stats.value(&"attack_speed") if actor.stats else 1.0
	if actor.mounts and actor.mounts.mounted: swing_speed *= PlayerMount.ATTACK_SPEED_MULTIPLIER
	swing_damage = attack.damage * actor.stats.value(&"attack") / 25.0 if actor.stats else attack.damage
	idle_elapsed = 0.0
	motion_elapsed = 0.0
	attack_direction = -actor.global_basis.z
	queued = false
	hit_ids.clear()
	swing_serial += 1
	swing_hits = 0
	_set_phase(Phase.WINDUP)
	return true

func cancel() -> void:
	queued = false
	idle_elapsed = combo_grace + 1.0
	_set_phase(Phase.IDLE)

func queue_followup() -> void:
	# One buffered click during recovery; no unlimited input queue.
	if phase == Phase.RECOVERY and not sequence.is_empty():
		queued = true

func movement_locked() -> bool:
	return is_attacking() and (phase != Phase.RECOVERY or
		phase_elapsed < attack.recovery * attack.recovery_movement_unlock)

func consume_motion_velocity(delta: float) -> Vector3:
	# Integrate an authored displacement window; movement still uses body collision.
	if not is_attacking() or delta <= 0.0:
		return Vector3.ZERO
	var start := motion_elapsed
	motion_elapsed += delta * swing_speed
	var overlap := maxf(0.0, minf(motion_elapsed, attack.lunge_start + attack.lunge_duration)
		- maxf(start, attack.lunge_start))
	return attack_direction * attack.lunge_distance * overlap / maxf(attack.lunge_duration * delta, 0.00001)

func phase_name() -> String:
	return Phase.keys()[phase]

func _set_phase(value: Phase) -> void:
	phase = value
	phase_elapsed = 0.0
	phase_changed.emit(phase_name())

func _physics_process(delta: float) -> void:
	if not actor.health.is_alive():
		if is_attacking():
			cancel()
		return
	if phase == Phase.IDLE:
		idle_elapsed += delta
		return
	phase_elapsed += delta * swing_speed
	match phase:
		Phase.WINDUP:
			if phase_elapsed >= attack.windup:
				_set_phase(Phase.ACTIVE)
				_resolve_hits()
		Phase.ACTIVE:
			_resolve_hits()
			if phase_elapsed >= attack.active:
				_set_phase(Phase.RECOVERY)
		Phase.RECOVERY:
			if phase_elapsed >= attack.recovery:
				_set_phase(Phase.IDLE)
				if queued:
					request_attack()

func _resolve_hits() -> void:
	var forward := -actor.global_basis.z
	forward.y = 0.0
	forward = forward.normalized()
	var threshold := cos(deg_to_rad(attack.cone_degrees * 0.5))
	for target in get_tree().get_nodes_in_group(target_group):
		var id := target.get_instance_id()
		if hit_ids.has(id) or not target.health.is_alive():
			continue
		var offset: Vector3 = target.global_position - actor.global_position
		if absf(offset.y) > attack.height_tolerance:
			continue
		offset.y = 0.0
		if offset.length() > attack.reach:
			continue
		if offset.length_squared() > 0.001 and forward.dot(offset.normalized()) < threshold:
			continue
		# Static world geometry blocks melee. Actor bodies do not block cleaves.
		var ray := PhysicsRayQueryParameters3D.create(
			actor.global_position + Vector3.UP, target.global_position + Vector3.UP, 1)
		if not actor.get_world_3d().direct_space_state.intersect_ray(ray).is_empty():
			continue
		hit_ids[id] = true
		var damage: float = target.statuses.modify_incoming_basic_damage(swing_damage, actor) if target.statuses else swing_damage
		if target.health.apply_damage(damage, actor):
			swing_hits += 1
			total_hits += 1
			hit_landed.emit(target)
			if actor.mounts and actor.mounts.mounted:
				actor.mounts.record_hit(target, swing_serial, attack.reach)
