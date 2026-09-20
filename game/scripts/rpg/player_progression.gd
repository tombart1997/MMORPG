class_name PlayerProgression
extends Node
signal level_gained(level: int)
signal changed
var level: int = 1
var xp: int = 0
var kills: int = 0

func xp_required() -> int:
	return 80 + (level - 1) * 40

func award_xp(amount: int) -> void:
	xp += maxi(0, amount)
	while xp >= xp_required():
		xp -= xp_required()
		level += 1
		level_gained.emit(level)
	changed.emit()
