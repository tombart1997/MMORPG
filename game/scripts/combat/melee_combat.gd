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

func _ready() -> void:
	actor = get_parent() as CharacterBody3D

func is_attacking() -> bool:
	return phase != Phase.IDLE

func request_attack() -> bool:
	if is_attacking() or not actor.health.is_alive() or attack == null:
		return false
	hit_ids.clear()
	swing_hits = 0
	_set_phase(Phase.WINDUP)
	return true

func cancel() -> void:
	_set_phase(Phase.IDLE)

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
		return
	phase_elapsed += delta
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
		if target.health.apply_damage(attack.damage, actor):
			swing_hits += 1
			total_hits += 1
			hit_landed.emit(target)
