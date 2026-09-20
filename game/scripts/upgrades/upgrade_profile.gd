class_name UpgradeProfile
extends Resource
## Ordered next-level rules. Length is the data-driven cap; bonuses are cumulative.
@export var steps: Array[Dictionary] = []
@export_enum("retain", "downgrade") var failure_policy: String = "retain"

func bonuses(level: int) -> Dictionary:
	var total: Dictionary = {}
	for i in mini(level, steps.size()):
		for stat in steps[i].get("bonuses", {}): total[stat] = float(total.get(stat, 0)) + float(steps[i].bonuses[stat])
	return total
