class_name PlayerProgression
extends Node
signal level_gained(level: int)
signal changed
var level: int = 1
var xp: int = 0
var kills: int = 0

func xp_required() -> int:
	return requirement_for(level)

static func requirement_for(at_level: int) -> int:
	# Deliberate long-form progression: 30 level-one kills, rising by level band.
	return 600 + 180 * (at_level - 1) + 35 * (at_level - 1) * (at_level - 1)

func award_xp(amount: int) -> void:
	xp += maxi(0, amount)
	while xp >= xp_required():
		xp -= xp_required()
		level += 1
		level_gained.emit(level)
	changed.emit()
