class_name CombatStatuses
extends Node
signal hostile_applied(source: ActorBody)
var actor: ActorBody
var entries: Dictionary = {}
var push_velocity := Vector3.ZERO
var push_remaining: float = 0
func _ready() -> void:
	actor = get_parent() as ActorBody
func has(id: StringName) -> bool:
	return entries.has(id)
func add(id: StringName, duration: float, magnitude: float = 1.0, source: ActorBody = null) -> void:
	if not actor.health.is_alive(): return
	if source and source.faction != actor.faction:
		if SafeArea.protects(actor) or SafeArea.protects(source): return
		hostile_applied.emit(source)
	var old: Dictionary = entries.get(id, {})
	entries[id] = {"remaining": maxf(duration, float(old.get("remaining", 0))), "magnitude": maxf(magnitude, float(old.get("magnitude", 0))), "source": source, "direction": -actor.global_basis.z}
func remove(id: StringName) -> void:
	entries.erase(id)
func clear() -> void:
	entries.clear()
	push_remaining = 0
	push_velocity = Vector3.ZERO
func movement_multiplier() -> float:
	var reduction := 0.0
	for id in [&"slow", &"zone_slow"]:
		if has(id): reduction = maxf(reduction, entries[id].magnitude)
	return (1.0 - clampf(reduction, 0, 0.8)) * (float(entries[&"haste"].magnitude) if has(&"haste") else 1.0)
func modify_incoming_basic_damage(amount: float, _source: ActorBody) -> float:
	# Basic combat asks the receiver for its modifier instead of knowing which
	# specialization authored the status. Future policies belong in the status
	# layer rather than in MeleeCombat.
	return amount * (1.25 if has(&"open") else 1.0)
func filter_damage(amount: float, source: Node3D) -> float:
	var reduction := float(entries.get(&"shelter", {}).get("magnitude", 0))
	if has(&"guard") and is_instance_valid(source) and source is ActorBody and source.faction != actor.faction:
		var direction := source.global_position - actor.global_position
		direction.y = 0
		if direction.length_squared() < 0.001 or entries[&"guard"].direction.dot(direction.normalized()) >= 0.5:
			reduction = maxf(reduction, entries[&"guard"].magnitude)
			remove(&"guard")
			add(&"answer", 5.0)
			SkillVFX.flash(actor.get_parent(), actor.global_position, 0.85, Color.GOLD)
	return amount * (1.0 - clampf(reduction, 0, 0.8))
func push(direction: Vector3, distance: float, duration: float) -> void:
	push_velocity = direction.normalized() * distance / duration
	push_remaining = duration
func consume_push(delta: float) -> Vector3:
	if push_remaining <= 0: return Vector3.ZERO
	var portion := minf(delta, push_remaining)
	push_remaining -= portion
	return push_velocity * portion / maxf(delta, 0.0001)
func _physics_process(delta: float) -> void:
	if not actor.health.is_alive(): clear(); return
	for id in entries.keys():
		entries[id].remaining -= delta
		if entries[id].remaining <= 0: entries.erase(id)
