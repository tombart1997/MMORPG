class_name HealthComponent
extends Node
## Damage entry point. A future authority layer should validate requests here.
signal damaged(amount: float, source: Node3D)
signal changed(current: float, maximum: float)
signal died(source: Node3D)

@export var maximum: float = 100.0
var current: float

func _ready() -> void:
	current = maximum

func is_alive() -> bool:
	return current > 0.0

func heal(amount: float) -> void:
	if is_alive() and amount > 0:
		current = minf(maximum, current + amount)
		changed.emit(current, maximum)

func apply_damage(amount: float, source: Node3D) -> bool:
	if not is_alive() or amount <= 0.0:
		return false
	var applied := minf(amount, current)
	current -= applied
	damaged.emit(applied, source)
	changed.emit(current, maximum)
	if not is_alive():
		died.emit(source)
	return true
