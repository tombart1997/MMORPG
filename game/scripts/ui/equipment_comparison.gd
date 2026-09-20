class_name EquipmentComparison
extends RefCounted
static func describe(item: ItemData, player: ActorBody, instance: ItemStack = null) -> String:
	if item.equipment_slot == &"": return ""
	var current: ItemStack = player.equipment.slots.get(item.equipment_slot)
	var modifiers: Dictionary = current.modifiers() if current else {}
	var candidate := instance.modifiers() if instance else item.modifiers
	var keys: Array = candidate.keys()
	for key in modifiers:
		if not keys.has(key): keys.append(key)
	keys.sort()
	var changes := PackedStringArray()
	for key in keys:
		var delta := float(candidate.get(key, 0)) - float(modifiers.get(key, 0))
		changes.append("%s %+.1f" % [String(key).replace("_", " ").capitalize(), delta])
	return "Compared with %s: %s" % [current.display_name() if current else "empty slot", ", ".join(changes)]
