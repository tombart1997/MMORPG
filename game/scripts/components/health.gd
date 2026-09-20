class_name HealthComponent
extends Node
## Damage entry point. A future authority layer should validate requests here.
signal damaged(amount: float, source: Node3D)
signal changed(current: float, maximum: float)
signal died(source: Node3D)

@export var maximum: float = 100.0
var current: float
var defense: float = 0.0

func _ready() -> void:
	current = maximum

func is_alive() -> bool:
	return current > 0.0

func heal(amount: float) -> void:
	if is_alive() and amount > 0 and current < maximum:
		current = minf(maximum, current + amount)
		changed.emit(current, maximum)

func apply_damage(amount: float, source: Node3D) -> bool:
	# Sanctuary blocks hostile damage in both directions, including active swings.
	var actor := get_parent() as ActorBody
	if actor and source is ActorBody and actor.faction != source.faction:
		if SafeArea.protects(actor) or SafeArea.protects(source): return false
	if not is_alive() or amount <= 0.0:
		return false
	var mitigated := maxf(1.0, amount - defense)
	if actor and actor.statuses: mitigated = actor.statuses.filter_damage(mitigated, source)
	var applied := minf(mitigated, current)
	current -= applied
	damaged.emit(applied, source)
	changed.emit(current, maximum)
	if not is_alive():
		died.emit(source)
	return true
