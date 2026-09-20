class_name CharacterStats
extends Node
signal changed
var actor: ActorBody
var base: Dictionary = {"max_hp": 160.0, "attack": 15.0, "defense": 0.0, "movement_speed": 5.5, "attack_speed": 1.0}
var progression_bonus: Dictionary = {}
var equipment_bonus: Dictionary = {}
var calculated: Dictionary = {}

func value(key: StringName) -> float:
	return float(calculated.get(String(key), 0.0))

func recalculate() -> void:
	progression_bonus = {"max_hp": (actor.progression.level - 1) * 20.0, "attack": (actor.progression.level - 1) * 2.0}
	equipment_bonus.clear()
	for stack in actor.equipment.slots.values():
		if stack:
			for key in stack.modifiers():
				equipment_bonus[key] = float(equipment_bonus.get(key, 0)) + float(stack.modifiers()[key])
	calculated = base.duplicate()
	for layer in [progression_bonus, equipment_bonus]:
		for key in layer: calculated[key] = float(calculated.get(key, 0)) + float(layer[key])
	calculated["max_hp"] = maxf(1, value(&"max_hp"))
	calculated["attack_speed"] = clampf(value(&"attack_speed"), 0.2, 4.0)
	calculated["movement_speed"] = maxf(0, value(&"movement_speed"))
	actor.health.maximum = value(&"max_hp")
	# Preserve absolute HP on equipment changes; clamp on removal, never resurrect.
	actor.health.current = minf(actor.health.current, actor.health.maximum)
	actor.health.defense = maxf(0, value(&"defense"))
	actor.health.changed.emit(actor.health.current, actor.health.maximum)
	changed.emit()
