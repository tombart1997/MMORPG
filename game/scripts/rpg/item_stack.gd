class_name ItemStack
extends RefCounted
## Separate runtime state; reserved properties support future unique equipment.
var id: StringName
var quantity: int
var properties: Dictionary = {}

func _init(item_id: StringName = &"", amount: int = 1) -> void:
	id = item_id
	quantity = amount

func definition() -> ItemData:
	return ItemCatalog.get_item(id)

func upgrade_level() -> int:
	return int(properties.get("upgrade", 0))

func modifiers() -> Dictionary:
	var result := definition().modifiers.duplicate()
	if definition().upgrade_profile:
		var bonus := definition().upgrade_profile.bonuses(upgrade_level())
		for key in bonus: result[key] = float(result.get(key, 0)) + float(bonus[key])
	return result

func display_name() -> String:
	return definition().display_name + (" +%d" % upgrade_level() if upgrade_level() > 0 else "")

func tooltip() -> String:
	var result := display_name() + "\n" + definition().description
	for key in modifiers(): result += "\n%+.1f %s" % [float(modifiers()[key]), String(key).replace("_", " ").capitalize()]
	if definition().healing > 0: result += "\nRestores %.0f HP" % definition().healing
	return result + "\nLevel %d | Sell %d gold" % [definition().required_level, definition().value]
